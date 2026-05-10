"""Algorithm discovery and loading."""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Callable, Dict, List


AlgorithmFn = Callable[[List[str], int, Dict], str]


@dataclass(frozen=True)
class AlgorithmSpec:
    name: str
    path: Path


def discover_algorithms(directory: Path) -> List[AlgorithmSpec]:
    if not directory.exists():
        return []

    specs = []
    for path in sorted(directory.glob("*.py")):
        if path.name == "template.py" or path.name.startswith("_"):
            continue
        specs.append(AlgorithmSpec(name=path.stem, path=path))
    return specs


def load_module(path: Path) -> ModuleType:
    algorithm_dir = str(path.parent.resolve())
    if algorithm_dir not in sys.path:
        sys.path.insert(0, algorithm_dir)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import algorithm file: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_reconstruct(path: Path) -> AlgorithmFn:
    module = load_module(path)
    reconstruct = getattr(module, "reconstruct", None)
    if not callable(reconstruct):
        raise AttributeError(f"{path} must define reconstruct(reads, reference_length, metadata)")
    return reconstruct
