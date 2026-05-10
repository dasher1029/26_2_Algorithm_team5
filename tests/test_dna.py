from benchmark.dna import ExperimentCase, generate_reference, simulate_reads


def test_generate_reference_is_deterministic():
    assert generate_reference(20, seed=7) == generate_reference(20, seed=7)


def test_simulate_reads_uses_expected_count_and_length():
    case = ExperimentCase(reference_length=100, read_length=10, coverage=3, noise_rate=0, seed=1)
    reference = generate_reference(case.reference_length, case.seed)
    reads = simulate_reads(reference, case)
    assert len(reads) == 30
    assert all(len(read) == 10 for read in reads)
