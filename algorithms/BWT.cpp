#include <bits/stdc++.h>
#include <chrono>
#define fast_io ios::sync_with_stdio(false); cin.tie(NULL); cout.tie(NULL)
#define Occ(x, y) occ.query(x, y)

using namespace std;
using hrc = chrono::high_resolution_clock;
using ms  = chrono::duration<double, milli>;

// =============================================
// 설정값 (metadata로 덮어씌워짐)
// =============================================
int    D          = 1;     // 허용 mismatch (SNP) 수
int    READ_LEN   = 30;    // read 길이
int    MAPQ_THRESH   = 20;
double MIN_SUPPORT   = 1.5;
int    MIN_COUNT     = 2;
// =============================================

const int SAMPLE_K = 4;

int cidx(char c) {
    switch(c) {
        case '$':           return 0;
        case 'A': case 'a': return 1;
        case 'C': case 'c': return 2;
        case 'G': case 'g': return 3;
        case 'T': case 't': return 4;
        default:            return -1;
    }
}

// =============================================
// OccSampled
// =============================================
class OccSampled {
    vector<array<int,5>> samples;
    string bwt;
    int k;
public:
    OccSampled(int k = SAMPLE_K) : k(k) {}

    void build(const string& bwt_in) {
        bwt = bwt_in;
        int n = bwt.size();
        samples.resize(n/k + 2, {0,0,0,0,0});
        array<int,5> cnt = {0,0,0,0,0};
        for (int i = 0; i < n; i++) {
            if (i % k == 0) samples[i/k] = cnt;
            cnt[cidx(bwt[i])]++;
        }
    }

    int query(char c, int i) const {
        if (i < 0) return 0;
        int ci = cidx(c);
        int si = (i + 1) / k;
        int cnt = samples[si][ci];
        for (int j = si * k; j <= i; j++)
            if (cidx(bwt[j]) == ci) cnt++;
        return cnt;
    }
};

// =============================================
// FM-Index
// =============================================
struct FMIndex {
    string genome;
    string bwt;
    vector<int> sa;
    array<int,5> C;
    OccSampled occ;
    int n;

    FMIndex() : occ(SAMPLE_K), n(0) {}

    void build(const string& ref) {
        genome = ref + "$";
        n = genome.size();
        buildSA();
        buildBWT();
        buildC();
        occ.build(bwt);
    }

    void buildSA() {
        sa.resize(n);
        iota(sa.begin(), sa.end(), 0);
        vector<int> rank_(n), tmp(n), cnt;
        for(int i=0;i<n;i++) rank_[i]=(unsigned char)genome[i];

        for(long long gap=1;;gap*=2){
            auto key2=[&](int i){ return gap<n&&i+gap<n?rank_[i+gap]+1:0; };
            auto key1=[&](int i){ return rank_[i]; };

            int maxv=*max_element(rank_.begin(),rank_.end())+2;
            cnt.assign(maxv,0);
            for(int i=0;i<n;i++) cnt[key2(i)]++;
            for(int i=1;i<maxv;i++) cnt[i]+=cnt[i-1];
            vector<int> buf(n);
            for(int i=n-1;i>=0;i--) buf[--cnt[key2(sa[i])]]=sa[i];

            cnt.assign(maxv,0);
            for(int i=0;i<n;i++) cnt[key1(i)]++;
            for(int i=1;i<maxv;i++) cnt[i]+=cnt[i-1];
            for(int i=n-1;i>=0;i--) sa[--cnt[key1(buf[i])]]=buf[i];

            tmp[sa[0]]=0;
            for(int i=1;i<n;i++){
                tmp[sa[i]]=tmp[sa[i-1]];
                if(key1(sa[i])!=key1(sa[i-1])||
                   key2(sa[i])!=key2(sa[i-1])) tmp[sa[i]]++;
            }
            rank_=tmp;
            if(rank_[sa[n-1]]==n-1) break;
        }
    }

    void buildBWT() {
        bwt = "";
        for (int i = 0; i < n; i++)
            bwt += genome[(sa[i] - 1 + n) % n];
    }

    void buildC() {
        array<int,5> freq = {0,0,0,0,0};
        for (char c : bwt) freq[cidx(c)]++;
        C[0] = 0;
        for (int i = 1; i < 5; i++) C[i] = C[i-1] + freq[i-1];
    }

    pair<int,int> fmSearch(const string& pattern) const {
        int lo = 0, hi = n - 1;
        for (int i = pattern.size()-1; i >= 0 && lo <= hi; i--) {
            char c = pattern[i];
            lo = C[cidx(c)] + occ.query(c, lo-1);
            hi = C[cidx(c)] + occ.query(c, hi) - 1;
        }
        return {lo, hi};
    }

    vector<int> saSearch(const string& pattern) const {
        auto [lo, hi] = fmSearch(pattern);
        if (lo > hi) return {};
        vector<int> positions;
        for (int i = lo; i <= hi; i++)
            positions.push_back(sa[i]);
        sort(positions.begin(), positions.end());
        return positions;
    }
};

// =============================================
// MAPQ
// =============================================
struct Candidate {
    int    pos;
    int    mm;
    int    mapq;
    double weight;
};

vector<Candidate> calcMAPQ(const vector<pair<int,int>>& raw) {
    if (raw.empty()) return {};

    double total = 0;
    vector<Candidate> cands;
    for (auto& [pos, mm] : raw) {
        double score = pow(0.25, mm);
        total += score;
        cands.push_back({pos, mm, 0, score});
    }
    for (auto& c : cands) {
        double p_wrong = (total - c.weight) / total;
        if      (p_wrong <= 0) c.mapq = 60;
        else if (p_wrong >= 1) c.mapq = 0;
        else    c.mapq = min(60, (int)(-10 * log10(p_wrong)));
        c.weight = c.weight / total;
    }
    return cands;
}

// =============================================
// Seed-and-Extend
// =============================================
struct SeedExtend {
    const FMIndex& fm;
    int D;
    int seed_len;

    SeedExtend(const FMIndex& fm, int D, int read_len)
        : fm(fm), D(D), seed_len(read_len / (D+1)) {}

    int countMismatch(const string& read, int gpos) const {
        int mm = 0, L = read.size();
        int refLen = fm.genome.size() - 1;
        if (gpos < 0 || gpos + L > refLen) return INT_MAX;
        for (int i = 0; i < L; i++)
            if (read[i] != fm.genome[gpos + i])
                if (++mm > D) return mm;
        return mm;
    }

    vector<Candidate> mapOne(const string& read) const {
        int L = read.size();
        set<int> checked;
        vector<pair<int,int>> raw;

        for (int s = 0; s < D+1; s++) {
            int offset = s * seed_len;
            if (offset + seed_len > L) break;
            auto candidates = fm.saSearch(read.substr(offset, seed_len));
            for (int gp : candidates) {
                int rs = gp - offset;
                if (rs < 0 || checked.count(rs)) continue;
                checked.insert(rs);
                int mm = countMismatch(read, rs);
                if (mm <= D) raw.push_back({rs, mm});
            }
        }
        sort(raw.begin(), raw.end());
        return calcMAPQ(raw);
    }
};

// =============================================
// SNP 탐지
// =============================================
struct SNP {
    int   pos;
    char  ref, alt;
    float support;
    int   count;
};

vector<SNP> detectSNPs(
    const string& ref,
    const vector<string>& reads,
    const vector<vector<Candidate>>& mappings,
    int    mapq_thresh = MAPQ_THRESH,
    double min_support = MIN_SUPPORT,
    int    min_count   = MIN_COUNT)
{
    int N = ref.size();
    vector<array<float,5>> wsum (N, {0,0,0,0,0});
    vector<array<int,5>>   count(N, {0,0,0,0,0});

    for (int i = 0; i < (int)reads.size(); i++) {
        for (auto& m : mappings[i]) {
            if (m.mapq < mapq_thresh) continue;
            for (int j = 0; j < (int)reads[i].size(); j++) {
                int gpos = m.pos + j;
                int ci   = cidx(reads[i][j]);
                if (gpos >= N || ci <= 0) continue;
                wsum [gpos][ci] += m.weight;
                count[gpos][ci]++;
            }
        }
    }

    const char bases[] = "$ACGT";
    vector<SNP> snps;
    for (int p = 0; p < N; p++) {
        int ri = cidx(ref[p]);
        if (ri <= 0) continue;
        for (int b = 1; b < 5; b++) {
            if (b == ri) continue;
            if (wsum[p][b]  >= min_support &&
                count[p][b] >= min_count)
                snps.push_back({p, ref[p], bases[b],
                                wsum[p][b], count[p][b]});
        }
    }
    return snps;
}

// =============================================
// 게놈 복원
// =============================================
string restoreGenome(const string& ref, const vector<SNP>& snps) {
    string my_genome = ref;
    for (auto& s : snps)
        my_genome[s.pos] = s.alt;
    return my_genome;
}

// =============================================
// stdin 파싱
// =============================================
struct Input {
    string ref;
    vector<string> reads;
};

Input parseStdin() {
    Input input;

    // reference_length
    int ref_len;
    cin >> ref_len;
    cin.ignore();

    // reference
    getline(cin, input.ref);
    // 유효 DNA 문자만, 대문자 정규화
    string clean_ref = "";
    for (char c : input.ref)
        if (cidx(toupper(c)) >= 0) clean_ref += toupper(c);
    input.ref = clean_ref;

    // read_count
    int read_count;
    cin >> read_count;
    cin.ignore();

    // reads
    input.reads.reserve(read_count);
    for (int i = 0; i < read_count; i++) {
        string line;
        getline(cin, line);
        string clean = "";
        for (char c : line)
            if (cidx(toupper(c)) >= 0) clean += toupper(c);
        if (!clean.empty()) input.reads.push_back(clean);
    }

    // metadata
    int meta_count;
    cin >> meta_count;
    cin.ignore();
    for (int i = 0; i < meta_count; i++) {
        string line;
        getline(cin, line);
        auto eq = line.find('=');
        if (eq == string::npos) continue;
        string key = line.substr(0, eq);
        string val = line.substr(eq + 1);

        // 관련 설정값 덮어쓰기
        if      (key == "read_length")          READ_LEN      = stoi(val);
        else if (key == "genome_mutation_rate")  D = max(1, (int)(stod(val) * 30) + 1);
    }

    return input;
}

// =============================================
// 메인
// =============================================
int main() {
    fast_io;

    auto t_start = hrc::now();

    // stdin 파싱
    Input input = parseStdin();
    const string& ref   = input.ref;
    const auto&   reads = input.reads;

    cerr << "[파일 로드] ref=" << ref.size() << "bp"
         << " reads=" << reads.size() << "개\n";

    // FM-Index 구축
    auto t0 = hrc::now();
    FMIndex fm;
    fm.build(ref);
    cerr << "[FM-Index] " << ms(hrc::now()-t0).count() << " ms\n";

    // Read 매핑
    t0 = hrc::now();
    SeedExtend se(fm, D, READ_LEN);
    vector<vector<Candidate>> mappings(reads.size());
    int mapped = 0;
    for (int i = 0; i < (int)reads.size(); i++) {
        mappings[i] = se.mapOne(reads[i]);
        if (!mappings[i].empty()) mapped++;
    }
    cerr << "[매핑] " << mapped << "/" << reads.size()
         << " " << ms(hrc::now()-t0).count() << " ms\n";

    // SNP 탐지
    t0 = hrc::now();
    auto snps = detectSNPs(ref, reads, mappings);
    cerr << "[SNP] " << snps.size() << "개 "
         << ms(hrc::now()-t0).count() << " ms\n";

    // 게놈 복원
    string restored = restoreGenome(ref, snps);

    cerr << "[전체] " << ms(hrc::now()-t_start).count() << " ms\n";

    // stdout: 복원 게놈만 출력
    cout << restored << "\n";

    return 0;
}
