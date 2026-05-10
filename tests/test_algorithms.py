from benchmark.algorithms import discover_algorithms


def test_discover_algorithms_ignores_template_and_private_files(tmp_path):
    (tmp_path / "alice.py").write_text("def reconstruct(reads, reference_length, metadata): return ''")
    (tmp_path / "template.py").write_text("")
    (tmp_path / "_helper.py").write_text("")

    specs = discover_algorithms(tmp_path)

    assert [spec.name for spec in specs] == ["alice"]
