# -*- coding: utf-8 -*-
# Convert a raw trace created by the Valgrind OPT C backend to a format
# that the OPT frontend can digest, making various optimizations and
# clean-ups along the way to beautify the trace

# Created 2015-10-04 by Philip Guo

# 用法说明：
# 传入一个以 .c 或 .cpp 结尾的源文件全路径，假定 Valgrind 生成的 trace 文件为 $basename.vgtrace
# 可选参数 --end-of-trace-error-msg 用于在 trace 结尾显示自定义错误信息

# 依赖于 gcc 版本和编译参数，trace 结构可能有差异
# 推荐编译参数：gcc -ggdb -O0 -fno-omit-frame-pointer
#
# 适用平台示例：
'''
$ gcc -v
Using built-in specs.
COLLECT_GCC=gcc
COLLECT_LTO_WRAPPER=/usr/lib/gcc/x86_64-linux-gnu/4.8/lto-wrapper
Target: x86_64-linux-gnu
Configured with: ../src/configure -v --with-pkgversion='Ubuntu 4.8.4-2ubuntu1~14.04' --with-bugurl=file:///usr/share/doc/gcc-4.8/README.Bugs --enable-languages=c,c++,java,go,d,fortran,objc,obj-c++ --prefix=/usr --program-suffix=-4.8 --enable-shared --enable-linker-build-id --libexecdir=/usr/lib --without-included-gettext --enable-threads=posix --with-gxx-include-dir=/usr/include/c++/4.8 --libdir=/usr/lib --enable-nls --with-sysroot=/ --enable-clocale=gnu --enable-libstdcxx-debug --enable-libstdcxx-time=yes --enable-gnu-unique-object --disable-libmudflap --enable-plugin --with-system-zlib --disable-browser-plugin --enable-java-awt=gtk --enable-gtk-cairo --with-java-home=/usr/lib/jvm/java-1.5.0-gcj-4.8-amd64/jre --enable-java-home --with-jvm-root-dir=/usr/lib/jvm/java-1.5.0-gcj-4.8-amd64 --with-jvm-jar-dir=/usr/lib/jvm-exports/java-1.5.0-gcj-4.8-amd64 --with-arch-directory=amd64 --with-ecj-jar=/usr/share/java/eclipse-ecj.jar --enable-objc-gc --enable-multiarch --disable-werror --with-arch-32=i686 --with-abi=m64 --with-multilib-list=m32,m64,mx32 --with-tune=generic --enable-checking=release --build=x86_64-linux-gnu --host=x86_64-linux-gnu --target=x86_64-linux-gnu
Thread model: posix
gcc version 4.8.4 (Ubuntu 4.8.4-2ubuntu1~14.04)
'''

import json
import os
import pprint
import sys
from optparse import OptionParser

pp = pprint.PrettyPrinter(indent=2)  # 用于调试时美观打印对象

RECORD_SEP = '=== pg_trace_inst ==='  # trace 文件中每条记录的分隔符

MAX_STEPS = 2000  # trace 步数上限，防止死循环
ONLY_ONE_REC_PER_LINE = True  # 是否只保留每行的第一个 step_line 事件

all_execution_points = []  # 存储所有解析出的 trace 步骤

# 处理一条 trace 记录，返回 False 表示遇到异常或解析失败
# lines: 单条记录的所有原始文本行
# 主要负责分类、解析、调用 process_json_obj 生成标准化 trace 步骤
# 并追加到 all_execution_points
# 如果遇到异常事件，立即终止后续解析
# 返回 True/False 表示是否继续解析后续记录

def process_record(lines):
    if not lines:
        return True # 空记录直接跳过，保持解析流程

    err_lines = []      # 错误信息行
    stdout_lines = []   # 标准输出行
    regular_lines = []  # 其它普通内容
    for e in lines:
        if e.startswith('ERROR: '): # 错误信息行
            err_lines.append(e)
        elif e.startswith('STDOUT: '): # 标准输出行
            stdout_lines.append(e)
        elif e.startswith('MAX_STEPS_EXCEEDED'): # 超步数提示，忽略
            pass # 超步数提示，忽略
        else:
            regular_lines.append(e) # 其它普通内容行

    rec = '\n'.join(regular_lines) # 只保留普通内容行
    try:
        # 处理特殊浮点值，防止 json 解析失败
        rec = rec.replace('"val":******', '"val":null') 
        obj = json.loads(rec)
    except ValueError:
        print >> sys.stderr, "错误的记录,无法解析", rec # 解析失败
        return False

    assert len(stdout_lines) == 1 # 每条记录应有一行 STDOUT
    stdout_str = json.loads(stdout_lines[0][len('STDOUT: '):])

    err_str = err_lines[0] if err_lines else None  # 只取第一条错误

    x = process_json_obj(obj, err_str, stdout_str) # 生成标准化 trace 步骤
    all_execution_points.append(x) 
    # 如果遇到异常事件，立即终止后续解析
    if x['event'] == 'exception': 
        return False
    return True

# 解析单条 json 记录，生成标准化 trace 步骤
# obj: 解析后的 json 对象
# err_str: 错误信息
# stdout_str: 标准输出
# 返回 dict，包含 heap/stack/globals/line/func_name/event/stdout 等

def process_json_obj(obj, err_str, stdout_str):
    #assert len(obj['stack']) > 0 # C 程序至少有 main
    obj['stack'].reverse() # 让栈按从高到低顺序排列
    top_stack_entry = obj['stack'][-1] # 栈顶函数

    # 构造 trace 步骤对象
    ret = {} 

    heap = {} # 用于存储堆对象，避免重复
    stack = [] # 用于存储栈帧信息
    # 记录当前栈帧的局部变量
    # 以及当前栈帧的函数名、行号等信息
    enc_globals = {} 
    ret['heap'] = heap 
    ret['stack_to_render'] = stack 
    ret['globals'] = enc_globals 

    # 记录全局变量顺序
    if 'ordered_globals' in obj: 
        ret['ordered_globals'] = obj['ordered_globals']
    else:
        ret['ordered_globals'] = []

    ret['line'] = obj['line'] # 当前行号
    ret['func_name'] = top_stack_entry['func_name'] # 当前栈顶函数名

    # 标记事件类型
    if err_str:
        ret['event'] = 'exception' 
        ret['exception_msg'] = err_str + '\n(Stopped running after the first error. Please fix your code.)'
    else:
        ret['event'] = 'step_line'

    ret['stdout'] = stdout_str

    # 处理全局变量
    if 'globals' in obj:
        for g_var, g_val in obj['globals'].iteritems(): 
            enc_globals[g_var] = encode_value(g_val, heap)  

    # 处理栈帧
    for e in obj['stack']:
        stack_obj = {}
        stack.append(stack_obj)

        stack_obj['func_name'] = e['func_name'] 
        stack_obj['ordered_varnames'] = e['ordered_varnames']   
        stack_obj['is_highlighted'] = e is top_stack_entry
        stack_obj['frame_id'] = e['FP']
        stack_obj['unique_hash'] = stack_obj['func_name'] + '_' + stack_obj['frame_id']
        if 'line' in e:
            stack_obj['line'] = e['line']
        stack_obj['is_parent'] = False
        stack_obj['is_zombie'] = False
        stack_obj['parent_frame_id_list'] = []
        enc_locals = {}
        stack_obj['encoded_locals'] = enc_locals
        for local_var, local_val in e['locals'].iteritems():
            enc_locals[local_var] = encode_value(local_val, heap)

    # 指令级trace输出
    if 'inst_info' in obj:
        ret['inst_info'] = obj['inst_info']

    return ret

# 类型推断辅助函数，返回 {'target_type': ..., 'bytes': ...}
# 用于生成每个变量/对象的类型描述和字节数

def infer_type_hint(obj):
    target_type = obj.get('type', '') 
    size = 0
    if obj.get('kind') == 'pointer' and not obj.get('type'):
        print >> sys.stderr, 'Pointer type missing:', obj
    # 指针类型特殊处理
    if obj.get('kind') == 'pointer':
        base_type = ''
        if 'type' in obj and obj['type']:
            t = obj['type'].strip()
            if t.endswith('*'):
                base_type = t[:-1].strip()
            else:
                base_type = t
        elif 'deref_val' in obj and isinstance(obj['deref_val'], dict):
            base_type = infer_type_hint(obj['deref_val']).get('target_type', '')
        if base_type:
            target_type =  base_type
        else:
            target_type = 'unknown'
        size = 8
    elif obj.get('kind') == 'base':
        if 'char' in target_type:
            size = 1
        elif 'int' in target_type:
            size = 4
        elif 'long' in target_type:
            size = 8
        elif 'float' in target_type:
            size = 4
        elif 'double' in target_type:
            size = 8
        elif 'pointer' in target_type or '*' in target_type:
            size = 8
    elif obj.get('kind') == 'array':
        element_size = 1
        if obj.get('type'):
            if 'char' in obj['type']:
                element_size = 1
            elif 'int' in obj['type']:
                element_size = 4
            elif 'long' in obj['type']:
                element_size = 8
            elif 'float' in obj['type']:
                element_size = 4
            elif 'double' in obj['type']:
                element_size = 8
        total_elements = len(obj.get('val', []))
        size = element_size * total_elements
    elif obj.get('kind') == 'struct':
        for member in obj.get('val', {}).values():
            if isinstance(member, dict):
                size += infer_type_hint(member).get('bytes', 0)
    return {
        'target_type': target_type, 
        'bytes': size
    }

# 编码单个变量/对象，递归处理嵌套结构，生成可序列化的trace格式
# heap: 用于存储堆对象，避免重复

def encode_value(obj, heap):
    # 提取block_info元数据（如类型、数组信息、虚表等）
    def extract_blockinfo(obj):
        blockinfo = obj.get('block_info')
        if not blockinfo:
            return None
        out = {}
        if 'type' in blockinfo and blockinfo['type']:
            out['type_info'] = blockinfo['type']                                    
        if 'array' in blockinfo and blockinfo['array']:
            out['array_info'] = blockinfo['array']
        if 'has_vtable' in blockinfo:
            out['has_vtable'] = blockinfo['has_vtable']
        return out if out else None

    if obj['kind'] == 'base':
        val = ['C_DATA', obj['addr'], obj['type'], obj['val']]
        blockinfo = extract_blockinfo(obj)
        meta = {}
        if blockinfo:
            meta['__blockinfo__'] = blockinfo
        type_info = infer_type_hint(obj)
        # 只有 pointer 类型才加 target_type
        if type_info and ('pointer' in obj['type'] or '*' in obj['type']):
            meta['target_type'] = type_info['target_type']
        if type_info:
            meta['bytes'] = type_info['bytes']
        if meta:
            val.append(meta) # 尾部元数据，便于前端显示类型/字节数
        return val

    elif obj['kind'] == 'pointer':
        if 'deref_val' in obj:
            encode_value(obj['deref_val'], heap) # 递归处理指针指向的对象
        val = ['C_DATA', obj['addr'], 'pointer', obj['val']]
        blockinfo = extract_blockinfo(obj)
        meta = {}
        if blockinfo:
            meta['__blockinfo__'] = blockinfo
        type_info = infer_type_hint(obj)
        if type_info:
            meta['target_type'] = type_info['target_type']
            meta['bytes'] = type_info['bytes']
        if meta:
            val.append(meta)
        return val

    elif obj['kind'] == 'struct':
        ret = ['C_STRUCT', obj['addr'], obj['type']]
        members = obj['val'].items()
        members.sort(key=lambda e: e[1]['addr'])
        for k, v in members:
            entry = [k, encode_value(v, heap)]
            ret.append(entry)
        blockinfo = extract_blockinfo(obj)
        meta = {}
        if blockinfo:
            meta['__blockinfo__'] = blockinfo
        type_info = infer_type_hint(obj)
        if type_info:
            meta['target_type'] = type_info['target_type']
            meta['bytes'] = type_info['bytes']
        if meta:
            val.append(meta)
        return ret

    elif obj['kind'] == 'array':
        # remote.json风格：C_ARRAY的第三个元素是数组元信息（如元素字节数、heap_block等），后面才是元素
        # 判断是否是堆分配的block（heap_block），如果是则加元信息，否则不加
        is_heap_block = obj.get('heap_block', False)
        element_size = 1
        if obj.get('type'):
            if 'char' in obj['type']:
                element_size = 1
            elif 'int' in obj['type']:
                element_size = 4
            elif 'long' in obj['type']:
                element_size = 8
            elif 'float' in obj['type']:
                element_size = 4
            elif 'double' in obj['type']:
                element_size = 8
        # remote.json风格：堆block加元信息
        if is_heap_block:
            meta = {
                'elt_bytes': element_size,
                'heap_block': True
            }
            # 兼容oob_addr
            if 'oob_addr' in obj:
                meta['oob_addr'] = obj['oob_addr']
            ret = ['C_ARRAY', obj['addr'], meta]
            for e in obj['val']:
                ret.append(encode_value(e, heap))
            return ret
        else:
            # 普通数组不加target_type元数据
            ret = ['C_ARRAY', obj['addr']]
            for e in obj['val']:
                ret.append(encode_value(e, heap))
            return ret

    elif obj['kind'] == 'typedef':
        obj['val']['type'] = obj['type']
        return encode_value(obj['val'], heap)

    elif obj['kind'] == 'heap_block':
        assert obj['addr'] not in heap
        new_elt = ['C_ARRAY', obj['addr']]
        for e in obj['val']:
            new_elt.append(encode_value(e, heap))
        blockinfo = extract_blockinfo(obj)
        meta = {}
        if blockinfo:
            meta['__blockinfo__'] = blockinfo
        type_info = infer_type_hint(obj)
        # 只有 pointer 类型才加 target_type
        if type_info and type_info['target_type'].startswith('pointer'):
            meta['target_type'] = type_info['target_type']
            meta['bytes'] = type_info['bytes']
        elif type_info:
            meta['bytes'] = type_info['bytes']
        if meta:
            new_elt.append(meta)
        # heap对象只存一份，避免重复
        heap[obj['addr']] = new_elt
    else:
        assert False

# ================= 主程序入口 =================
if __name__ == '__main__':
    parser = OptionParser(usage="Create an OPT trace from a Valgrind trace")
    parser.add_option("--create_jsvar", dest="js_varname", default=None,
                      help="Create a JavaScript variable out of the trace")
    parser.add_option("--jsondump", dest="jsondump", action="store_true", default=False,
                      help="Dump compact JSON as output")
    parser.add_option("--prettydump", dest="prettydump", action="store_true", default=False,
                      help="Dump pretty-printed JSON as output")
    parser.add_option("--end-of-trace-error-msg", dest="end_of_trace_error_msg", default=None,
                      help="Display this error message at the end of the trace")

    (options, args) = parser.parse_args()

    fn = args[0]
    basename, ext = os.path.splitext(fn)
    assert ext in ('.c', '.cpp')
    cur_record_lines = []

    success = True

    # 逐行读取 .vgtrace 文件，按分隔符切分为多条记录
    for line in open(basename + '.vgtrace'):
        line = line.strip()
        if line == RECORD_SEP:
            success = process_record(cur_record_lines)
            if not success:
                break
            cur_record_lines = []
        else:
            cur_record_lines.append(line)

    # 处理最后一条记录
    if success:
        success = process_record(cur_record_lines)

    # ========== trace 后处理与优化 ========== #
    filtered_execution_points = []

    # 1. 过滤掉无效帧（如 frame_id 为 0x0、重复、???等）
    for pt in all_execution_points:
        frame_ids = [e['frame_id'] for e in pt['stack_to_render']]
        func_names = [e['func_name'] for e in pt['stack_to_render']]
        if '0x0' in frame_ids:
            continue
        if len(set(frame_ids)) < len(frame_ids):
            continue
        if '???' in func_names:
            continue
        filtered_execution_points.append(pt)

    final_execution_points = []
    if filtered_execution_points:
        final_execution_points.append(filtered_execution_points[0])
        # 2. 只保留栈帧变化合理的步骤（同一帧、进栈、退栈）
        for prev, cur in zip(filtered_execution_points, filtered_execution_points[1:]):
            prev_frame_ids = [e['frame_id'] for e in prev['stack_to_render']]
            cur_frame_ids = [e['frame_id'] for e in cur['stack_to_render']]
            if prev_frame_ids == cur_frame_ids:
                final_execution_points.append(cur)
            elif len(prev_frame_ids) < len(cur_frame_ids):
                if prev_frame_ids == cur_frame_ids[:-1]:
                    final_execution_points.append(cur)
            elif len(prev_frame_ids) > len(cur_frame_ids):
                if cur_frame_ids == prev_frame_ids[:-1]:
                    final_execution_points.append(cur)
        assert len(final_execution_points) <= len(filtered_execution_points)

        cur_ind = 1
        # 3. 标记 call/return 事件，并优化参数初始化冗余步骤
        for prev, cur in zip(final_execution_points, final_execution_points[1:]):
            prev_frame_ids = [e['frame_id'] for e in prev['stack_to_render']]
            cur_frame_ids = [e['frame_id'] for e in cur['stack_to_render']]
            if len(prev_frame_ids) < len(cur_frame_ids):
                if prev_frame_ids == cur_frame_ids[:-1]:
                    cur['event'] = 'call'
                # 优化：跳过同一行/同一帧的冗余参数初始化
                lookahead = final_execution_points[cur_ind+1:]
                for future_step in lookahead:
                    future_frame_ids = [e['frame_id'] for e in future_step['stack_to_render']]
                    if cur_frame_ids == future_frame_ids and cur['line'] == future_step['line']:
                        future_step['to_delete'] = True
                    else:
                        break
            elif len(prev_frame_ids) > len(cur_frame_ids):
                if cur_frame_ids == prev_frame_ids[:-1]:
                    prev['event'] = 'return'
            cur_ind += 1
        # 4. 最后一步标记为 return 或 exception
        if success:
            if options.end_of_trace_error_msg:
                final_execution_points[-1]['event'] = 'exception'
                final_execution_points[-1]['exception_msg'] = options.end_of_trace_error_msg
            else:
                final_execution_points[-1]['event'] = 'return'

    # 5. 不要删除一行函数体的 return（防止丢失重要返回）
    for e in final_execution_points:
        if e['event'] == 'return':
            if 'to_delete' in e:
                del e['to_delete']

    # 6. 只保留每行第一个 step_line（已加详细注释）
    if ONLY_ONE_REC_PER_LINE:
        tmp = []
        prev_event = None
        prev_line = None
        prev_frame_ids = None
        for elt in final_execution_points:
            skip = False
            cur_event = elt['event']
            cur_line = elt['line']
            cur_frame_ids = [e['frame_id'] for e in elt['stack_to_render']]
            if prev_frame_ids:
                if cur_event == prev_event == 'step_line':
                    if cur_line == prev_line and cur_frame_ids == prev_frame_ids:
                        skip = True
            if not skip:
                tmp.append(elt)
            prev_event = cur_event
            prev_line = cur_line
            prev_frame_ids = cur_frame_ids
        final_execution_points = tmp

    # 7. 优化：如果 return 后回到调用者同一行，且下一个事件函数名一致，则跳过该步骤
    for prev, cur, next in zip(final_execution_points, final_execution_points[1:], final_execution_points[2:]):
        if prev['event'] == 'return' and len(prev['stack_to_render']) > 1:
            prev_caller = prev['stack_to_render'][-2]
            cur_top = cur['stack_to_render'][-1]
            if (cur_top['frame_id'] == prev_caller['frame_id']) and \
               (cur_top['line'] == prev_caller['line']) and \
               (cur['func_name'] == next['func_name']):
                cur['to_delete'] = True

    # 8. 删除 main 之前的所有步骤（C++全局初始化等）
    for e in final_execution_points:
        if e['func_name'] == 'main':
            break
        else:
            e['to_delete'] = True

    # 9. 打印被删除的步骤（调试用）
    for e in final_execution_points:
        if 'to_delete' in e:
            print >> sys.stderr, 'to_delete:', json.dumps(e)
    final_execution_points = [e for e in final_execution_points if 'to_delete' not in e]

    # 10. 过滤掉最后无用的“空return”步骤（heap、globals、stack_to_render都为空或无变量）
    def is_useless_return_step(e):
        if e.get('event') != 'return':
            return False
        if e.get('heap') and len(e['heap']) > 0:
            return False
        if e.get('globals') and len(e['globals']) > 0:
            return False
        stack = e.get('stack_to_render', [])
        if not stack:
            return True
        for frame in stack:
            if frame.get('encoded_locals') and len(frame['encoded_locals']) > 0:
                return False
            if frame.get('ordered_varnames') and len(frame['ordered_varnames']) > 0:
                return False
        return True
    #final_execution_points = [e for e in final_execution_points if not is_useless_return_step(e)]

    # 10.1 过滤掉无用的 step_line 步骤（main帧，所有变量都为空，stdout 为空）
    # 只保留变量出现前的最后一个 main 空帧，其余 main 空帧全部过滤
    def is_useless_step_line(e, idx, keep_idx):
        if e.get('event') != 'step_line':
            return False
        if e.get('func_name') != 'main':
            return False
        if e.get('heap') and len(e['heap']) > 0:
            return False
        if e.get('globals') and len(e['globals']) > 0:
            return False
        if e.get('stdout'):
            return False
        stack = e.get('stack_to_render', [])
        if len(stack) != 1:
            return False
        frame = stack[0]
        if frame.get('func_name') != 'main':
            return False
        if frame.get('encoded_locals') and len(frame['encoded_locals']) > 0:
            return False
        if frame.get('ordered_varnames') and len(frame['ordered_varnames']) == 0:
            return False
        # 只保留变量出现前的最后一个 main 空帧
        if idx == keep_idx:
            return False
        return True

    # 找到变量出现前的最后一个 main 空帧的索引
    last_empty_main_idx = None
    for idx, e in enumerate(final_execution_points):
        if e.get('event') == 'step_line' and e.get('func_name') == 'main':
            stack = e.get('stack_to_render', [])
            if len(stack) == 1:
                frame = stack[0]
                if frame.get('func_name') == 'main' and \
                   (not frame.get('encoded_locals') or len(frame['encoded_locals']) == 0) and \
                   (not frame.get('ordered_varnames') or len(frame['ordered_varnames']) == 0) and \
                   (not e.get('heap') or len(e['heap']) == 0) and \
                   (not e.get('globals') or len(e['globals']) == 0) and \
                   not e.get('stdout'):
                    last_empty_main_idx = idx
                else:
                    break  # 第一次出现变量就停止
        else:
            break  # 只在 main 空帧区间内查找

    # 保留变量出现前的最后一个 main 空帧，return 帧始终保留
    tmp = []
    for idx, e in enumerate(final_execution_points):
        if e.get('event') == 'return':
            tmp.append(e)
        elif not is_useless_step_line(e, idx, last_empty_main_idx):
            tmp.append(e)
    final_execution_points = tmp

    # 11. 超步数截断
    if len(final_execution_points) > MAX_STEPS:
        final_execution_points = final_execution_points[:MAX_STEPS]
        final_execution_points[-1]['event'] = '超过步数限制'
        final_execution_points[-1]['exception_msg'] = 'Stopped after running ' + str(MAX_STEPS) + ' steps. Please fix your code and try again.'

    # 12. 读取源代码，生成最终 trace 结果
    cod = open(fn).read()
    final_res = {'code': cod, 'trace': final_execution_points}

    # 13. 按需输出为 js 变量、紧凑json或美化json
    if options.js_varname:
        s = json.dumps(final_res, indent=2, sort_keys=True)
        print 'var ' + options.js_varname + ' = ' + s + ';'
    elif options.jsondump:
        print json.dumps(final_res, sort_keys=True)
    elif options.prettydump:
        print json.dumps(final_res, indent=2, sort_keys=True)
    else:
        assert False
