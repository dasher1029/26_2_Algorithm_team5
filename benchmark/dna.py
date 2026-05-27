"""DNA reference generation and read simulation."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class ExperimentCase:
    reference_length: int
    read_length: int
    coverage: float
    noise_rate: float
    seed: int
    alphabet: str = "ATCG"
    reference_path: str = ""
    reference_start: int = 0
    genome_mutation_rate: float = 0.0

    @property
    def read_count(self) -> int:
        return int(math.ceil(self.coverage * self.reference_length / self.read_length))


def load_reference_text(path: Path, alphabet: str = "ATCG") -> str:
    allowed = set(alphabet.upper())
    text = path.read_text(encoding="utf-8")
    reference = "".join(base for base in text.upper() if base in allowed)
    if not reference:
        raise ValueError(f"No DNA bases found in reference file: {path}")
    return reference


def mutate_base(base: str, rng: random.Random, alphabet: str = "ATCG") -> str:
    choices = [candidate for candidate in alphabet if candidate != base]
    return rng.choice(choices)


def slice_reference(reference: str, start: int, length: int) -> str:
    if start < 0:
        raise ValueError("reference_start must be non-negative")
    if length <= 0:
        raise ValueError("genome_length must be positive")
    end = start + length
    if end > len(reference):
        raise ValueError(
            f"reference slice {start}:{end} exceeds reference length {len(reference)}"
        )
    return reference[start:end]


def create_my_genome(
    reference_slice: str,
    mutation_rate: float,
    seed: int,
    alphabet: str = "ATCG",
) -> str:
    if not 0 <= mutation_rate <= 1:
        raise ValueError("genome_mutation_rate must be between 0 and 1")

    rng = random.Random(seed + 2_000_003)
    genome = []
    for base in reference_slice:
        if rng.random() < mutation_rate:
            genome.append(mutate_base(base, rng, alphabet))
        else:
            genome.append(base)
    return "".join(genome)


def build_experiment_inputs(case: ExperimentCase) -> tuple[str, str, List[str]]:
    reference = load_reference_text(Path(case.reference_path), case.alphabet)
    reference_slice = slice_reference(reference, case.reference_start, case.reference_length)
    gold_standard = create_my_genome(
        reference_slice,
        case.genome_mutation_rate,
        case.seed,
        case.alphabet,
    )
    reads = simulate_reads(gold_standard, case)
    return reference_slice, gold_standard, reads


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
