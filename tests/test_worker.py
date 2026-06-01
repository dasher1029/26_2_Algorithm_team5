import shutil

import pytest

from benchmark.algorithms import AlgorithmSpec, compile_algorithm
from benchmark.worker import run_with_timeout


@pytest.mark.skipif(shutil.which("g++") is None, reason="g++ is required for C++ algorithm tests")
def test_run_with_timeout_reports_crash(tmp_path):
    source = tmp_path / "bad.cpp"
    source.write_text(
        '#include <iostream>\nint main() { std::cerr << "boom"; return 1; }\n',
        encoding="utf-8",
    )
    algorithm = compile_algorithm(AlgorithmSpec("bad", source), tmp_path / "build")

    result = run_with_timeout(algorithm, "AT", ["AT"], 2, {}, 2)

    assert result["status"] == "crash"
    assert "boom" in result["error"]
