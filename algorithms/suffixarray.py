"""
Suffix Array + Binary Search based DNA reconstruction.

Algorithm overview:
  1. Concatenate all reads with separators → build suffix array
  2. For each read, binary search SA to find overlapping reads (O(L log n) per query)
  3. Build overlap graph → greedy assembly → consensus

Complexity:
  - SA build (naive):  O(M·L · log(M·L))
  - Overlap detection: O(M · L · log(M·L))   vs naive O(M² · L)
  - Assembly:          O(M · log M)
"""

from _assembly_utils import trim_to_reference_length

SEPARATOR = "#"
TERMINATOR = "$"


# ---------------------------------------------------------------------------
# 1. Suffix Array
# ---------------------------------------------------------------------------

def build_suffix_array(text: str) -> list[int]:
    """Return suffix array of text (naive O(n log^2 n) sort).

    SA[i] = j  means  text[j:] is the i-th lexicographically smallest suffix.
    """
    # TODO: implement
    return sorted(range(len(text)), key=lambda i: text[i:])


# ---------------------------------------------------------------------------
# 2. Binary Search on SA
# ---------------------------------------------------------------------------

def sa_search(sa: list[int], text: str, pattern: str) -> tuple[int, int]:
    """Return (lo, hi) s.t. SA[lo:hi] are indices where text[SA[i]:] starts with pattern.

    Uses binary search → O(|pattern| · log n).
    Returns (lo, lo) (empty range) if pattern not found.
    """
    n = len(sa)

    # lower bound
    lo, hi = 0, n
    while lo < hi:
        mid = (lo + hi) // 2
        suffix = text[sa[mid]: sa[mid] + len(pattern)]
        if suffix < pattern:
            lo = mid + 1
        else:
            hi = mid
    left = lo

    # upper bound
    hi = n
    while lo < hi:
        mid = (lo + hi) // 2
        suffix = text[sa[mid]: sa[mid] + len(pattern)]
        if suffix <= pattern:
            lo = mid + 1
        else:
            hi = mid

    return left, lo


# ---------------------------------------------------------------------------
# 3. Overlap Detection
# ---------------------------------------------------------------------------

def find_overlaps(reads: list[str], min_overlap: int) -> dict[int, list[tuple[int, int]]]:
    """Return adjacency list: overlaps[i] = [(j, overlap_len), ...].

    For each read i, find reads j where read_i[-k:] == read_j[:k] (k >= min_overlap).
    Uses SA binary search instead of naive O(M²·L) scan.
    """
    # Build concatenated text with separators
    text = SEPARATOR.join(reads) + TERMINATOR
    sa = build_suffix_array(text)

    overlaps: dict[int, list[tuple[int, int]]] = {i: [] for i in range(len(reads))}

    # Map each SA position back to which read it belongs to
    # TODO: build pos→read_index mapping to filter cross-separator hits

    read_start_positions = []
    pos = 0
    for i, read in enumerate(reads):
        read_start_positions.append(pos)
        pos += len(read) + 1  # +1 for separator

    def pos_to_read(p: int) -> int | None:
        """Return read index for position p, or None if on separator/terminator."""
        for i in range(len(reads) - 1, -1, -1):
            start = read_start_positions[i]
            end = start + len(reads[i])
            if start <= p < end:
                return i
        return None

    # For each read i, search suffixes of length min_overlap..len(read)
    for i, read in enumerate(reads):
        for k in range(len(read), min_overlap - 1, -1):
            suffix = read[-k:]                      # last k chars of read i
            lo, hi = sa_search(sa, text, suffix)
            for idx in range(lo, hi):
                hit_pos = sa[idx]
                j = pos_to_read(hit_pos)
                if j is None or j == i:
                    continue
                # Confirm hit_pos is exactly the start of read j
                if hit_pos == read_start_positions[j]:
                    overlaps[i].append((j, k))
                    break                           # longest overlap found, stop

    return overlaps


# ---------------------------------------------------------------------------
# 4. Greedy Assembly
# ---------------------------------------------------------------------------

def greedy_assemble(reads: list[str], overlaps: dict[int, list[tuple[int, int]]], reference_length: int) -> str:
    """Greedy path through overlap graph → contig string."""
    if not reads:
        return ""

    used = [False] * len(reads)
    # Start with read that has best outgoing overlap
    best_start = max(range(len(reads)), key=lambda i: max((ov for _, ov in overlaps[i]), default=0))

    contig = reads[best_start]
    used[best_start] = True
    current = best_start

    while len(contig) < reference_length:
        candidates = [(j, ov) for j, ov in overlaps[current] if not used[j]]
        if not candidates:
            break
        next_read, overlap_len = max(candidates, key=lambda x: x[1])
        contig += reads[next_read][overlap_len:]
        used[next_read] = True
        current = next_read

    return trim_to_reference_length(contig, reference_length)


# ---------------------------------------------------------------------------
# 5. Entry point
# ---------------------------------------------------------------------------

def reconstruct(reads: list[str], reference_length: int, metadata: dict) -> str:
    """Reconstruct DNA sequence from short reads using suffix array + binary search.

    Time complexity:  O(M·L · log(M·L))  for SA build + overlap detection
    Space complexity: O(M·L)             for SA + concatenated text
    """
    if not reads:
        return trim_to_reference_length("", reference_length)

    read_length = metadata.get("read_length", len(reads[0]))
    min_overlap = max(3, int(read_length * 0.4))

    overlaps = find_overlaps(reads, min_overlap)
    return greedy_assemble(reads, overlaps, reference_length)
