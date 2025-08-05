@echo off
REM 自动杀掉之前的 Node.js 和 Python 相关进程

taskkill /F /IM node.exe >nul 2>nul
taskkill /F /IM python.exe >nul 2>nul
taskkill /F /IM py.exe >nul 2>nul


REM 启动 v4-cokapi 的 Node.js 后端（最小化窗口）
cd /d %~dp0v4-cokapi
start /min "Node Cokapi" cmd /k make local

REM 启动 v5-unity 的 Python bottle_server.py（最小化窗口）
cd /d %~dp0v5-unity
start /min "Python Bottle Server" cmd /k  npm start

cd /d %~dp0

REM 启动 Edge 浏览器访问 C++ 可视化页面
start msedge http://localhost:8003/cpp.html



