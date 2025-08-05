#!/bin/bash    #这是 Linux shell 脚本的标准开头 
# 自动杀掉之前的 Node.js 和 Python 相关进程

pkill -f node >/dev/null 2>&1   #抑制输出
pkill -f python >/dev/null 2>&1
pkill -f py >/dev/null 2>&1

# 启动 v4-cokapi 的 Node.js 后端（在后台运行）
cd "$(dirname "$0")/v4-cokapi"
make local &

# 启动 v5-unity 的 Python bottle_server.py（在后台运行）
cd "$(dirname "$0")/v5-unity"
npm start &

cd "$(dirname "$0")"

# 启动默认浏览器访问 C++ 可视化页面
xdg-open http://localhost:8003/cpp.html


＃本文件运行前需要设置可执行权限 执行设置权限的命令是  chmod +x start_all.sh 
#npm run webpack 监控改动自动编译