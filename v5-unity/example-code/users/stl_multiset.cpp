#include <iostream>
#include <set>
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
    // 8. multiset - 有序可重复集合
    multiset<int> ms = {1, 2, 2, 3, 3, 3};
    ms.insert(2);
    printContainer(ms, "Multiset");
    return 0;
}
