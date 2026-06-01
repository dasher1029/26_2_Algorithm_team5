"""Benchmark metrics."""

from __future__ import annotations


def positional_distance(left: str, right: str) -> int:
    shared_length = min(len(left), len(right))
    mismatches = sum(1 for index in range(shared_length) if left[index] != right[index])
    return mismatches + abs(len(left) - len(right))


def normalized_accuracy(reference: str, reconstruction: str) -> tuple[float, int]:
    distance = positional_distance(reference, reconstruction)
    denominator = max(len(reference), len(reconstruction), 1)
    return max(0.0, 1.0 - distance / denominator), distance
