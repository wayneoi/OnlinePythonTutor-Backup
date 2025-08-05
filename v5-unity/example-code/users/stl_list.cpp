#include <iostream>
#include <list>
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
    // 2. list - 双向链表
    list<string> lst = {"apple", "banana", "cherry"};
    lst.push_front("orange");
    lst.push_back("grape");
    lst.insert(next(lst.begin(), 2), "kiwi");
    printContainer(lst, "List");
    return 0;
}
