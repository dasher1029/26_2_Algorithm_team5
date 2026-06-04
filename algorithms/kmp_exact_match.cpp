#include <algorithm>
#include <iostream>
#include <map>
#include <string>
#include <vector>

using namespace std;

// 실패 함수(pi 배열) 계산
vector<int> compute_pi(const string& pattern) {
    int m = pattern.size();
    vector<int> pi(m, 0);
    int j = 0;
    for (int i = 1; i < m; ++i) {
        while (j > 0 && pattern[i] != pattern[j]) {
            j = pi[j - 1];
        }
        if (pattern[i] == pattern[j]) {
            pi[i] = ++j;
        }
    }
    return pi;
}

// 텍스트에서 패턴의 매칭 시작 위치들을 찾음
vector<int> kmp_search(const string& text, const string& pattern) {
    vector<int> matches;
    if (pattern.empty() || pattern.size() > text.size()) {
        return matches;
    }

    vector<int> pi = compute_pi(pattern);
    int n = text.size();
    int m = pattern.size();
    int j = 0;
    
    for (int i = 0; i < n; ++i) {
        while (j > 0 && text[i] != pattern[j]) {
            j = pi[j - 1];
        }
        if (text[i] == pattern[j]) {
            if (j == m - 1) {
                matches.push_back(i - m + 1);
                j = pi[j]; // 다음 매칭을 위해 복원
            } else {
                j++;
            }
        }
    }
    return matches;
}

// DNA 염기 기호를 정수 인덱스(0~3)로 변환
int char_to_idx(char c) {
    if (c == 'A') return 0;
    if (c == 'C') return 1;
    if (c == 'G') return 2;
    if (c == 'T') return 3;

    return -1;
}

// 정수 인덱스(0~3)를 DNA 염기 기호로 변환
char idx_to_char(int idx) {
    if (idx == 0) return 'A';
    if (idx == 1) return 'C';
    if (idx == 2) return 'G';
    if (idx == 3) return 'T';

    return 'A';
}

// 표준 입력에서 key=value 메타데이터 파싱
map<string, string> parse_metadata(int count) {
    map<string, string> metadata;
    string dummy;
    getline(cin, dummy); // 입력 버퍼 비우기 (개행 문자 제거)
    
    for (int i = 0; i < count; ++i) {
        string line;
        getline(cin, line);
        size_t eq_pos = line.find('=');
        if (eq_pos != string::npos) {
            string key = line.substr(0, eq_pos);
            string val = line.substr(eq_pos + 1);
            metadata[key] = val;
        }
    }
    return metadata;
}

// 비둘기집 원리에 따라 리드를 (allowed_mismatches + 1)개의 세그먼트(seed)로 분할
vector<pair<int, string>> split_into_seeds(const string& read, int allowed_mismatches) {
    int k = max(1, allowed_mismatches + 1);
    int base_size = read.size() / k;
    int remainder = read.size() % k;

    vector<pair<int, string>> seeds;
    int start = 0;
    for (int i = 0; i < k; ++i) {
        int cur_size = base_size + (i < remainder ? 1 : 0);
        if (cur_size > 0) {
            seeds.push_back({start, read.substr(start, cur_size)});
        }
        start += cur_size;
    }
    return seeds;
}

// 두 문자열 간의 불일치(mismatch) 수 계산
int get_mismatch_count(const string& reference, const string& read, int ref_start) {
    int mismatches = 0;
    for (int i = 0; i < (int)read.size(); ++i) {
        if (reference[ref_start + i] != read[i]) {
            mismatches++;
        }
    }
    return mismatches;
}

// 리드가 레퍼런스 상에서 가장 잘 매칭되는 시작 위치를 찾음
int find_best_alignment(const string& reference, const string& read, int allowed_mismatches) {
    int best_start = -1;
    int min_mismatches = allowed_mismatches + 1;

    // 리드를 조각내어 매칭 후보를 찾음
    vector<pair<int, string>> seeds = split_into_seeds(read, allowed_mismatches);
    for (const auto& seed : seeds) {
        int seed_offset = seed.first;
        const string& pattern = seed.second;

        // 조각(seed)이 레퍼런스에 정확히 일치하는 위치들을 KMP로 탐색
        for (int matched_pos : kmp_search(reference, pattern)) {
            int candidate_start = matched_pos - seed_offset;
            
            // 유효한 범위 체크
            if (candidate_start < 0 || candidate_start + (int)read.size() > (int)reference.size()) {
                continue;
            }

            int current_mismatches = get_mismatch_count(reference, read, candidate_start);
            if (current_mismatches < min_mismatches) {
                min_mismatches = current_mismatches;
                best_start = candidate_start;
                
                // 완벽한 매칭(0 오차)을 발견하면 즉시 탐색 종료
                if (min_mismatches == 0) {
                    return best_start;
                }
            }
        }
    }

    if (min_mismatches <= allowed_mismatches) {
        return best_start;
    }
    return -1;
}

// 정렬된 리드 정보를 바탕으로 레퍼런스의 각 위치에서 다수결로 서열 복원
string reconstruct_consensus(const string& reference, const vector<pair<int, string>>& placements) {
    int n = reference.size();
    vector<vector<int>> counts(n, vector<int>(4, 0));
    
    // 기본값으로 레퍼런스 게놈의 염기를 카운트에 기여시킴 (기초 가중치)
    for (int i = 0; i < n; ++i) {
        int idx = char_to_idx(reference[i]);
        if (idx >= 0) {
            counts[i][idx] = 1;
        }
    }

    // 각 리드들의 매칭 위치를 기반으로 카운트 누적
    for (const auto& p : placements) {
        int start = p.first;
        const string& read = p.second;
        for (int i = 0; i < (int)read.size(); ++i) {
            int idx = char_to_idx(read[i]);
            int pos = start + i;
            if (idx >= 0 && pos >= 0 && pos < n) {
                counts[pos][idx]++;
            }
        }
    }

    // 다수결로 최종 서열 재구성
    string reconstruction = reference;
    for (int i = 0; i < n; ++i) {
        int best_idx = 0;
        for (int j = 1; j < 4; ++j) {
            if (counts[i][j] > counts[i][best_idx]) {
                best_idx = j;
            }
        }
        reconstruction[i] = idx_to_char(best_idx);
    }
    return reconstruction;
}

int main() {
    // 빠른 입출력 설정
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

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
    map<string, string> metadata = parse_metadata(metadata_count);

    // 메타데이터에 allowed_mismatches가 있으면 그 값으로 업데이트, 없으면 기본값은 2
    int allowed_mismatches = 2;
    if (metadata.find("allowed_mismatches") != metadata.end()) {
        allowed_mismatches = stoi(metadata["allowed_mismatches"]);
    }

    // 각 리드의 최적 배치 찾기
    vector<pair<int, string>> placements;
    for (const string& read : reads) {
        int start = find_best_alignment(reference, read, allowed_mismatches);
        if (start >= 0) {
            placements.push_back({start, read});
        }
    }

    // 최종 서열 복원
    string reconstruction = reconstruct_consensus(reference, placements);
    reconstruction.resize(reference_length, 'A');
    cout << reconstruction << "\n";

    return 0;
}
