from collections import defaultdict

from _assembly_utils import consensus_from_placements, hamming_distance, trim_to_reference_length


DEFAULT_ALLOWED_MISMATCHES = 3


def _build_seed(reads, reference_length):
    ordered = sorted(reads, key=len, reverse=True)
    seed = "".join(ordered)
    return trim_to_reference_length(seed, reference_length)


def _split_segments(read, allowed_mismatches):
    """Split a read into e + 1 segments for pigeonhole matching."""
    segment_count = max(1, allowed_mismatches + 1)
    base_size = len(read) // segment_count
    remainder = len(read) % segment_count

    segments = []
    start = 0
    for index in range(segment_count):
        size = base_size + (1 if index < remainder else 0)
        end = start + size
        if size > 0:
            segments.append((start, read[start:end]))
        start = end
    return segments


def _build_position_table(seed, segment_lengths):
    """Map exact seed segments to all seed positions where they appear."""
    table = {}
    for length in sorted(set(segment_lengths)):
        positions = defaultdict(list)
        if length <= 0 or length > len(seed):
            table[length] = positions
            continue
        for start in range(0, len(seed) - length + 1):
            positions[seed[start : start + length]].append(start)
        table[length] = positions
    return table


def _candidate_starts(read, position_table, allowed_mismatches, reference_length):
    candidates = set()
    for segment_offset, segment in _split_segments(read, allowed_mismatches):
        positions = position_table.get(len(segment), {})
        for seed_position in positions.get(segment, []):
            candidate_start = seed_position - segment_offset
            if 0 <= candidate_start <= reference_length - len(read):
                candidates.add(candidate_start)
    return candidates


def _best_position(seed, read, position_table, allowed_mismatches):
    candidates = _candidate_starts(read, position_table, allowed_mismatches, len(seed))

    # If no segment matched exactly, fall back to a full scan so the example is
    # robust even when the rough seed is poor.
    if not candidates:
        candidates = range(0, max(1, len(seed) - len(read) + 1))

    best_start = 0
    best_distance = None
    for start in candidates:
        window = seed[start : start + len(read)]
        distance = hamming_distance(window, read)
        if best_distance is None or distance < best_distance:
            best_start = start
            best_distance = distance
            if distance <= allowed_mismatches:
                break
    return best_start


def reconstruct(reads, reference_length, metadata):
    """Pigeonhole principle position-table mapping example.

    If up to e mismatches are allowed, split each read into e + 1 segments.
    At least one segment must match exactly, so the position table indexes exact
    segment matches and only verifies those candidate positions.
    """
    if not reads:
        return trim_to_reference_length("", reference_length)

    allowed_mismatches = int(metadata.get("allowed_mismatches", DEFAULT_ALLOWED_MISMATCHES))
    seed = _build_seed(reads, reference_length)
    all_segment_lengths = []
    for read in reads:
        all_segment_lengths.extend(len(segment) for _, segment in _split_segments(read, allowed_mismatches))
    position_table = _build_position_table(seed, all_segment_lengths)

    placements = []
    for read in reads:
        start = _best_position(seed, read, position_table, allowed_mismatches)
        placements.append((start, read))

    return consensus_from_placements(reference_length, placements)
