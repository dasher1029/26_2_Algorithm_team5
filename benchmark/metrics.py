"""Benchmark metrics."""

from __future__ import annotations


def hamming_distance(left: str, right: str) -> int:
    """Position-by-position mismatches plus the absolute length difference.

    This penalises any frame shift: a single inserted base makes every later
    position disagree. Use ``edit_distance`` for a shift-tolerant comparison.
    """
    shared_length = min(len(left), len(right))
    mismatches = sum(1 for index in range(shared_length) if left[index] != right[index])
    return mismatches + abs(len(left) - len(right))


# Backwards-compatible alias. The metric is a Hamming distance, not a positional
# edit distance; the old name lingers in external callers.
positional_distance = hamming_distance


def normalized_accuracy(reference: str, reconstruction: str) -> tuple[float, int]:
    """Hamming-based accuracy in [0, 1] together with the raw Hamming distance."""
    distance = hamming_distance(reference, reconstruction)
    denominator = max(len(reference), len(reconstruction), 1)
    return max(0.0, 1.0 - distance / denominator), distance


def _banded_edit(left: str, right: str, band: int) -> int:
    """Levenshtein distance restricted to a diagonal band of width ``band``.

    Cells outside ``|i - j| <= band`` are treated as unreachable. The returned
    value equals the true edit distance whenever that distance is ``<= band``.

    Two full-width buffers are allocated once and reused; each row only resets
    and fills its O(band) window, so the work is O(len(left) * band) in time and
    O(len(right)) in space — no per-row allocation.
    """
    n, m = len(left), len(right)
    inf = n + m + 1
    # The corner cell (n, m) sits on diagonal n - m; if that exceeds the band it
    # is unreachable, so the true distance is larger than any in-band alignment.
    if abs(n - m) > band:
        return inf
    prev = [inf] * (m + 1)
    cur = [inf] * (m + 1)
    for j in range(min(m, band) + 1):
        prev[j] = j

    for i in range(1, n + 1):
        lo = max(0, i - band)
        hi = min(m, i + band)
        # Reset just this row's window (plus the left/right boundary cells the
        # recurrence reads) back to inf, leaving the recycled buffer's stale
        # values outside the band harmless.
        for j in range(max(0, lo - 1), min(m, hi + 1) + 1):
            cur[j] = inf
        if lo == 0:
            cur[0] = i
        left_base = left[i - 1]
        for j in range(max(1, lo), hi + 1):
            cost = 0 if left_base == right[j - 1] else 1
            best = prev[j - 1] + cost          # substitute / match
            delete = prev[j] + 1               # delete left[i-1]
            if delete < best:
                best = delete
            insert = cur[j - 1] + 1            # insert right[j-1]
            if insert < best:
                best = insert
            cur[j] = best
        prev, cur = cur, prev
    return prev[m]


def edit_distance(left: str, right: str, max_band: int = 64) -> tuple[int, bool]:
    """Shift-tolerant Levenshtein distance, computed with one banded pass.

    Returns ``(distance, exact)``. A single ``_banded_edit`` runs at a fixed band
    (``max_band``, default 64) — wide enough to credit the small frame shifts a
    greedy assembler produces, while keeping cost at a flat O(len * max_band)
    with no adaptive re-runs. The reported value is ``min(banded, hamming)``,
    always a valid upper bound on the true edit distance.

    ``exact`` is ``True`` only when the result is ``<= max_band`` (the alignment
    provably fits the band). Otherwise — e.g. substitution-heavy outputs whose
    distance equals the Hamming distance — the value is still correct but
    conservatively flagged ``False``; read ``hamming_distance`` for the magnitude.
    Raise ``max_band`` to catch larger shifts at proportionally higher cost.
    """
    hamming = hamming_distance(left, right)
    if left == right:
        return 0, True

    band = min(max_band, max(len(left), len(right)))
    distance = _banded_edit(left, right, band)
    result = min(distance, hamming)
    return result, result <= band


def mutation_recall(
    reference: str, gold_standard: str, reconstruction: str
) -> tuple[float | None, int]:
    """Fraction of true variant positions the reconstruction recovers.

    A variant is a position where ``gold_standard`` (the mutated truth the reads
    came from) differs from ``reference`` (the pre-mutation template the mapping
    algorithms read as input). Recall is the share of those positions where
    ``reconstruction`` matches ``gold_standard``. Returns ``(None, 0)`` when there
    are no variants, so the caller can record a blank cell.
    """
    variants = 0
    recovered = 0
    shared = min(len(reference), len(gold_standard))
    for index in range(shared):
        if reference[index] != gold_standard[index]:
            variants += 1
            if index < len(reconstruction) and reconstruction[index] == gold_standard[index]:
                recovered += 1
    if variants == 0:
        return None, 0
    return recovered / variants, variants
