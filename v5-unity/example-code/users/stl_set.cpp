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
    // 7. set - 有序不重复集合
    set<int> s = {5, 3, 1, 4, 2};
    s.insert(3); // 不会插入重复值
    s.insert(6);
    printContainer(s, "Set");
    return 0;
}
