#include <iostream>
#include <string>

using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int reference_length = 0;
    cin >> reference_length;

    string reference;
    cin >> reference;

    int read_count = 0;
    cin >> read_count;

    string reconstruction;
    for (int i = 0; i < read_count; ++i) {
        string read;
        cin >> read;
        reconstruction += read;
    }

    int metadata_count = 0;
    cin >> metadata_count;

    string metadata;
    for (int i = 0; i < metadata_count; ++i) {
        cin >> metadata;
    }

    if (static_cast<int>(reconstruction.size()) < reference_length) {
        reconstruction.resize(reference_length, 'A');
    } else {
        reconstruction.resize(reference_length);
    }

    cout << reconstruction << '\n';
    return 0;
}
