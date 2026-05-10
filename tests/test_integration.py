from benchmark.run import run_benchmark


def test_quick_benchmark_outputs_csv_figures_and_html(tmp_path):
    output = tmp_path / "results"
    config = {
        "experiment": {
            "alphabet": "ATCG",
            "reference_lengths": [40],
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
