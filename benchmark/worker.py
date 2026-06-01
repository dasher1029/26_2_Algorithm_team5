"""Run compiled C++ algorithm submissions."""

from __future__ import annotations

import subprocess
import time
from typing import Any, Dict

from benchmark.algorithms import AlgorithmSpec


def _build_stdin(reference: str, reads: list[str], reference_length: int, metadata: dict) -> str:
    lines = [str(reference_length), reference, str(len(reads))]
    lines.extend(reads)
    lines.append(str(len(metadata)))
    for key in sorted(metadata):
        lines.append(f"{key}={metadata[key]}")
    return "\n".join(lines) + "\n"


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

    started = time.perf_counter()
    try:
        completed = subprocess.run(
            [str(algorithm.executable_path)],
            input=_build_stdin(reference, reads, reference_length, metadata),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "reconstruction": "",
            "runtime_seconds": timeout_seconds,
            "peak_memory_mb": "",
            "error": f"Timed out after {timeout_seconds} seconds",
        }
    except OSError as exc:
        return {
            "status": "crash",
            "reconstruction": "",
            "runtime_seconds": time.perf_counter() - started,
            "peak_memory_mb": "",
            "error": str(exc),
        }

    runtime = time.perf_counter() - started
    if completed.returncode != 0:
        return {
            "status": "crash",
            "reconstruction": "",
            "runtime_seconds": runtime,
            "peak_memory_mb": "",
            "error": (completed.stderr or completed.stdout).strip(),
        }

    reconstruction = "".join(completed.stdout.split())
    if not reconstruction:
        return {
            "status": "crash",
            "reconstruction": "",
            "runtime_seconds": runtime,
            "peak_memory_mb": "",
            "error": "Algorithm produced no reconstruction on stdout",
        }

    return {
        "status": "ok",
        "reconstruction": reconstruction,
        "runtime_seconds": runtime,
        "peak_memory_mb": "",
        "error": "",
    }
