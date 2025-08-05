/*

Online Python Tutor
https://github.com/pgbovine/OnlinePythonTutor/

Copyright (C) Philip J. Guo (philip@pgbovine.net)

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

*/

// This is a nodejs server based on express that serves the v4-cokapi/ app,
// which implements OPT language backends for languages such as Java,
// Ruby, JavaScript, TypeScript, C, C++, ...

// To test locally, run 'make' and load http://localhost:3000/

// Run with an 'https' command-line flag to use https (must have
// the proper certificate and key files, though)




var assert = require('assert');
var child_process = require('child_process');
var express = require('express');
var util = require('util');


// to use low-numbered ports, Node must be allowed to bind to ports lower than 1024.
// e.g., run: sudo setcap 'cap_net_bind_service=+ep' <node executable>
// defaults:
var PORT = 80;
var useHttps = false;
var local = false;

var args = process.argv.slice(2);
if (args.length > 0) {
  if (args[0] === 'https') {
    PORT = 443;
    useHttps = true;
  } else if (args[0] === 'http3000') {
    PORT = 3000;
  } else if (args[0] === 'https8001') {
    PORT = 8001;
    useHttps = true;
  } else if (args[0] === 'local') {
    PORT = 3000;
    local = true;
    console.log('running in local mode');
  } else {
    assert(false);
  }
}

 
// We use this to execute since it supports utf8 and also an optional
// timeout, but it needs the exact location of binaries because it doesn't
// spawn a shell
// http://nodejs.org/api/child_process.html#child_process_child_process_execfile_file_args_options_callback

var TIMEOUT_SECS = 600;

var MAX_BUFFER_SIZE = 10 * 1024 * 1024 * 2; //20M 允许最大输出内存，超过的话会报错

var MEM_LIMIT = "8192m"; // raise it from 512MB to 1024MB and measure what happens


// bind() res and useJSONP before using
function postExecHandler(res, useJSONP, err, stdout, stderr) {
  var errTrace;
  if (err) {
    console.log('postExecHandler', util.inspect(err, {depth: null}));
    if (err.killed) {
      // timeout!
      errTrace = {code: '', trace: [{'event': 'uncaught_exception',
                                     'exception_msg': 'Error: Your code ran for more than ' + TIMEOUT_SECS + ' seconds.[#BackendError]'}]};
      if (useJSONP) {
        res.jsonp(errTrace /* return an actual object, not a string */);
      } else {
        res.send(JSON.stringify(errTrace));
      }
    } else {
      if (err.code === 42) {
        // special error code for instruction_limit_reached in jslogger.js
        errTrace = {code: '', trace: [{'event': 'uncaught_exception',
                                       'exception_msg': 'Error: stopped after running 1000 steps and cannot display visualization.\nShorten your code, since Python Tutor is not designed to handle long-running code.'}]};
      } else {
        errTrace = {code: '', trace: [{'event': 'uncaught_exception',
                                       'exception_msg': "Docker未启动或后端服务出错,去查看日志[#BackendError]"}]};
                                       // old error message, retired on 2018-03-02
                                       //'exception_msg': "Unknown error. The server may be down or overloaded right now.\nReport a bug to philip@pgbovine.net by clicking on the\n'Generate permanent link' button at the bottom and including a URL in your email."}]};
      }

      if (useJSONP) {
        res.jsonp(errTrace /* return an actual object, not a string */);
      } else {
        res.send(JSON.stringify(errTrace));
      }
    }
  } else {
    if (useJSONP) {
      try {
        // stdout better be real JSON, or we've got a problem!!!
        var stdoutParsed = JSON.parse(stdout);
        res.jsonp(stdoutParsed /* return an actual object, not a string */);
      } catch(e) {
        errTrace = {code: '', trace: [{'event': '未捕获的异常',
                                       'exception_msg': "出故障,等待修复或联系管理员"}]};
                                       // old error message, retired on 2018-03-02
                                       //'exception_msg': "Unknown error. The server may be down or overloaded right now.\nReport a bug to philip@pgbovine.net by clicking on the\n'Generate permanent link' button at the bottom and including a URL in your email."}]};
        res.jsonp(errTrace /* return an actual object, not a string */);
      }
    } else {
      res.send(stdout);
    }
  }
}


var app = express();

 


// 添加 API 路由
const path = require('path');
const fs = require('fs');
app.get('/api/user-cpp-files', (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*'); // 允许所有来源跨域
  const dir = path.join(__dirname, '../v5-unity/example-code/users');
  fs.readdir(dir, (err, files) => {
    if (err) {
      res.json([]);
      return;
    }
    const cppFiles = files.filter(f => f.endsWith('.cpp'));
    res.json(cppFiles);
  });
});

app.get('/api/user-cpp-file', (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  const filename = req.query.name;
  if (!filename || !filename.endsWith('.cpp')) {
    res.status(400).send('Invalid filename');
    return;
  }
  const dir = path.join(__dirname, '../v5-unity/example-code/users');
  const filePath = path.join(dir, filename);
  // 防止路径穿越
  if (!filePath.startsWith(dir)) {
    res.status(403).send('Forbidden');
    return;
  }
  fs.readFile(filePath, 'utf8', (err, data) => {
    if (err) {
      res.status(404).send('Not found');
      return;
    }
    res.type('text/plain').send(data);
  });
});

// 处理 /api/save-user-cpp-file 的 CORS 预检请求
app.options('/api/save-user-cpp-file', (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.sendStatus(204);
});

// 保存用户 C++ 文件的 API
app.post('/api/save-user-cpp-file', (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') {
    res.sendStatus(204);
    return;
  }
  let body = '';
  req.on('data', chunk => { body += chunk; });
  req.on('end', () => {
    try {
      const { fileName, code } = JSON.parse(body);
      if (!fileName || !fileName.endsWith('.cpp')) {
        res.status(400).send('Invalid filename');
        return;
      }
      const dir = path.join(__dirname, '../v5-unity/example-code/users');
      if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
      const filePath = path.join(dir, fileName);
      // 防止路径穿越
      if (!filePath.startsWith(dir)) {
        res.status(403).send('Forbidden');
        return;
      }
      fs.writeFile(filePath, code, 'utf8', err => {
        if (err) {
          res.status(500).send('Write failed');
        } else {
          res.send('OK');
        }
      });
    } catch (e) {
      res.status(400).send('Bad request');
    }
  });
});

// http://ilee.co.uk/jsonp-in-express-nodejs/
app.set("jsonp callback", true);

app.get('/exec_js', exec_js_handler.bind(null, false, false));
app.get('/exec_js_jsonp', exec_js_handler.bind(null, true, false));

app.get('/exec_ts', exec_js_handler.bind(null, false, true));
app.get('/exec_ts_jsonp', exec_js_handler.bind(null, true, true));

function exec_js_handler(useJSONP /* use bind first */, isTypescript /* use bind first */, req, res) {
  var usrCod = req.query.user_script;

  var exeFile;
  if (process.platform === 'win32') {
    exeFile = 'docker'; // Windows 下直接用 docker
  } else {
    exeFile = '/usr/bin/docker'; // 类 Unix 系统
  }
  var args = [];

  // must match the docker setup in backends/javascript/Dockerfile
  args.push('run', '-m', MEM_LIMIT, '--rm', '--user=netuser', '--net=none', '--cap-drop', 'all', 'pgbovine/cokapi-js:v1',
            '/tmp/javascript/node-v6.0.0-linux-x64/bin/node', // custom Node.js version
            '--expose-debug-as=Debug',
            '/tmp/javascript/jslogger.js');

  if (isTypescript) {
    args.push('--typescript=true');
  }
  args.push('--jsondump=true');
  args.push('--code=' + usrCod);

  // 打印完整命令，便于调试
  console.log('[exec]', exeFile, args.map(a => JSON.stringify(a)).join(' '));
  child_process.execFile(exeFile, args,
                         {timeout: TIMEOUT_SECS * 1000 /* milliseconds */,
                          maxBuffer: MAX_BUFFER_SIZE,
                          // make SURE docker gets the kill signal;
                          // this signal seems to allow docker to clean
                          // up after itself to --rm the container, but
                          // double-check with 'docker ps -a'
                          killSignal: 'SIGINT'},
                         postExecHandler.bind(null, res, useJSONP));
}

app.get('/exec_pyanaconda', exec_pyanaconda_handler.bind(null, false));
app.get('/exec_pyanaconda_jsonp', exec_pyanaconda_handler.bind(null, true));

function exec_pyanaconda_handler(useJSONP /* use bind first */, req, res) {
  var usrCod = req.query.user_script;
  var parsedOptions = {};
  if (req.query.options_json) {
    parsedOptions = JSON.parse(req.query.options_json);
  }

  var exeFile;
  if (process.platform === 'win32') {
    exeFile = 'docker'; // Windows 下直接用 docker
  } else {
    exeFile = '/usr/bin/docker'; // 类 Unix 系统
  }
  var args = [];

  // must match the docker setup in backends/javascript/Dockerfile
  args.push('run', '-m', MEM_LIMIT, '--rm', '--user=netuser', '--net=none', '--cap-drop', 'all', 'pgbovine/cokapi-python-anaconda:v1',
            'python',
            '/tmp/python/generate_json_trace.py',
            '--allmodules', // freely allow importing of all modules
            '--code=' + usrCod);

  if (parsedOptions.heap_primitives) {
    args.push('--heapPrimitives');
  }
  if (parsedOptions.cumulative_mode) {
    args.push('--cumulative');
  }
  if (req.query.raw_input_json) {
    args.push('--input=' + req.query.raw_input_json);
  }

  // 打印完整命令，便于调试
  console.log('[exec]', exeFile, args.map(a => JSON.stringify(a)).join(' '));
  child_process.execFile(exeFile, args,
                         {timeout: TIMEOUT_SECS * 1000 /* milliseconds */,
                          maxBuffer: MAX_BUFFER_SIZE,
                          // make SURE docker gets the kill signal;
                          // this signal seems to allow docker to clean
                          // up after itself to --rm the container, but
                          // double-check with 'docker ps -a'
                          killSignal: 'SIGINT'},
                         postExecHandler.bind(null, res, useJSONP));
}

// for running *natively* on localhost my Mac (must customize for Linux):
if (local) {
  app.get('/exec_js_native', function(req, res) {
    res.setHeader('Access-Control-Allow-Origin', '*'); // enable CORS

    var usrCod = req.query.user_script;

    var exeFile = 'backends/javascript/node-v6.0.0-darwin-x64/bin/node';
    var args = [];
    args.push('--expose-debug-as=Debug',
              'backends/javascript/jslogger.js',
              '--jsondump=true',
              '--code=' + usrCod);

    // 打印完整命令，便于调试
    console.log('[exec]', exeFile, args.map(a => JSON.stringify(a)).join(' '));
    child_process.execFile(exeFile, args,
                           {timeout: TIMEOUT_SECS * 1000 /* milliseconds */,
                            maxBuffer: MAX_BUFFER_SIZE,
                            // make SURE docker gets the kill signal;
                            // this signal seems to allow docker to clean
                            // up after itself to --rm the container, but
                            // double-check with 'docker ps -a'
                            killSignal: 'SIGINT'},
                           postExecHandler.bind(null, res, false));
  });
}


app.get('/exec_java', exec_java_handler.bind(null, false));
app.get('/exec_java_jsonp', exec_java_handler.bind(null, true));

// runs David Pritchard's Java backend in backends/java/
function exec_java_handler(useJSONP /* use bind first */, req, res) {
  var usrCod = req.query.user_script;

  var parsedOptions = JSON.parse(req.query.options_json);
  var heapPrimitives = parsedOptions.heap_primitives;

  var exeFile;
  if (process.platform === 'win32') {
    exeFile = 'docker'; // Windows 下直接用 docker
  } else {
    exeFile = '/usr/bin/docker'; // 类 Unix 系统
  }
  var args = [];

  var inputObj = {};
  inputObj.usercode = usrCod;
  // TODO: add options, arg, and stdin later ...
  inputObj.options = {};
  inputObj.args = [];
  inputObj.stdin = "";

  // VERY unintuitive -- to get strings to display as heap objects and
  // NOT 'primitive' values in the Java backend, set showStringsAsValues
  // to false
  if (heapPrimitives) {
    inputObj.options.showStringsAsValues = false;
  }

  var inputObjJSON = JSON.stringify(inputObj);

  // must match the docker setup in backends/java/Dockerfile
  args.push('run', '-m', MEM_LIMIT, '--rm', '--user=netuser', '--net=none', '--cap-drop', 'all', 'pgbovine/cokapi-java:v1',
            '/tmp/run-java-backend.sh',
            inputObjJSON);

  // 打印完整命令，便于调试
  console.log('[exec]', exeFile, args.map(a => JSON.stringify(a)).join(' '));
  child_process.execFile(exeFile, args,
                         {timeout: TIMEOUT_SECS * 1000 /* milliseconds */,
                          maxBuffer: MAX_BUFFER_SIZE,
                          // make SURE docker gets the kill signal;
                          // this signal seems to allow docker to clean
                          // up after itself to --rm the container, but
                          // double-check with 'docker ps -a'
                          killSignal: 'SIGINT'},
                         postExecHandler.bind(null, res, useJSONP));
}


app.get('/exec_ruby', exec_ruby_handler.bind(null, false));
app.get('/exec_ruby_jsonp', exec_ruby_handler.bind(null, true));

function exec_ruby_handler(useJSONP /* use bind first */, req, res) {
  var usrCod = req.query.user_script;

  var exeFile;
  if (process.platform === 'win32') {
    exeFile = 'docker'; // Windows 下直接用 docker
  } else {
    exeFile = '/usr/bin/docker'; // 类 Unix 系统
  }
  var args = [];

  // must match the docker setup in backends/ruby/Dockerfile
  args.push('run', '-m', MEM_LIMIT, '--rm', '--user=netuser', '--net=none', '--cap-drop', 'all', 'pgbovine/cokapi-ruby:v1',
            '/tmp/ruby/ruby',
            '/tmp/ruby/pg_logger.rb',
            '-c',
            usrCod);

  // 打印完整命令，便于调试
  console.log('[exec]', exeFile, args.map(a => JSON.stringify(a)).join(' '));
  child_process.execFile(exeFile, args,
                         {timeout: TIMEOUT_SECS * 1000 /* milliseconds */,
                          maxBuffer: MAX_BUFFER_SIZE,
                          // make SURE docker gets the kill signal;
                          // this signal seems to allow docker to clean
                          // up after itself to --rm the container, but
                          // double-check with 'docker ps -a'
                          killSignal: 'SIGINT'},
                         postExecHandler.bind(null, res, useJSONP));
}


app.get('/exec_c', exec_cpp_handler.bind(null, false, false));
app.get('/exec_c_jsonp', exec_cpp_handler.bind(null, false, true));
app.get('/exec_cpp', exec_cpp_handler.bind(null, true, false));
app.get('/exec_cpp_jsonp', exec_cpp_handler.bind(null, true, true));

function exec_cpp_handler(useCPP /* use bind first */, useJSONP /* use bind first */, req, res) {
  var usrCod = req.query.user_script;
  var stdinContent = req.query.stdin || ''; // 获取标准输入内容
  
  // 处理用户代码和标准输入中的换行符，确保正确传递给 Python 后端
  usrCod = usrCod.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
  stdinContent = stdinContent.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
  
  var exeFile;
  if (process.platform === 'win32') {
    exeFile = 'docker';
  } else {
    exeFile = '/usr/bin/docker';
  }
  var args = [];

  // must match the docker setup in backends/c_cpp/Dockerfile
  // args.push('run', '-m', MEM_LIMIT, '--rm', '--user=netuser', '--net=none', '--cap-drop', 'all', 'pgbovine/opt-cpp-backend:v1',
  //           'python',
  //           '/tmp/opt-cpp-backend/run_cpp_backend.py',
  //           usrCod,
  //           useCPP ? 'cpp' : 'c',
  //           '--stdin=' + stdinContent); // 添加标准输入参数

    // 使用 exec 进入已存在的容器
  args.push('exec', 'charming_hopper',
            'python',
            '/tmp/opt-cpp-backend/run_cpp_backend.py',
            usrCod,
            useCPP ? 'cpp' : 'c',
            '--stdin=' + stdinContent); // 添加标准输入参数


  // 打印调试信息
  console.log('\n[Docker 命令开始执行] ' + '-'.repeat(50));
  console.log('执行文件:', exeFile);
  console.log('用户代码:\n```cpp\n' + usrCod + '\n```');
  console.log('标准输入:\n```\n' + stdinContent + '\n```');
  console.log('命令参数:', util.inspect(args, {colors: true, depth: null}));
  console.log('[拼接后的完整命令]:\n', exeFile, args.join(' '));
  console.log('-'.repeat(70));

  child_process.execFile(exeFile, args,
                       {timeout: TIMEOUT_SECS * 1000,
                        maxBuffer: MAX_BUFFER_SIZE,
                        killSignal: 'SIGINT'},
                       function(err, stdout, stderr) {
    // 执行完成后的调试信息
    console.log('\n[Docker 命令执行完成] ' + '-'.repeat(50));
    if (err) {
      console.log('[错误信息]:', util.inspect(err, {colors: true, depth: null}));
    }
    if (stderr) {
      console.log('[标准错误]:', stderr);
    }
    if (stdout) {
      try {
        // 完整显示对象和数组内容
        console.log('[输出完整对象和数组内容]:', util.inspect(JSON.parse(stdout), {depth: null, colors: true}));
      } catch(e) {
        console.log('[原始输出]:', stdout);
      }
    }
    console.log('-'.repeat(70), '\n');
    
    // 调用原有的处理函数
    postExecHandler(res, useJSONP, err, stdout, stderr);
  });
}

// test
app.get('/test_failure_jsonp', function(req, res) {
   errTrace = {code: '', trace: [{'event': '未捕获的异常',
                                       'exception_msg': "出故障,等待修复或联系管理员"}]};
   res.jsonp(errTrace /* return an actual object, not a string */);
});


// https support
var https = require('https');

if (useHttps) {
  // added letsencrypt support on 2017-06-28 -- MAKE SURE we have read permissions
  var options = {
    key: fs.readFileSync('/etc/letsencrypt/live/cokapi.com/privkey.pem'),
    cert: fs.readFileSync('/etc/letsencrypt/live/cokapi.com/cert.pem'),
    ca: fs.readFileSync('/etc/letsencrypt/live/cokapi.com/chain.pem')
  };

  var server = https.createServer(options, app).listen(
    PORT,
    function() {
      var host = server.address().address;
      var port = server.address().port;
      console.log('https app listening at https://%s:%s', host, port);
  });
} else {
 
  var server = app.listen(
    PORT,
    function() {
      var host = server.address().address;
      var port = server.address().port;
      console.log('http app listening at http://%s:%s', host, port);
  });
}

