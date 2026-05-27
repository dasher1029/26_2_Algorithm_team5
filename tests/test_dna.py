from benchmark.dna import (
    ExperimentCase,
    build_experiment_inputs,
    create_my_genome,
    load_reference_text,
    simulate_reads,
    slice_reference,
)


def test_load_reference_text_extracts_dna_bases(tmp_path):
    reference_file = tmp_path / "reference.txt"
    reference_file.write_text(">id\nATcg xyz\nNNA-T-C-G\n", encoding="utf-8")

    assert load_reference_text(reference_file) == "ATCGATCG"


def test_create_my_genome_is_deterministic():
    reference_slice = "ATCGATCGATCG"

    left = create_my_genome(reference_slice, mutation_rate=0.25, seed=7)
    right = create_my_genome(reference_slice, mutation_rate=0.25, seed=7)

    assert left == right


def test_create_my_genome_zero_mutation_copies_reference_slice():
    reference_slice = "ATCGATCGATCG"

    assert create_my_genome(reference_slice, mutation_rate=0.0, seed=7) == reference_slice


def test_simulate_reads_uses_expected_count_and_length():
    case = ExperimentCase(reference_length=100, read_length=10, coverage=3, noise_rate=0, seed=1)
    gold_standard = "ATCG" * 25

    reads = simulate_reads(gold_standard, case)

    assert len(reads) == 30
    assert all(len(read) == 10 for read in reads)


def test_build_experiment_inputs_uses_my_genome_as_read_source(tmp_path):
    reference_file = tmp_path / "reference.txt"
    reference_file.write_text("AAAACCCCGGGGTTTT", encoding="utf-8")
    case = ExperimentCase(
        reference_length=8,
        read_length=4,
        coverage=2,
        noise_rate=0,
        seed=3,
        reference_path=str(reference_file),
        reference_start=4,
        genome_mutation_rate=0.0,
    )

    reference_slice, gold_standard, reads = build_experiment_inputs(case)

    assert reference_slice == slice_reference("AAAACCCCGGGGTTTT", 4, 8)
    assert gold_standard == "CCCCGGGG"
    assert len(reads) == 4
    assert all(read in gold_standard for read in reads)
