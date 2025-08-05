#include <iostream>
#include <queue>
using namespace std;

int main() {
    // 5. queue - 队列 (FIFO)
    queue<char> q;
    q.push('a');
    q.push('b');
    q.push('c');
    cout << "Queue (front to back): ";
    while (!q.empty()) {
        cout << q.front() << " ";
        q.pop();
    }
    cout << endl;
    return 0;
}
