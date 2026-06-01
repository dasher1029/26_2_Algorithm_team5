#include <iostream>
#include <string>
#include <vector>

int main() {
    int reference_length = 0;
    std::string reference;
    int read_count = 0;
    std::cin >> reference_length >> reference >> read_count;

    std::vector<std::string> reads(read_count);
    for (int i = 0; i < read_count; ++i) {
        std::cin >> reads[i];
    }

    int metadata_count = 0;
    std::cin >> metadata_count;
    std::string line;
    std::getline(std::cin, line);
    for (int i = 0; i < metadata_count; ++i) {
        std::getline(std::cin, line);
    }

    std::string reconstruction;
    for (const std::string& read : reads) {
        reconstruction += read;
        if ((int)reconstruction.size() >= reference_length) {
            break;
        }
    }
    reconstruction.resize(reference_length, 'A');

    std::cout << reconstruction << "\n";
    return 0;
}
