from collections import Counter


def trim_to_reference_length(sequence, reference_length):
    if len(sequence) >= reference_length:
        return sequence[:reference_length]
    return sequence + ("N" * (reference_length - len(sequence)))


def overlap_length(left, right, min_overlap=3):
    max_size = min(len(left), len(right))
    for size in range(max_size, min_overlap - 1, -1):
        if left[-size:] == right[:size]:
            return size
    return 0


def greedy_overlap_assemble(reads, reference_length, min_overlap=3):
    unused = [read for read in reads if read]
    if not unused:
        return trim_to_reference_length("", reference_length)

    contig = unused.pop(0)
    while unused and len(contig) < reference_length:
        best_index = -1
        best_overlap = -1
        best_read = ""
        best_prepend = False

        for index, read in enumerate(unused):
            append_overlap = overlap_length(contig, read, min_overlap)
            prepend_overlap = overlap_length(read, contig, min_overlap)

            if append_overlap > best_overlap:
                best_index = index
                best_overlap = append_overlap
                best_read = read
                best_prepend = False

            if prepend_overlap > best_overlap:
                best_index = index
                best_overlap = prepend_overlap
                best_read = read
                best_prepend = True

        if best_index == -1:
            break

        unused.pop(best_index)
        if best_overlap <= 0:
            contig += best_read
        elif best_prepend:
            contig = best_read + contig[best_overlap:]
        else:
            contig = contig + best_read[best_overlap:]

    return trim_to_reference_length(contig, reference_length)


def consensus_from_placements(reference_length, placements):
    columns = [Counter() for _ in range(reference_length)]
    for start, read in placements:
        for offset, base in enumerate(read):
            position = start + offset
            if 0 <= position < reference_length:
                columns[position][base] += 1

    consensus = []
    for column in columns:
        if not column:
            consensus.append("N")
        else:
            consensus.append(column.most_common(1)[0][0])
    return "".join(consensus)


def hamming_distance(left, right):
    return sum(a != b for a, b in zip(left, right)) + abs(len(left) - len(right))
