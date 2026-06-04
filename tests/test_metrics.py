from benchmark.metrics import (
    edit_distance,
    hamming_distance,
    mutation_recall,
    normalized_accuracy,
    positional_distance,
)


def test_hamming_distance_counts_mismatches_and_length_difference():
    assert hamming_distance("ATCG", "ATGG") == 1
    assert hamming_distance("", "AT") == 2
    assert hamming_distance("ATCG", "AT") == 2
    assert hamming_distance("ATCG", "ATG") == 2


def test_positional_distance_is_a_hamming_alias():
    assert positional_distance is hamming_distance


def test_normalized_accuracy():
    accuracy, distance = normalized_accuracy("ATCG", "ATGG")
    assert distance == 1
    assert accuracy == 0.75


def test_edit_distance_rewards_a_shift_that_hamming_punishes():
    truth = "ATCGATCGAT"
    shifted = "A" + truth[:-1]  # one insertion at the front, everything slides
    # Hamming sees almost every position as wrong...
    assert hamming_distance(truth, shifted) > 5
    # ...but the real edit distance is tiny (one insert + one delete at the ends).
    distance, exact = edit_distance(truth, shifted)
    assert exact is True
    assert distance <= 2


def test_edit_distance_caps_and_flags_inexact():
    left = "AC" * 200
    right = "GT" * 200  # every position differs; no cheap alignment
    distance, exact = edit_distance(left, right, max_band=8)
    assert exact is False
    assert distance <= hamming_distance(left, right)


def test_mutation_recall_scores_only_variant_positions():
    reference = "AAAA"
    gold = "ACGA"  # variants at positions 1 and 2
    reconstruction = "ACAA"  # recovers position 1, misses position 2
    recall, variants = mutation_recall(reference, gold, reconstruction)
    assert variants == 2
    assert recall == 0.5


def test_mutation_recall_blank_when_no_variants():
    recall, variants = mutation_recall("ATCG", "ATCG", "ATCG")
    assert recall is None
    assert variants == 0
