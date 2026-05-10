from benchmark.metrics import edit_distance, normalized_accuracy


def test_edit_distance():
    assert edit_distance("ATCG", "ATGG") == 1
    assert edit_distance("", "AT") == 2


def test_normalized_accuracy():
    accuracy, distance = normalized_accuracy("ATCG", "ATGG")
    assert distance == 1
    assert accuracy == 0.75
