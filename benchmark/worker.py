"""Run algorithm submissions in isolated child processes."""

from __future__ import annotations

import multiprocessing as mp
import queue
import time
import traceback
import tracemalloc
from pathlib import Path
from typing import Any, Dict

from benchmark.algorithms import AlgorithmSpec, load_reconstruct


def _run_algorithm(
    algorithm_path: str,
    reads: list[str],
    reference_length: int,
    metadata: dict,
    output: mp.Queue,
) -> None:
    tracemalloc.start()
    started = time.perf_counter()
    try:
        reconstruct = load_reconstruct(Path(algorithm_path))
        reconstruction = reconstruct(reads, reference_length, metadata)
        if not isinstance(reconstruction, str):
            raise TypeError("reconstruct(...) must return a string")
        runtime = time.perf_counter() - started
        _, peak = tracemalloc.get_traced_memory()
        output.put(
            {
                "status": "ok",
                "reconstruction": reconstruction,
                "runtime_seconds": runtime,
                "peak_memory_mb": peak / (1024 * 1024),
                "error": "",
            }
        )
    except Exception:
        runtime = time.perf_counter() - started
        _, peak = tracemalloc.get_traced_memory()
        output.put(
            {
                "status": "crash",
                "reconstruction": "",
                "runtime_seconds": runtime,
                "peak_memory_mb": peak / (1024 * 1024),
                "error": traceback.format_exc(limit=3),
            }
        )
    finally:
        tracemalloc.stop()


def run_with_timeout(
    algorithm: AlgorithmSpec,
    reads: list[str],
    reference_length: int,
    metadata: dict,
    timeout_seconds: float,
) -> Dict[str, Any]:
    output: mp.Queue = mp.Queue()
    process = mp.Process(
        target=_run_algorithm,
        args=(str(algorithm.path), reads, reference_length, metadata, output),
    )
    process.start()
    process.join(timeout_seconds)

    if process.is_alive():
        process.terminate()
        process.join(2)
        return {
            "status": "timeout",
            "reconstruction": "",
            "runtime_seconds": timeout_seconds,
            "peak_memory_mb": "",
            "error": f"Timed out after {timeout_seconds} seconds",
        }

    try:
        return output.get_nowait()
    except queue.Empty:
        return {
            "status": "crash",
            "reconstruction": "",
            "runtime_seconds": "",
            "peak_memory_mb": "",
            "error": "Algorithm process exited without returning a result",
        }
