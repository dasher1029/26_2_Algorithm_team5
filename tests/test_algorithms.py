from benchmark.algorithms import discover_algorithms


def test_discover_algorithms_uses_cpp_and_ignores_template_private_files(tmp_path):
    (tmp_path / "alice.cpp").write_text("int main() { return 0; }")
    (tmp_path / "template.cpp").write_text("")
    (tmp_path / "_helper.cpp").write_text("")
    (tmp_path / "old_python.py").write_text("")

    specs = discover_algorithms(tmp_path)

    assert [spec.name for spec in specs] == ["alice"]
