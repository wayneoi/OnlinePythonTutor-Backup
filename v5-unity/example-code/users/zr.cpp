#include <bits/stdc++.h>
using namespace std;
long long k;
signed main(){

    cin >> k;
    if((long long)(sqrt(k)) * (long long)(sqrt(k)) == k) cout << sqrt(k);
    else if(k % 4) cout << -1;
    else cout << k / 2;
    return 0;
}