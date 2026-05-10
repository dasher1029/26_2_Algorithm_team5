from collections import defaultdict

from _assembly_utils import greedy_overlap_assemble, trim_to_reference_length


def _suffix_array(text):
    return sorted(range(len(text)), key=lambda index: text[index:])


def _bwt(text):
    if not text.endswith("$"):
        text += "$"
    suffixes = _suffix_array(text)
    return "".join(text[index - 1] if index > 0 else "$" for index in suffixes), suffixes, text


def _bwt_kmer_index(reads, k):
    """Build a tiny BWT-backed k-mer position index over concatenated reads."""
    separator = "#"
    text = separator.join(reads) + "$"
    _, suffixes, indexed_text = _bwt(text)
    index = defaultdict(set)

    for suffix_start in suffixes:
        kmer = indexed_text[suffix_start : suffix_start + k]
        if len(kmer) == k and separator not in kmer and "$" not in kmer:
            index[kmer].add(suffix_start)
    return index


def _rank_reads_with_bwt(reads, k):
    index = _bwt_kmer_index(reads, k)
    scored = []
    for read in reads:
        score = 0
        for start in range(0, max(1, len(read) - k + 1)):
            score += len(index.get(read[start : start + k], ()))
        scored.append((score, read))
    scored.sort(reverse=True)
    return [read for _, read in scored]


def reconstruct(reads, reference_length, metadata):
    """BWT-assisted overlap assembly example.

    This small educational example builds a Burrows-Wheeler-transform-based
    k-mer index over the read collection, uses it to prioritize informative
    reads, then performs greedy overlap assembly.
    """
    if not reads:
        return trim_to_reference_length("", reference_length)

    read_length = metadata.get("read_length", len(reads[0]))
    k = max(3, min(12, int(read_length * 0.35)))
    ranked_reads = _rank_reads_with_bwt(reads, k)
    min_overlap = max(3, int(read_length * 0.4))
    return greedy_overlap_assemble(ranked_reads, reference_length, min_overlap=min_overlap)
