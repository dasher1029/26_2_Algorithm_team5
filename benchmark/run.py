"""Run DNA reconstruction benchmarks."""

from __future__ import annotations

import argparse
import csv
import itertools
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml

from benchmark.algorithms import AlgorithmSpec, discover_algorithms
from benchmark.dna import ExperimentCase, generate_reference, simulate_reads
from benchmark.metrics import normalized_accuracy
from benchmark.report import build_report
from benchmark.worker import run_with_timeout


RESULT_FIELDS = [
    "algorithm",
    "status",
    "runtime_seconds",
    "accuracy",
    "edit_distance",
    "reference_length",
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
            "reference_lengths": [80],
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
    for reference_length, read_length, coverage, noise_rate, seed in itertools.product(
        experiment["reference_lengths"],
        experiment["read_lengths"],
        experiment["coverages"],
        experiment["noise_rates"],
        experiment["seeds"],
    ):
        yield ExperimentCase(
            reference_length=int(reference_length),
            read_length=int(read_length),
            coverage=float(coverage),
            noise_rate=float(noise_rate),
            seed=int(seed),
            alphabet=alphabet,
        )


def _sanity_reconstruct(reads: list[str], reference_length: int, metadata: dict) -> str:
    joined = "".join(reads)
    if len(joined) >= reference_length:
        return joined[:reference_length]
    return joined.ljust(reference_length, metadata.get("alphabet", "A")[0])


def _run_builtin_sanity(case: ExperimentCase, reference: str, reads: list[str]) -> dict:
    reconstruction = _sanity_reconstruct(reads, case.reference_length, {"alphabet": case.alphabet})
    accuracy, distance = normalized_accuracy(reference, reconstruction)
    return {
        "algorithm": "__quick_sanity__",
        "status": "ok",
        "runtime_seconds": 0.0,
        "accuracy": accuracy,
        "edit_distance": distance,
        "reference_length": case.reference_length,
        "read_length": case.read_length,
        "coverage": case.coverage,
        "read_count": case.read_count,
        "noise_rate": case.noise_rate,
        "seed": case.seed,
        "reconstructed_length": len(reconstruction),
        "length_ratio": len(reconstruction) / max(case.reference_length, 1),
        "peak_memory_mb": "",
        "error": "",
    }


def run_case(algorithm: AlgorithmSpec, case: ExperimentCase, timeout_seconds: float) -> dict:
    reference = generate_reference(case.reference_length, case.seed, case.alphabet)
    reads = simulate_reads(reference, case)
    metadata = {
        "alphabet": case.alphabet,
        "seed": case.seed,
        "read_length": case.read_length,
        "read_count": case.read_count,
        "coverage": case.coverage,
        "noise_rate": case.noise_rate,
        "reference_length": case.reference_length,
    }
    result = run_with_timeout(algorithm, reads, case.reference_length, metadata, timeout_seconds)
    reconstruction = result.get("reconstruction", "")
    accuracy, distance = normalized_accuracy(reference, reconstruction) if result["status"] == "ok" else (0.0, "")

    return {
        "algorithm": algorithm.name,
        "status": result["status"],
        "runtime_seconds": result["runtime_seconds"],
        "accuracy": accuracy,
        "edit_distance": distance,
        "reference_length": case.reference_length,
        "read_length": case.read_length,
        "coverage": case.coverage,
        "read_count": case.read_count,
        "noise_rate": case.noise_rate,
        "seed": case.seed,
        "reconstructed_length": len(reconstruction),
        "length_ratio": len(reconstruction) / max(case.reference_length, 1),
        "peak_memory_mb": result.get("peak_memory_mb", ""),
        "error": result.get("error", ""),
    }


def run_benchmark(
    config: Dict[str, Any],
    algorithms_dir: Path,
    output_dir: Path,
    quick: bool = False,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    experiment = config["experiment"]
    timeout_seconds = float(experiment.get("timeout_seconds", 10))
    algorithms = discover_algorithms(algorithms_dir)

    if not algorithms and not quick:
        raise SystemExit(
            f"No algorithms found in {algorithms_dir}. Add Python files with reconstruct(...) first."
        )

    cases = list(iter_cases(config))
    if quick and not algorithms:
        total_runs = len(cases)
        print("No algorithm files found. Running built-in quick sanity check.")
    else:
        total_runs = len(cases) * len(algorithms)
        print(f"Discovered {len(algorithms)} algorithm(s): {', '.join(a.name for a in algorithms)}")
    print(f"Planned benchmark runs: {total_runs}")

    rows: List[dict] = []
    completed_runs = 0
    for case in cases:
        reference = generate_reference(case.reference_length, case.seed, case.alphabet)
        reads = simulate_reads(reference, case)
        if quick and not algorithms:
            rows.append(_run_builtin_sanity(case, reference, reads))
            completed_runs += 1
            print(
                f"[{completed_runs}/{total_runs}] __quick_sanity__ "
                f"ref={case.reference_length} read={case.read_length} "
                f"cov={case.coverage:g} noise={case.noise_rate:g} seed={case.seed} -> ok"
            )
            continue
        for algorithm in algorithms:
            row = run_case(algorithm, case, timeout_seconds)
            rows.append(row)
            completed_runs += 1
            print(
                f"[{completed_runs}/{total_runs}] {algorithm.name} "
                f"ref={case.reference_length} read={case.read_length} "
                f"cov={case.coverage:g} noise={case.noise_rate:g} seed={case.seed} "
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
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config, args.quick)
    results_csv = run_benchmark(config, args.algorithms, args.out, quick=args.quick)
    print(f"Wrote {results_csv}")
    print(f"Wrote {args.out / 'report.html'}")


if __name__ == "__main__":
    main()
