#include <stdio.h>
#include <stdlib.h>
#include <iostream>
#include <string>
#include <vector>

typedef struct Queue {
    char * elements;
    short front;
    short rear;
} Queue;
typedef struct GenomePiece {
    int genome;
    int position;
} GenomePiece;
typedef struct SectionInfo {
    int perfect_match_info;
    short count_diff;
} SectionInfo;

void makeTable(void);
int hashingInQueue(Queue* genome_piece, short queue_size);
int compareGenomePiece(const void* left, const void* right);
int findPosition(void);
int hashing(char genome_piece[]);
void unhashing(int hash, char genome_piece[]);
int findPerfectMatch(int hash);
short countDiff(char reference_genome_piece[], char genome_piece[]);

int REFERENCE_SIZE = 0;
int TABLE_SIZE = 0;
short PIECE_SIZE = 0;
short READ_SIZE = 0;
char * reference = NULL;
GenomePiece * table_by_genome = NULL;
int * table_by_position = NULL;
int read_count = 0;
char * read = NULL;

void enqueue(Queue* queue, short queue_size, char element) {
    queue->rear = (queue->rear+1)%queue_size;
    queue->elements[queue->rear] = element;
}

void dequeue(Queue* queue, short queue_size) {
    queue->front = (queue->front+1)%queue_size;
}

int main(void) {
    long position = -1;
    char * original_sequence;
    std::string reference_input;
    std::vector<std::string> reads;
    int metadata_count = 0;
    std::string metadata_line;

    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);

    if (!(std::cin >> REFERENCE_SIZE >> reference_input >> read_count)) {
        return 0;
    }

    reads.resize(read_count);
    for (int i = 0; i < read_count; i++) {
        std::cin >> reads[i];
    }

    if (std::cin >> metadata_count) {
        std::getline(std::cin, metadata_line);
        for (int i = 0; i < metadata_count; i++) {
            std::getline(std::cin, metadata_line);
        }
    }

    if (read_count > 0) {
        READ_SIZE = (short)reads[0].size();
    }
    PIECE_SIZE = READ_SIZE/3;
    TABLE_SIZE = REFERENCE_SIZE - PIECE_SIZE + 1;

    original_sequence = (char*)malloc(sizeof(char)*REFERENCE_SIZE);
    for (int i = 0; i < REFERENCE_SIZE; i++) {
        original_sequence[i] = 'N';
    }

    if (read_count == 0 || READ_SIZE == 0 || PIECE_SIZE == 0 || TABLE_SIZE <= 0) {
        std::cout.write(original_sequence, REFERENCE_SIZE);
        std::cout << "\n";
        free(original_sequence);
        return 0;
    }

    reference = (char*)malloc(sizeof(char)*REFERENCE_SIZE);
    for (int i = 0; i < REFERENCE_SIZE; i++) {
        reference[i] = reference_input[i];
    }

    table_by_genome = (GenomePiece*)malloc(sizeof(GenomePiece)*TABLE_SIZE);
    table_by_position = (int*)malloc(sizeof(int)*TABLE_SIZE);
    makeTable();

    free(reference);

    read = (char*)malloc(sizeof(char)*READ_SIZE);
    for (long _ = 0; _ < read_count; _++) {
        for (int i = 0; i < READ_SIZE; i++) {
            read[i] = reads[_][i];
        }

        if ((position = findPosition()) == -1) continue;
        
        for (int i = 0; i < READ_SIZE; i++) {
            original_sequence[position+i] = read[i];
        }
    }

    std::cout.write(original_sequence, REFERENCE_SIZE);
    std::cout << "\n";

    free(table_by_genome);
    free(table_by_position);
    free(original_sequence);
    free(read);

    return 0;
}

void makeTable(void) {
    Queue reference_genome_piece = {NULL, 0, 0};
    short queue_size = PIECE_SIZE+1;
    int index = 0;

    reference_genome_piece.elements = (char*)malloc(sizeof(char)*queue_size);

    for (int i = 0; i < PIECE_SIZE; i++) {
        enqueue(&reference_genome_piece, queue_size, reference[i]);
    }

    table_by_genome[index].genome = hashingInQueue(&reference_genome_piece, queue_size);
    table_by_genome[index].position = index;
    index++;

    while (index < TABLE_SIZE) {
        dequeue(&reference_genome_piece, queue_size);
        enqueue(&reference_genome_piece, queue_size, reference[index+PIECE_SIZE-1]);

        table_by_genome[index].genome = hashingInQueue(&reference_genome_piece, queue_size);
        table_by_genome[index].position = index;
        index++;
    }

    free(reference_genome_piece.elements);

    for (int i = 0; i < index; i++) {
        table_by_position[i] = table_by_genome[i].genome;
    }

    qsort(table_by_genome, index, sizeof(GenomePiece), compareGenomePiece);    
}

int hashingInQueue(Queue* genome_piece, short queue_size) {
    int result = 0;
    int start = (genome_piece->front+1)%queue_size;
    int end_condition = (genome_piece->rear+1)%queue_size;
    for (int i = start; i != end_condition; i = (i+1)%queue_size) {
        result *= 4;
        switch (genome_piece->elements[i]) {
            case 'A':
                result += 0;
                break;
            case 'C':
                result += 1;
                break;
            case 'G':
                result += 2;
                break;
            case 'T':
                result += 3;
                break;
        }
    }
    return result;
}

int compareGenomePiece(const void* left, const void* right) {
    const GenomePiece * left_piece = (const GenomePiece*) left;
    const GenomePiece * right_piece = (const GenomePiece*) right;

    if (left_piece->genome < right_piece->genome) return -1;
    if (left_piece->genome > right_piece->genome) return 1;
    if (left_piece->position < right_piece->position) return -1;
    if (left_piece->position > right_piece->position) return 1;
    return 0;
}

int findPosition(void) {
    int hash;
    short section;
    SectionInfo section_info[3];
    char * reference_piece;
    int reference_piece_position;
    int position;

    for (section = 0; section < 3; section++) {
        hash = hashing(read+(PIECE_SIZE*section));
        section_info[section].perfect_match_info = findPerfectMatch(hash);
        section_info[section].count_diff = READ_SIZE;

        if (section_info[section].perfect_match_info == -1) continue;

        while (section_info[section].perfect_match_info > 0 &&
            table_by_genome[section_info[section].perfect_match_info - 1].genome == hash) section_info[section].perfect_match_info--;
    }

    if (section_info[0].perfect_match_info == -1 &&
        section_info[1].perfect_match_info == -1 &&
        section_info[2].perfect_match_info == -1) {
        return -1;
    }

    reference_piece = (char*)malloc(sizeof(char)*PIECE_SIZE);
    for (section = 0; section < 3; section++) {
        int i;
        if ((i = section_info[section].perfect_match_info) == -1) continue;
        section_info[section].perfect_match_info = -1;

        hash = table_by_genome[i].genome;
        
        for ( ; i < TABLE_SIZE && table_by_genome[i].genome == hash; i++) {
            int target_position = table_by_genome[i].position;
            int start_position;
            short temp = 0;

            if ((start_position = target_position - PIECE_SIZE * section) < 0) continue;
            if (start_position + READ_SIZE > REFERENCE_SIZE) continue;

            for (int compare_section = 0; compare_section < 3; compare_section++) {
                if (compare_section == section) continue;

                reference_piece_position = start_position + PIECE_SIZE * compare_section;
                unhashing(table_by_position[reference_piece_position], reference_piece);
                temp += countDiff(reference_piece, read + PIECE_SIZE * compare_section);
            }

            if (temp < section_info[section].count_diff) {
                section_info[section].perfect_match_info = i;
                section_info[section].count_diff = temp;
            }
        }
    }
    free(reference_piece);

    if (section_info[0].perfect_match_info == -1 &&
        section_info[1].perfect_match_info == -1 &&
        section_info[2].perfect_match_info == -1) {
        return -1;
    }

    for (int i = 2; i > -1; i--) {
        if (section_info[i].perfect_match_info >= 0) {
            section = i;
            position = table_by_genome[section_info[section].perfect_match_info].position;
        }
    }
    for (int i = 0; i < 3; i++) {
        if (section_info[i].count_diff < section_info[section].count_diff) {
            section = i;
            position = table_by_genome[section_info[section].perfect_match_info].position;
        }
    }

    switch (section) {
        case 1:
            position -= PIECE_SIZE * section;
            break;
        case 2:
            position -= PIECE_SIZE * section;
            break;
    }

    return position;
}

int hashing(char genome_piece[]) {
    int result = 0;
    for (int i = 0; i < PIECE_SIZE; i++) {
        result *= 4;
        switch (genome_piece[i]) {
            case 'A':
                result += 0;
                break;
            case 'C':
                result += 1;
                break;
            case 'G':
                result += 2;
                break;
            case 'T':
                result += 3;
                break;
        }
    }
    return result;
}

void unhashing(int hash, char genome_piece[]) {
    for (int i = PIECE_SIZE-1; i >= 0; i--) {
        switch (hash % 4) {
            case 0:
                genome_piece[i] = 'A';
                break;
            case 1:
                genome_piece[i] = 'C';
                break;
            case 2:
                genome_piece[i] = 'G';
                break;
            case 3:
                genome_piece[i] = 'T';
                break;
        }
        hash /= 4;
    }
}

int findPerfectMatch(int hash) {
    long start = 0;
    long end = TABLE_SIZE-1;
    int index;

    while (start <= end) {
        index = (start + end)/2;
        if (table_by_genome[index].genome == hash) return index;
        else if (table_by_genome[index].genome > hash) end = index - 1;
        else if (table_by_genome[index].genome < hash) start = index + 1;
    }

    return -1;
}

short countDiff(char reference_genome_piece[], char genome_piece[]) {
    short count = 0;
    for (int i = 0; i < PIECE_SIZE; i++) {
        if (reference_genome_piece[i] != genome_piece[i]) count++;
    }
    return count;
}
