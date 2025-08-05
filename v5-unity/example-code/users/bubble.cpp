#include <iostream>
#include <vector>

void bubbleSort(std::vector<int>& arr) {
    int n = arr.size();
    for (int i = 0; i < n-1; i++) {
        // 每次遍历将最大的元素冒泡到最后
        bool swapped = false;
        for (int j = 0; j < n-i-1; j++) {
            if (arr[j] > arr[j+1]) {
                std::swap(arr[j], arr[j+1]);
                swapped = true;
            }
        }
        // 如果没有发生交换，说明已经有序
        if (!swapped) break;
    }
}

int main() {
    std::vector<int> arr = {64, 34, 25, 12, 22, 11, 90};
    
    std::cout << "排序前: ";
    for (int num : arr) std::cout << num << " ";
    std::cout << std::endl;
    
    bubbleSort(arr);
    
    std::cout << "冒泡排序后: ";
    for (int num : arr) std::cout << num << " ";
    std::cout << std::endl;
    
    return 0;
}