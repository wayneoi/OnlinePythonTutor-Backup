#include <iostream>
#include <queue>
using namespace std;

int main() {
    // 6. priority_queue - 优先队列
    priority_queue<int> pq;
    pq.push(30);
    pq.push(10);
    pq.push(50);
    pq.push(20);
    cout << "Priority Queue (max heap): ";
    while (!pq.empty()) {
        cout << pq.top() << " ";
        pq.pop();
    }
    cout << endl;
    return 0;
}
