#include <iostream>
#include <map>
#include <string>
#include <vector>

using namespace std;

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
    if (read.empty() || read.size() > reference.size()) {
        return -1;
    }

    int best_start = -1;
    int best_mismatches = allowed_mismatches + 1;
    int max_start = (int)reference.size() - (int)read.size();
    for (int start = 0; start <= max_start; ++start) {
        int mismatches = mismatch_count(reference, read, start);
        if (mismatches < best_mismatches) {
            best_mismatches = mismatches;
            best_start = start;
            if (best_mismatches == 0) {
                return best_start;
            }
        }
    }

    if (best_mismatches <= allowed_mismatches) {
        return best_start;
    }
    return -1;
}

string build_consensus(const string& reference, const vector<pair<int, string>>& placements) {
    int n = (int)reference.size();
    vector<vector<int>> counts(n, vector<int>(4, 0));

    for (int i = 0; i < n; ++i) {
        int index = base_index(reference[i]);
        if (index >= 0) {
            counts[i][index] = 1;
        }
    }

    for (const auto& placement : placements) {
        int start = placement.first;
        const string& read = placement.second;
        for (int i = 0; i < (int)read.size(); ++i) {
            int position = start + i;
            int index = base_index(read[i]);
            if (0 <= position && position < n && index >= 0) {
                counts[position][index] += 1;
            }
        }
    }

    string reconstruction = reference;
    for (int i = 0; i < n; ++i) {
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
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int declared_length = 0;
    string reference;
    int read_count = 0;
    cin >> declared_length >> reference >> read_count;

    vector<string> reads(read_count);
    for (int i = 0; i < read_count; ++i) {
        cin >> reads[i];
    }

    int metadata_count = 0;
    cin >> metadata_count;
    map<string, string> metadata = read_metadata(metadata_count);
    int allowed_mismatches = metadata_int(metadata, "allowed_mismatches", 2);

    vector<pair<int, string>> placements;
    placements.reserve(reads.size());
    for (const string& read : reads) {
        int start = find_best_position(reference, read, allowed_mismatches);
        if (start >= 0) {
            placements.push_back({start, read});
        }
    }

    string reconstruction = build_consensus(reference, placements);
    reconstruction.resize(declared_length, 'A');
    cout << reconstruction << '\n';
    return 0;
}
