from _assembly_utils import greedy_overlap_assemble


def reconstruct(reads, reference_length, metadata):
    """Simple de novo greedy overlap assembler.

    This example does not use the hidden reference. It repeatedly joins reads
    with the strongest suffix-prefix overlap and trims/pads the final contig.
    """
    read_length = metadata.get("read_length", 20)
    min_overlap = max(3, int(read_length * 0.45))
    return greedy_overlap_assemble(reads, reference_length, min_overlap=min_overlap)
