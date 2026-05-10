from benchmark.algorithms import AlgorithmSpec
from benchmark.worker import run_with_timeout


def test_run_with_timeout_reports_crash(tmp_path):
    algorithm = tmp_path / "bad.py"
    algorithm.write_text("def reconstruct(reads, reference_length, metadata):\n    raise RuntimeError('boom')\n")

    result = run_with_timeout(AlgorithmSpec("bad", algorithm), ["AT"], 2, {}, 2)

    assert result["status"] == "crash"
    assert "boom" in result["error"]
