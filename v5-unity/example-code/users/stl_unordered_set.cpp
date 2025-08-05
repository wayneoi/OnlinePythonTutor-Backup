#include <iostream>
#include <unordered_set>
#include <string>
using namespace std;

template <typename T>
void printContainer(const T& container, const string& name) {
    cout << name << ": ";
    for (const auto& item : container) {
        cout << item << " ";
    }
    cout << endl;
}

int main() {
    // 11. unordered_set - 哈希集合
    unordered_set<string> us = {"red", "green", "blue"};
    us.insert("yellow");
    printContainer(us, "Unordered Set");
    return 0;
}
