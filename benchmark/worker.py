"""Run compiled C++ algorithm submissions."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict

from benchmark.algorithms import AlgorithmSpec


def _build_stdin(reference: str, reads: list[str], reference_length: int, metadata: dict) -> str:
    lines = [str(reference_length), reference, str(len(reads))]
    lines.extend(reads)
    lines.append(str(len(metadata)))
    for key in sorted(metadata):
        lines.append(f"{key}={metadata[key]}")
    return "\n".join(lines) + "\n"


def _read_measurements(mem_path: str) -> tuple[float | str, float | None]:
    """Parse the wrapper's output: peak memory in MB and child wall time."""
    try:
        content = Path(mem_path).read_text(encoding="utf-8")
    except OSError:
        return "", None
    lines = content.splitlines()
    peak: float | str = ""
    child_runtime: float | None = None
    if lines and lines[0]:
        try:
            peak = float(lines[0])
        except ValueError:
            peak = ""
    if len(lines) > 1 and lines[1]:
        try:
            child_runtime = float(lines[1])
        except ValueError:
            child_runtime = None
    return peak, child_runtime


def run_with_timeout(
    algorithm: AlgorithmSpec,
    reference: str,
    reads: list[str],
    reference_length: int,
    metadata: dict,
    timeout_seconds: float,
) -> Dict[str, Any]:
    if algorithm.compile_error:
        return {
            "status": "crash",
            "reconstruction": "",
            "runtime_seconds": "",
            "peak_memory_mb": "",
            "error": f"Compilation failed:\n{algorithm.compile_error}",
        }
    if algorithm.executable_path is None:
        return {
            "status": "crash",
            "reconstruction": "",
            "runtime_seconds": "",
            "peak_memory_mb": "",
            "error": "Algorithm was not compiled before execution",
        }

    stdin_text = _build_stdin(reference, reads, reference_length, metadata)
    mem_fd, mem_path = tempfile.mkstemp(prefix="benchmark_mem_")
    os.close(mem_fd)
    command = [sys.executable, "-m", "benchmark._memwrap", mem_path, str(algorithm.executable_path)]

    # start_new_session puts the wrapper (and the algorithm binary it spawns) in
    # their own process group so a timeout can kill the whole tree, not just the
    # Python wrapper, leaving no orphaned algorithm process behind.
    started = time.perf_counter()
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
    except OSError as exc:
        os.unlink(mem_path)
        return {
            "status": "crash",
            "reconstruction": "",
            "runtime_seconds": time.perf_counter() - started,
            "peak_memory_mb": "",
            "error": str(exc),
        }

    try:
        stdout, stderr = process.communicate(input=stdin_text, timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            process.kill()
        process.communicate()
        os.unlink(mem_path)
        return {
            "status": "timeout",
            "reconstruction": "",
            "runtime_seconds": timeout_seconds,
            "peak_memory_mb": "",
            "error": f"Timed out after {timeout_seconds} seconds",
        }

    wall_runtime = time.perf_counter() - started
    peak_memory_mb, child_runtime = _read_measurements(mem_path)
    os.unlink(mem_path)
    runtime = child_runtime if child_runtime is not None else wall_runtime

    if process.returncode != 0:
        return {
            "status": "crash",
            "reconstruction": "",
            "runtime_seconds": runtime,
            "peak_memory_mb": peak_memory_mb,
            "error": (stderr or stdout).strip(),
        }

    reconstruction = "".join(stdout.split())
    if not reconstruction:
        return {
            "status": "crash",
            "reconstruction": "",
            "runtime_seconds": runtime,
            "peak_memory_mb": peak_memory_mb,
            "error": "Algorithm produced no reconstruction on stdout",
        }

    return {
        "status": "ok",
        "reconstruction": reconstruction,
        "runtime_seconds": runtime,
        "peak_memory_mb": peak_memory_mb,
        "error": "",
    }
