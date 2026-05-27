"""Run DNA reconstruction benchmarks."""

from __future__ import annotations

import argparse
import csv
import itertools
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml

from benchmark.algorithms import AlgorithmSpec, compile_algorithms, discover_algorithms
from benchmark.dna import ExperimentCase, build_experiment_inputs
from benchmark.metrics import normalized_accuracy
from benchmark.report import build_report
from benchmark.worker import run_with_timeout


TRIVIAL_BASELINE_NAME = "trivial_concat"

RESULT_FIELDS = [
    "algorithm",
    "status",
    "runtime_seconds",
    "accuracy",
    "edit_distance",
    "reference_path",
    "reference_start",
    "reference_length",
    "genome_mutation_rate",
    "gold_standard_length",
    "read_length",
    "coverage",
    "read_count",
    "noise_rate",
    "seed",
    "reconstructed_length",
    "length_ratio",
    "peak_memory_mb",
    "error",
]


def _quick_config() -> Dict[str, Any]:
    return {
        "experiment": {
            "alphabet": "ATCG",
            "reference_path": "data/example_reference.txt",
            "reference_starts": [0],
            "genome_lengths": [80],
            "genome_mutation_rates": [0.0],
            "read_lengths": [20],
            "coverages": [3],
            "noise_rates": [0.0],
            "seeds": [1],
            "timeout_seconds": 5,
        }
    }


def load_config(path: Path | None, quick: bool) -> Dict[str, Any]:
    if quick:
        return _quick_config()
    if path is None:
        path = Path("configs/default.yaml")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def iter_cases(config: Dict[str, Any]) -> Iterable[ExperimentCase]:
    experiment = config["experiment"]
    alphabet = experiment.get("alphabet", "ATCG")
    for reference_start, genome_length, genome_mutation_rate, read_length, coverage, noise_rate, seed in itertools.product(
        experiment["reference_starts"],
        experiment["genome_lengths"],
        experiment["genome_mutation_rates"],
        experiment["read_lengths"],
        experiment["coverages"],
        experiment["noise_rates"],
        experiment["seeds"],
    ):
        yield ExperimentCase(
            reference_length=int(genome_length),
            read_length=int(read_length),
            coverage=float(coverage),
            noise_rate=float(noise_rate),
            seed=int(seed),
            alphabet=alphabet,
            reference_path=str(experiment["reference_path"]),
            reference_start=int(reference_start),
            genome_mutation_rate=float(genome_mutation_rate),
        )


def _trivial_concat(reads: list[str], reference_length: int, metadata: dict) -> str:
    joined = "".join(reads)
    if len(joined) >= reference_length:
        return joined[:reference_length]
    return joined.ljust(reference_length, metadata.get("alphabet", "A")[0])


def _metadata(case: ExperimentCase) -> dict:
    return {
        "alphabet": case.alphabet,
        "seed": case.seed,
        "read_length": case.read_length,
        "read_count": case.read_count,
        "coverage": case.coverage,
        "noise_rate": case.noise_rate,
        "reference_length": case.reference_length,
        "reference_path": case.reference_path,
        "reference_start": case.reference_start,
        "genome_length": case.reference_length,
        "genome_mutation_rate": case.genome_mutation_rate,
        "allowed_mismatches": 2,
    }


def _result_row(
    algorithm_name: str,
    case: ExperimentCase,
    status: str,
    runtime_seconds: float | str,
    reconstruction: str,
    gold_standard: str,
    peak_memory_mb: float | str = "",
    error: str = "",
) -> dict:
    accuracy, distance = normalized_accuracy(gold_standard, reconstruction) if status == "ok" else (0.0, "")
    return {
        "algorithm": algorithm_name,
        "status": status,
        "runtime_seconds": runtime_seconds,
        "accuracy": accuracy,
        "edit_distance": distance,
        "reference_path": case.reference_path,
        "reference_start": case.reference_start,
        "reference_length": case.reference_length,
        "genome_mutation_rate": case.genome_mutation_rate,
        "gold_standard_length": len(gold_standard),
        "read_length": case.read_length,
        "coverage": case.coverage,
        "read_count": case.read_count,
        "noise_rate": case.noise_rate,
        "seed": case.seed,
        "reconstructed_length": len(reconstruction),
        "length_ratio": len(reconstruction) / max(case.reference_length, 1),
        "peak_memory_mb": peak_memory_mb,
        "error": error,
    }


def run_builtin_baseline(case: ExperimentCase, gold_standard: str, reads: list[str]) -> dict:
    reconstruction = _trivial_concat(reads, case.reference_length, {"alphabet": case.alphabet})
    return _result_row(TRIVIAL_BASELINE_NAME, case, "ok", 0.0, reconstruction, gold_standard)


def run_case(
    algorithm: AlgorithmSpec,
    case: ExperimentCase,
    reference: str,
    gold_standard: str,
    reads: list[str],
    timeout_seconds: float,
) -> dict:
    metadata = _metadata(case)
    result = run_with_timeout(algorithm, reference, reads, case.reference_length, metadata, timeout_seconds)
    reconstruction = result.get("reconstruction", "")
    return _result_row(
        algorithm.name,
        case,
        result["status"],
        result["runtime_seconds"],
        reconstruction,
        gold_standard,
        result.get("peak_memory_mb", ""),
        result.get("error", ""),
    )


def run_benchmark(
    config: Dict[str, Any],
    algorithms_dir: Path,
    output_dir: Path,
    quick: bool = False,
    build_dir: Path | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    experiment = config["experiment"]
    timeout_seconds = float(experiment.get("timeout_seconds", 10))
    compile_timeout_seconds = float(experiment.get("compile_timeout_seconds", 20))
    if build_dir is None:
        build_dir = output_dir / "build"
    algorithms = compile_algorithms(
        discover_algorithms(algorithms_dir),
        build_dir,
        compile_timeout_seconds,
    )
    cases = list(iter_cases(config))
    total_runs = len(cases) * (len(algorithms) + 1)
    if algorithms:
        print(f"Discovered {len(algorithms)} algorithm(s): {', '.join(a.name for a in algorithms)}")
        failed_compiles = [algorithm for algorithm in algorithms if algorithm.compile_error]
        for algorithm in failed_compiles:
            print(f"Compilation failed for {algorithm.name}; recording crash rows.")
    else:
        print(f"No algorithm files found in {algorithms_dir}. Running built-in baseline only.")
    print(f"Planned benchmark runs: {total_runs}")

    rows: List[dict] = []
    completed_runs = 0
    for case in cases:
        reference, gold_standard, reads = build_experiment_inputs(case)
        baseline_row = run_builtin_baseline(case, gold_standard, reads)
        rows.append(baseline_row)
        completed_runs += 1
        print(
            f"[{completed_runs}/{total_runs}] {TRIVIAL_BASELINE_NAME} "
            f"genome={case.reference_length} read={case.read_length} "
            f"cov={case.coverage:g} noise={case.noise_rate:g} "
            f"mut={case.genome_mutation_rate:g} seed={case.seed} -> ok "
            f"acc={float(baseline_row['accuracy']):.4f}"
        )
        for algorithm in algorithms:
            row = run_case(algorithm, case, reference, gold_standard, reads, timeout_seconds)
            rows.append(row)
            completed_runs += 1
            print(
                f"[{completed_runs}/{total_runs}] {algorithm.name} "
                f"genome={case.reference_length} read={case.read_length} "
                f"cov={case.coverage:g} noise={case.noise_rate:g} "
                f"mut={case.genome_mutation_rate:g} seed={case.seed} "
                f"-> {row['status']} "
                f"acc={float(row['accuracy']):.4f} time={float(row['runtime_seconds'] or 0):.3f}s"
            )

    results_csv = output_dir / "results.csv"
    with results_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    build_report(results_csv, output_dir)
    return results_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Run DNA reconstruction benchmarks.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=Path("results/latest"))
    parser.add_argument("--algorithms", type=Path, default=Path("algorithms"))
    parser.add_argument("--build-dir", type=Path, default=None)
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config, args.quick)
    results_csv = run_benchmark(config, args.algorithms, args.out, quick=args.quick, build_dir=args.build_dir)
    print(f"Wrote {results_csv}")
    print(f"Wrote {args.out / 'report.html'}")


if __name__ == "__main__":
    main()
