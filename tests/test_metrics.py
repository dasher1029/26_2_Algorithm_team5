from benchmark.metrics import normalized_accuracy, positional_distance


def test_positional_distance_counts_mismatches_and_length_difference():
    assert positional_distance("ATCG", "ATGG") == 1
    assert positional_distance("", "AT") == 2
    assert positional_distance("ATCG", "AT") == 2
    assert positional_distance("ATCG", "ATG") == 2


def test_normalized_accuracy():
    accuracy, distance = normalized_accuracy("ATCG", "ATGG")
    assert distance == 1
    assert accuracy == 0.75
