#include <bits/stdc++.h>
using namespace std;
void swap(int* a,int* b){
    int temp = *a;
    *a = *b;
    *b = temp;
}

int partition(int arr[],int low, int high){
    int pivot = arr[high];
    int i = low -1;
    for(int j = low;j<high;j++){
        if(arr[j]<pivot){
            i++;
            swap(&arr[i],&arr[j]);
        }
    }
    swap(&arr[i+1],&arr[high]);
    return i + 1;
}

void quickstart(int arr[],int low, int high){
    
    if(low<high){
        int pi = partition(arr,low,high);
        quickstart(arr,low,pi-1);
        quickstart(arr,pi+1,high);
    }
}


int main(){
    int n;
    int arr1[6];
    int num;
    cin >> n;
    for(int i=0;i<n;i++){
      cin >> arr1[i];
    }
    quickstart(arr1,0,n-1);
    for(int i=0;i<n;i++){
      if(i>0) cout << " ";
      cout << arr1[i];
    }
    return 0;
}