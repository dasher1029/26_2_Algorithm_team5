#include <algorithm>
#include <iostream>
#include <map>
#include <string>
#include <vector>

using namespace std;

vector<int> prefix_function(const string& text) {
    vector<int> pi(text.size(), 0);
    for (int i = 1; i < (int)text.size(); ++i) {
        int j = pi[i - 1];
        while (j > 0 && text[i] != text[j]) {
            j = pi[j - 1];
        }
        if (text[i] == text[j]) {
            ++j;
        }
        pi[i] = j;
    }
    return pi;
}

vector<int> kmp_search(const string& text, const string& pattern) {
    vector<int> matches;
    if (pattern.empty() || pattern.size() > text.size()) {
        return matches;
    }

    string combined = pattern + "#" + text;
    vector<int> pi = prefix_function(combined);
    int pattern_length = pattern.size();
    for (int i = pattern_length + 1; i < (int)combined.size(); ++i) {
        if (pi[i] == pattern_length) {
            matches.push_back(i - 2 * pattern_length);
        }
    }
    return matches;
}

int base_index(char base) {
    if (base == 'A') return 0;
    if (base == 'C') return 1;
    if (base == 'G') return 2;
    if (base == 'T') return 3;
    return -1;
}

char index_base(int index) {
    static const string bases = "ACGT";
    return bases[index];
}

map<string, string> read_metadata(int metadata_count) {
    map<string, string> metadata;
    string line;
    getline(cin, line);
    for (int i = 0; i < metadata_count; ++i) {
        getline(cin, line);
        size_t equals = line.find('=');
        if (equals != string::npos) {
            metadata[line.substr(0, equals)] = line.substr(equals + 1);
        }
    }
    return metadata;
}

int metadata_int(const map<string, string>& metadata, const string& key, int default_value) {
    auto found = metadata.find(key);
    if (found == metadata.end()) {
        return default_value;
    }
    return stoi(found->second);
}

vector<pair<int, string>> split_seeds(const string& read, int allowed_mismatches) {
    int segment_count = max(1, allowed_mismatches + 1);
    int base_size = read.size() / segment_count;
    int remainder = read.size() % segment_count;

    vector<pair<int, string>> seeds;
    int start = 0;
    for (int i = 0; i < segment_count; ++i) {
        int size = base_size + (i < remainder ? 1 : 0);
        if (size > 0) {
            seeds.push_back({start, read.substr(start, size)});
        }
        start += size;
    }
    return seeds;
}

int mismatch_count(const string& reference, const string& read, int start) {
    int mismatches = 0;
    for (int i = 0; i < (int)read.size(); ++i) {
        if (reference[start + i] != read[i]) {
            ++mismatches;
        }
    }
    return mismatches;
}

int find_best_position(const string& reference, const string& read, int allowed_mismatches) {
    int best_start = -1;
    int best_mismatches = allowed_mismatches + 1;

    for (const auto& seed : split_seeds(read, allowed_mismatches)) {
        int seed_offset = seed.first;
        const string& pattern = seed.second;
        for (int seed_position : kmp_search(reference, pattern)) {
            int candidate_start = seed_position - seed_offset;
            if (candidate_start < 0 || candidate_start + (int)read.size() > (int)reference.size()) {
                continue;
            }

            int mismatches = mismatch_count(reference, read, candidate_start);
            if (mismatches < best_mismatches) {
                best_mismatches = mismatches;
                best_start = candidate_start;
                if (best_mismatches == 0) {
                    return best_start;
                }
            }
        }
    }

    if (best_mismatches <= allowed_mismatches) {
        return best_start;
    }
    return -1;
}

string build_consensus(const string& reference, const vector<pair<int, string>>& placements) {
    vector<vector<int>> counts(reference.size(), vector<int>(4, 0));
    for (int i = 0; i < (int)reference.size(); ++i) {
        int index = base_index(reference[i]);
        if (index >= 0) {
            counts[i][index] = 1;
        }
    }

    for (const auto& placement : placements) {
        int start = placement.first;
        const string& read = placement.second;
        for (int i = 0; i < (int)read.size(); ++i) {
            int index = base_index(read[i]);
            int position = start + i;
            if (index >= 0 && 0 <= position && position < (int)reference.size()) {
                counts[position][index] += 1;
            }
        }
    }

    string reconstruction = reference;
    for (int i = 0; i < (int)counts.size(); ++i) {
        int best = 0;
        for (int j = 1; j < 4; ++j) {
            if (counts[i][j] > counts[i][best]) {
                best = j;
            }
        }
        reconstruction[i] = index_base(best);
    }
    return reconstruction;
}

int main() {
    int reference_length = 0;
    string reference;
    int read_count = 0;
    cin >> reference_length >> reference >> read_count;

    vector<string> reads(read_count);
    for (int i = 0; i < read_count; ++i) {
        cin >> reads[i];
    }

    int metadata_count = 0;
    cin >> metadata_count;
    map<string, string> metadata = read_metadata(metadata_count);
    int allowed_mismatches = metadata_int(metadata, "allowed_mismatches", 2);

    vector<pair<int, string>> placements;
    for (const string& read : reads) {
        int start = find_best_position(reference, read, allowed_mismatches);
        if (start >= 0) {
            placements.push_back({start, read});
        }
    }

    string reconstruction = build_consensus(reference, placements);
    reconstruction.resize(reference_length, 'A');
    cout << reconstruction << "\n";
    return 0;
}
