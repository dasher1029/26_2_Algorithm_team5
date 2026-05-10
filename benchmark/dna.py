"""DNA reference generation and read simulation."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ExperimentCase:
    reference_length: int
    read_length: int
    coverage: float
    noise_rate: float
    seed: int
    alphabet: str = "ATCG"

    @property
    def read_count(self) -> int:
        return int(math.ceil(self.coverage * self.reference_length / self.read_length))


def generate_reference(length: int, seed: int, alphabet: str = "ATCG") -> str:
    rng = random.Random(seed)
    return "".join(rng.choice(alphabet) for _ in range(length))


def mutate_base(base: str, rng: random.Random, alphabet: str = "ATCG") -> str:
    choices = [candidate for candidate in alphabet if candidate != base]
    return rng.choice(choices)


def simulate_reads(reference: str, case: ExperimentCase) -> List[str]:
    if case.read_length <= 0:
        raise ValueError("read_length must be positive")
    if case.read_length > len(reference):
        raise ValueError("read_length must be smaller than or equal to reference length")
    if not 0 <= case.noise_rate <= 1:
        raise ValueError("noise_rate must be between 0 and 1")

    rng = random.Random(case.seed + 1_000_003)
    reads = []
    max_start = len(reference) - case.read_length
    for _ in range(case.read_count):
        start = rng.randint(0, max_start)
        read = list(reference[start : start + case.read_length])
        for index, base in enumerate(read):
            if rng.random() < case.noise_rate:
                read[index] = mutate_base(base, rng, case.alphabet)
        reads.append("".join(read))
    return reads
