// Suffix array + binary search 기반 genome reconstruction.
//
// 파이프라인:
//   1) reference 에 대해 suffix array 를 만든다 (radix prefix-doubling, O(n log n)).
//   2) 각 read 를 allowed_mismatches+1 개의 seed 로 쪼갠다. mismatch 가
//      allowed_mismatches 이하라면 비둘기집 원리상 적어도 한 seed 는 정확히 일치한다.
//   3) 각 seed 를 suffix array 위에서 binary search 로 정확 매칭하여 후보 위치를 얻고,
//      read 전체 mismatch 가 가장 적은 위치를 그 read 의 매핑 위치로 고른다.
//   4) 매핑된 read 들로 위치별 다수결(consensus)을 내어 my genome 을 복원한다.
//      reference 는 각 위치의 prior 로 1표를 갖는다.

#include <algorithm>
#include <iostream>
#include <map>
#include <string>
#include <vector>

using namespace std;

static string reference;
static int reference_length = 0;

// reference 에 sentinel('\1', 'A'~'T' 보다 작음)을 붙여 표준 suffix array 를 만든다.
// 반환 배열 크기는 reference.size()+1 이며 SA[0] 은 sentinel suffix 다.
vector<int> build_suffix_array(const string& text) {
    string s = text;
    s.push_back('\1');
    int n = (int)s.size();
    const int ALPHA = 256;

    vector<int> sa(n), rnk(n), nsa(n), nrnk(n);
    vector<int> cnt(max(n, ALPHA), 0);

    for (int i = 0; i < n; ++i) cnt[(unsigned char)s[i]]++;
    for (int i = 1; i < ALPHA; ++i) cnt[i] += cnt[i - 1];
    for (int i = 0; i < n; ++i) sa[--cnt[(unsigned char)s[i]]] = i;

    rnk[sa[0]] = 0;
    int classes = 1;
    for (int i = 1; i < n; ++i) {
        if (s[sa[i]] != s[sa[i - 1]]) ++classes;
        rnk[sa[i]] = classes - 1;
    }

    for (int k = 1; k < n; k <<= 1) {
        // 두 번째 키(i+k 의 rank)를 기준으로 한 번 정렬한 효과를 cyclic shift 로 얻는다.
        for (int i = 0; i < n; ++i) {
            nsa[i] = sa[i] - k;
            if (nsa[i] < 0) nsa[i] += n;
        }
        // 첫 번째 키(rank)로 counting sort. nsa 가 두 번째 키 순서를 유지하므로 안정 정렬이면 충분.
        fill(cnt.begin(), cnt.begin() + classes, 0);
        for (int i = 0; i < n; ++i) cnt[rnk[nsa[i]]]++;
        for (int i = 1; i < classes; ++i) cnt[i] += cnt[i - 1];
        for (int i = n - 1; i >= 0; --i) sa[--cnt[rnk[nsa[i]]]] = nsa[i];

        nrnk[sa[0]] = 0;
        classes = 1;
        for (int i = 1; i < n; ++i) {
            int cur_first = rnk[sa[i]];
            int cur_second = rnk[(sa[i] + k) % n];
            int prev_first = rnk[sa[i - 1]];
            int prev_second = rnk[(sa[i - 1] + k) % n];
            if (cur_first != prev_first || cur_second != prev_second) ++classes;
            nrnk[sa[i]] = classes - 1;
        }
        rnk = nrnk;
        if (classes == n) break;
    }
    return sa;
}

// reference[pos..] 의 앞부분을 pattern 과 사전식 비교한다. -1: 작음, 0: pattern 이 prefix, 1: 큼.
// reference 가 먼저 끝나면(짧으면) 작은 것으로 본다 -> sentinel suffix 도 자연히 제외된다.
int compare_at(int pos, const string& pattern) {
    for (int i = 0; i < (int)pattern.size(); ++i) {
        if (pos + i >= reference_length) return -1;
        char c = reference[pos + i];
        if (c < pattern[i]) return -1;
        if (c > pattern[i]) return 1;
    }
    return 0;
}

// pattern 을 prefix 로 갖는 suffix 들의 SA 구간 [left, right) 을 binary search 로 찾는다.
pair<int, int> find_range(const vector<int>& sa, const string& pattern) {
    int n = (int)sa.size();
    int lo = 0, hi = n;
    while (lo < hi) {
        int mid = (lo + hi) / 2;
        if (compare_at(sa[mid], pattern) < 0) lo = mid + 1;
        else hi = mid;
    }
    int left = lo;
    hi = n;
    while (lo < hi) {
        int mid = (lo + hi) / 2;
        if (compare_at(sa[mid], pattern) <= 0) lo = mid + 1;
        else hi = mid;
    }
    return {left, lo};
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

// read 를 allowed_mismatches+1 개의 seed (시작 offset, 부분 문자열)로 균등 분할한다.
vector<pair<int, string>> split_seeds(const string& read, int allowed_mismatches) {
    int segment_count = max(1, allowed_mismatches + 1);
    int base_size = (int)read.size() / segment_count;
    int remainder = (int)read.size() % segment_count;

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

int mismatch_count(const string& read, int start) {
    int mismatches = 0;
    for (int i = 0; i < (int)read.size(); ++i) {
        if (reference[start + i] != read[i]) {
            ++mismatches;
        }
    }
    return mismatches;
}

// 각 seed 의 정확 매칭 위치를 suffix array 에서 찾고, read 전체 mismatch 가 가장 적은
// 후보 시작 위치를 고른다. allowed_mismatches 를 넘으면 매핑 실패(-1).
int find_best_position(const vector<int>& sa, const string& read, int allowed_mismatches) {
    int best_start = -1;
    int best_mismatches = allowed_mismatches + 1;

    for (const auto& seed : split_seeds(read, allowed_mismatches)) {
        int seed_offset = seed.first;
        const string& pattern = seed.second;
        pair<int, int> range = find_range(sa, pattern);
        for (int i = range.first; i < range.second; ++i) {
            int candidate_start = sa[i] - seed_offset;
            if (candidate_start < 0 || candidate_start + (int)read.size() > reference_length) {
                continue;
            }
            int mismatches = mismatch_count(read, candidate_start);
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

// 위치별로 reference(1표) + 매핑된 read 들의 염기를 모아 다수결로 복원한다.
string build_consensus(const vector<pair<int, string>>& placements) {
    vector<vector<int>> counts(reference_length, vector<int>(4, 0));
    for (int i = 0; i < reference_length; ++i) {
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
            if (index >= 0 && 0 <= position && position < reference_length) {
                counts[position][index] += 1;
            }
        }
    }

    string reconstruction = reference;
    for (int i = 0; i < reference_length; ++i) {
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
    int read_count = 0;
    cin >> declared_length >> reference >> read_count;
    reference_length = (int)reference.size();

    vector<string> reads(read_count);
    for (int i = 0; i < read_count; ++i) {
        cin >> reads[i];
    }

    int metadata_count = 0;
    cin >> metadata_count;
    map<string, string> metadata = read_metadata(metadata_count);
    int allowed_mismatches = metadata_int(metadata, "allowed_mismatches", 2);

    vector<int> sa = build_suffix_array(reference);

    vector<pair<int, string>> placements;
    placements.reserve(reads.size());
    for (const string& read : reads) {
        if (read.empty()) continue;
        int start = find_best_position(sa, read, allowed_mismatches);
        if (start >= 0) {
            placements.push_back({start, read});
        }
    }

    string reconstruction = build_consensus(placements);
    reconstruction.resize(declared_length, 'A');
    cout << reconstruction << "\n";
    return 0;
}
