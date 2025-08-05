#include <iostream>
#include <stack>
using namespace std;

int main() {
    // 4. stack - 栈 (LIFO)
    stack<int> stk;
    stk.push(10);
    stk.push(20);
    stk.push(30);
    cout << "Stack (top to bottom): ";
    while (!stk.empty()) {
        cout << stk.top() << " ";
        stk.pop();
    }
    cout << endl;
    return 0;
}
