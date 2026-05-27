"""C++ algorithm discovery and compilation."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class AlgorithmSpec:
    name: str
    path: Path
    executable_path: Path | None = None
    compile_error: str = ""


def discover_algorithms(directory: Path) -> List[AlgorithmSpec]:
    if not directory.exists():
        return []

    specs = []
    for path in sorted(directory.glob("*.cpp")):
        if path.name == "template.cpp" or path.name.startswith("_"):
            continue
        specs.append(AlgorithmSpec(name=path.stem, path=path))
    return specs


def compile_algorithm(
    algorithm: AlgorithmSpec,
    build_dir: Path,
    timeout_seconds: float = 20,
) -> AlgorithmSpec:
    build_dir.mkdir(parents=True, exist_ok=True)
    suffix = ".exe" if os.name == "nt" else ""
    executable_path = build_dir / f"{algorithm.name}{suffix}"
    command = [
        "g++",
        "-std=c++17",
        "-O2",
        str(algorithm.path),
        "-o",
        str(executable_path),
    ]

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return AlgorithmSpec(
            algorithm.name,
            algorithm.path,
            compile_error=f"Compilation timed out after {timeout_seconds} seconds",
        )
    except OSError as exc:
        return AlgorithmSpec(algorithm.name, algorithm.path, compile_error=str(exc))

    if completed.returncode != 0:
        error = (completed.stderr or completed.stdout).strip()
        return AlgorithmSpec(algorithm.name, algorithm.path, compile_error=error)

    return AlgorithmSpec(algorithm.name, algorithm.path, executable_path=executable_path)


def compile_algorithms(
    algorithms: List[AlgorithmSpec],
    build_dir: Path,
    timeout_seconds: float = 20,
) -> List[AlgorithmSpec]:
    return [compile_algorithm(algorithm, build_dir, timeout_seconds) for algorithm in algorithms]
