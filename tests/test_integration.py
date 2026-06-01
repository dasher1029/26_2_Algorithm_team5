import csv
import shutil

import pytest

from benchmark.run import run_benchmark


def test_quick_benchmark_outputs_csv_figures_and_html(tmp_path):
    output = tmp_path / "results"
    reference = tmp_path / "reference.txt"
    reference.write_text("ATCG" * 30, encoding="utf-8")
    config = {
        "experiment": {
            "alphabet": "ATCG",
            "reference_path": str(reference),
            "reference_starts": [0],
            "genome_lengths": [40],
            "genome_mutation_rates": [0.0],
            "read_lengths": [10],
            "coverages": [2],
            "noise_rates": [0.0],
            "seeds": [1],
            "timeout_seconds": 2,
        }
    }

    results_csv = run_benchmark(config, tmp_path / "algorithms", output, quick=True)

    assert results_csv.exists()
    assert (output / "report.html").exists()
    assert list((output / "figures").glob("*.png"))

    with results_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert [row["algorithm"] for row in rows] == ["trivial_concat"]
    assert rows[0]["reference_path"] == str(reference)
    assert rows[0]["reference_start"] == "0"
    assert rows[0]["genome_mutation_rate"] == "0.0"
    assert rows[0]["gold_standard_length"] == "40"


@pytest.mark.skipif(shutil.which("g++") is None, reason="g++ is required for C++ algorithm tests")
def test_benchmark_compiles_and_runs_cpp_algorithm(tmp_path):
    output = tmp_path / "results"
    algorithms = tmp_path / "algorithms"
    algorithms.mkdir()
    reference = tmp_path / "reference.txt"
    reference.write_text("ATCG" * 30, encoding="utf-8")
    (algorithms / "repeat_first_read.cpp").write_text(
        """
#include <iostream>
#include <string>
#include <vector>

int main() {
    int reference_length = 0;
    std::string reference;
    int read_count = 0;
    std::cin >> reference_length >> reference >> read_count;
    std::vector<std::string> reads(read_count);
    for (int i = 0; i < read_count; ++i) {
        std::cin >> reads[i];
    }

    std::string reconstruction;
    while ((int)reconstruction.size() < reference_length && !reads.empty()) {
        reconstruction += reads[0];
    }
    reconstruction.resize(reference_length, 'A');
    std::cout << reconstruction << "\\n";
    return 0;
}
""".strip(),
        encoding="utf-8",
    )
    config = {
        "experiment": {
            "alphabet": "ATCG",
            "reference_path": str(reference),
            "reference_starts": [0],
            "genome_lengths": [40],
            "genome_mutation_rates": [0.0],
            "read_lengths": [10],
            "coverages": [2],
            "noise_rates": [0.0],
            "seeds": [1],
            "timeout_seconds": 2,
        }
    }

    results_csv = run_benchmark(config, algorithms, output, build_dir=tmp_path / "build")

    with results_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert [row["algorithm"] for row in rows] == ["trivial_concat", "repeat_first_read"]
    assert rows[1]["status"] == "ok"
