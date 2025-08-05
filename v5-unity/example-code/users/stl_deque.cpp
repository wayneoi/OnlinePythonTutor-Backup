#include <iostream>
#include <deque>
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
    // 3. deque - 双端队列
    deque<double> dq = {1.1, 2.2, 3.3};
    dq.push_front(0.0);
    dq.push_back(4.4);
    printContainer(dq, "Deque");
    return 0;
}
