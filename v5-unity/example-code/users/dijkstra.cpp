#include <bits/stdc++.h>
using namespace std;
int t, n, ans, x;
inline void solve(){ //by wayneoi
    ans = 0;
    multiset<int> se;
    cin >> n;
    for(int i = 1; i <= n; i++){
        cin >> x;
        se.insert(x);
    }
    while(!se.empty()){
        auto k = se.begin();
        int it = *k;
        ans += it;
        se.erase(k);
        if(!se.empty()){
            auto k = prev(se.end());
            se.erase(k);
            if(*k - 2 > 0) se.insert(*k - 2);
        }
    }
    cout << ans << '\n';
}
int main(){
    ios::sync_with_stdio(0);
    cin.tie(0), cout.tie(0);
    cin >> t;
    while(t--) solve();
    return 0;
}