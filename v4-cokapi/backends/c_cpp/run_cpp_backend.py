# -*- coding: utf-8 -*-
# 运行基于 Valgrind 的 C/C++ 后端，生成 JSON 输出到 stdout，供 Web 前端使用，包含错误处理等
# Created: 2016-05-09

import json
import os
from subprocess import Popen, PIPE
import re
import sys
import argparse # 添加argparse用于解析命令行参数

VALGRIND_MSG_RE = re.compile('==\d+== (.*)$')
end_of_trace_error_msg = None

# 添加参数解析
parser = argparse.ArgumentParser()
parser.add_argument('program', help='Program source code') # 源代码
parser.add_argument('language', help='Language (c or cpp)') # 语言类型
parser.add_argument('--stdin', help='Standard input content', default='') # 标准输入
parser.add_argument('--prettydump', action='store_true', help='Pretty print the output') # 是否美化输出
args = parser.parse_args()

DN = os.path.dirname(sys.argv[0]) # 获取当前脚本目录
if not DN:
    DN = '.' # 保证有可执行路径
USER_PROGRAM = args.program # 从argparse获取参数
LANG = args.language
STDIN = args.stdin # 保存标准输入内容

prettydump = args.prettydump

# 根据语言类型选择编译器和文件名
if LANG == 'c':
    CC = 'gcc'
    DIALECT = '-std=c11'
    FN = 'usercode.c'
else:
    CC = 'g++'
    DIALECT = '-std=c++11'
    FN = 'usercode.cpp'

F_PATH = os.path.join(DN, FN) # 源文件路径
VGTRACE_PATH = os.path.join(DN, 'usercode.vgtrace') # Valgrind trace 路径
EXE_PATH = os.path.join(DN, 'usercode.exe') # 可执行文件路径

# 删除可能存在的旧文件，避免误用
for f in (F_PATH, VGTRACE_PATH, EXE_PATH):
    if os.path.exists(f):
        os.remove(f)

# 写入用户代码到源文件
with open(F_PATH, 'w') as f:
    f.write(USER_PROGRAM)

# 编译用户代码
p = Popen([CC, DIALECT, '-ggdb', '-O0', '-fno-omit-frame-pointer', '-o', EXE_PATH, F_PATH],
          stdout=PIPE, stderr=PIPE)
(gcc_stdout, gcc_stderr) = p.communicate()
gcc_retcode = p.returncode

if gcc_retcode == 0:
    print >> sys.stderr, '=== gcc stderr ===' # 输出 gcc 的标准错误
    print >> sys.stderr, gcc_stderr
    print >> sys.stderr, '===' # 分隔符

    # 使用 Valgrind 运行可执行文件，收集内存访问信息
    VALGRIND_EXE = os.path.join(DN, 'valgrind-3.11.0/inst/bin/valgrind')
    # --source-filename 只接受文件名，不接受完整路径
    valgrind_p = Popen(['stdbuf', '-o0', # 禁用 stdout 缓冲，保证输出顺序
                        VALGRIND_EXE,
                        '--tool=memcheck',
                        '--source-filename=' + FN,
                        '--trace-filename=' + VGTRACE_PATH,
                        EXE_PATH],
                       stdin=PIPE, stdout=PIPE, stderr=PIPE)
    # 将stdin内容编码为bytes并传入程序
    stdin_bytes = STDIN.encode('utf-8') if STDIN else None
    (valgrind_stdout, valgrind_stderr) = valgrind_p.communicate(input=stdin_bytes)
    valgrind_retcode = valgrind_p.returncode

    print >> sys.stderr, '=== Valgrind stdout ===' # 输出 Valgrind 的标准输出
    print >> sys.stderr, valgrind_stdout
    print >> sys.stderr, '=== Valgrind stderr ===' # 输出 Valgrind 的标准错误
    print >> sys.stderr, valgrind_stderr

    error_lines = []
    in_error_msg = False
    if valgrind_retcode != 0: # Valgrind 运行出错
        for line in valgrind_stderr.splitlines():
            m = VALGRIND_MSG_RE.match(line)
            if m:
                msg = m.group(1).rstrip()
                #print >> sys.stderr, msg
                if 'Process terminating' in msg:
                    in_error_msg = True

                if in_error_msg:
                    if not msg:
                        in_error_msg = False

                if in_error_msg:
                    error_lines.append(msg)

        #print >> sys.stderr, error_lines
        if error_lines:
            end_of_trace_error_msg = '\n'.join(error_lines)

    # 调用 vg_to_opt_trace.py 进行后处理，生成 OPT trace
    # TODO: 其实可以直接 import 进来调用，无需新进程
    POSTPROCESS_EXE = os.path.join(DN, 'vg_to_opt_trace.py')
    args = ['python', POSTPROCESS_EXE]
    if prettydump:
        args.append('--prettydump')
    else:
        args.append('--jsondump')
    if end_of_trace_error_msg:
        args += ['--end-of-trace-error-msg', end_of_trace_error_msg]
    args.append(F_PATH)

    postprocess_p = Popen(args, stdout=PIPE, stderr=PIPE)
    (postprocess_stdout, postprocess_stderr) = postprocess_p.communicate()
    postprocess_retcode = postprocess_p.returncode
    print >> sys.stderr, '=== postprocess stderr ===' # 输出后处理脚本的标准错误
    print >> sys.stderr, postprocess_stderr
    print >> sys.stderr, '===' # 分隔符

    print postprocess_stdout # 输出最终的 trace 结果
else:
    print >> sys.stderr, '=== gcc stderr ===' # 输出 gcc 的标准错误
    print >> sys.stderr, gcc_stderr
    print >> sys.stderr, '===' # 分隔符
    # 编译器报错，解析并友好输出

    exception_msg = 'unknown compiler error' # 默认错误信息
    lineno = None
    column = None

    # 只报告第一个能检测到行号和列号的错误
    for line in gcc_stderr.splitlines():
        # 匹配 'fatal error:' 或 'error:' 等
        m = re.search(FN + ':(\d+):(\d+):.+?(error:.*$)', line)
        if m:
            lineno = int(m.group(1)) # 错误所在行号
            column = int(m.group(2)) # 错误所在列号
            exception_msg = m.group(3).strip() # 错误信息
            break

        # 链接错误通常包含 'undefined '
        # （此处代码较脆弱）
        if 'undefined ' in line:
            parts = line.split(':')
            exception_msg = parts[-1].strip() # 错误信息
            # 匹配类似 /path/usercode.c:2: undefined reference to `xxx'
            if FN in parts[0]:
                try:
                    lineno = int(parts[1]) # 错误行号
                except:
                    pass
            break

    # 输出标准化的异常 JSON，供前端显示
    ret = {'code': USER_PROGRAM,
           'trace': [{'event': 'uncaught_exception',
                    'exception_msg': exception_msg,
                    'line': lineno}]}
    print json.dumps(ret) # 输出异常信息的 JSON

