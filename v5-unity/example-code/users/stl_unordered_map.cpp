#include <iostream>
#include <unordered_map>
#include <string>
using namespace std;

int main() {
    // 12. unordered_map - 哈希映射
    unordered_map<string, double> um = {{"pi", 3.14159}, {"e", 2.71828}};
    um["sqrt2"] = 1.41421;
    cout << "Unordered Map: ";
    for (const auto& pair : um) {
        cout << "{" << pair.first << ":" << pair.second << "} ";
    }
    cout << endl;
    return 0;
}
