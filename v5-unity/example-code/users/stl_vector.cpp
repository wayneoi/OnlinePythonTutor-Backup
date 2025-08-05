#include <iostream>
#include <vector>
#include <string>
using namespace std;

// 打印容器内容的辅助函数11wayneaaaaaabb
template <typename T>
void printContainer(const T& container, const string& name) {
    cout << name << ": ";
    for (const auto& item : container) {
        cout << item << " ";
    }
    cout << endl;
}

int main() {
    // 1. vector - 动态数组
    vector<int> vec = {1, 2, 3, 4, 5};
    vec.push_back(6);
    vec.insert(vec.begin() + 2, 10);
    printContainer(vec, "Vector");
    return 0;
}
