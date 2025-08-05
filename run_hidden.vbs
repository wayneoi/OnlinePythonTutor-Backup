Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd /d 路径 && node cokapi.js", 0
WshShell.Run "cmd /c cd /d 路径 && py bottle_server.py", 0