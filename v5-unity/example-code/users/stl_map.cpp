#include <iostream>
#include <map>
#include <string>
using namespace std;

template <typename K, typename V>
void printMap(const map<K, V>& container, const string& name) {
    cout << name << ": ";
    for (const auto& pair : container) {
        cout << "{" << pair.first << ":" << pair.second << "} ";
    }
    cout << endl;
}

int main() {
    // 9. map - 有序键值对 (键唯一)
    map<string, int> m = {{"Alice", 25}, {"Bob", 30}};
    m["Charlie"] = 35;
    m.insert({"Dave", 40});
    printMap(m, "Map");
    return 0;
}
