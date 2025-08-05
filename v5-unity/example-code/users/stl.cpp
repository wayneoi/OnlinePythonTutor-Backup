#include <iostream>
#include <vector>
#include <list>
#include <deque>
#include <stack>
#include <queue>
#include <set>
#include <map>
#include <unordered_set>
#include <unordered_map>
#include <algorithm>
#include <string>

using namespace std;

// 打印容器内容的辅助函数
template <typename T>
void printContainer(const T& container, const string& name) {
    cout << name << ": ";
    for (const auto& item : container) {
        cout << item << " ";
    }
    cout << endl;
}

// 打印map容器的辅助函数
template <typename K, typename V>
void printMap(const map<K, V>& container, const string& name) {
    cout << name << ": ";
    for (const auto& pair : container) {
        cout << "{" << pair.first << ":" << pair.second << "} ";
    }
    cout << endl;
}

int main() {
    // 1. vector - 动态数组
    vector<int> vec = {1, 2, 3, 4, 5};
    vec.push_back(6);
    vec.insert(vec.begin() + 2, 10);
    printContainer(vec, "Vector");

    // 2. list - 双向链表
    list<string> lst = {"apple", "banana", "cherry"};
    lst.push_front("orange");
    lst.push_back("grape");
    lst.insert(next(lst.begin(), 2), "kiwi");
    printContainer(lst, "List");

    // 3. deque - 双端队列
    deque<double> dq = {1.1, 2.2, 3.3};
    dq.push_front(0.0);
    dq.push_back(4.4);
    printContainer(dq, "Deque");

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

    // 7. set - 有序不重复集合
    set<int> s = {5, 3, 1, 4, 2};
    s.insert(3); // 不会插入重复值
    s.insert(6);
    printContainer(s, "Set");

    // 8. multiset - 有序可重复集合
    multiset<int> ms = {1, 2, 2, 3, 3, 3};
    ms.insert(2);
    printContainer(ms, "Multiset");

    // 9. map - 有序键值对 (键唯一)
    map<string, int> m = {{"Alice", 25}, {"Bob", 30}};
    m["Charlie"] = 35;
    m.insert({"Dave", 40});
    printMap(m, "Map");

    // 10. multimap - 有序键值对 (键可重复)
    multimap<string, int> mm = {{"Apple", 5}, {"Banana", 3}, {"Apple", 7}};
    mm.insert({"Banana", 2});
    cout << "Multimap: ";
    for (const auto& pair : mm) {
        cout << "{" << pair.first << ":" << pair.second << "} ";
    }
    cout << endl;

    // 11. unordered_set - 哈希集合
    unordered_set<string> us = {"red", "green", "blue"};
    us.insert("yellow");
    printContainer(us, "Unordered Set");

    // 12. unordered_map - 哈希映射
    unordered_map<string, double> um = {{"pi", 3.14159}, {"e", 2.71828}};
    um["sqrt2"] = 1.41421;
    cout << "Unordered Map: ";
    for (const auto& pair : um) {
        cout << "{" << pair.first << ":" << pair.second << "} ";
    }
    cout << endl;

    // 13. STL算法示例
    vector<int> nums = {3, 1, 4, 1, 5, 9, 2, 6};
    
    // 排序
    sort(nums.begin(), nums.end());
    printContainer(nums, "Sorted vector");
    
    // 查找
    auto it = find(nums.begin(), nums.end(), 5);
    if (it != nums.end()) {
        cout << "Found 5 at position: " << distance(nums.begin(), it) << endl;
    }
    
    // 计数
    int ones = count(nums.begin(), nums.end(), 1);
    cout << "Number of 1s: " << ones << endl;
    
    // 反转
    reverse(nums.begin(), nums.end());
    printContainer(nums, "Reversed vector");

    return 0;
}