# usr/bin/python3.4

import sys
import os
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer

class ServerException(Exception):
    '''服务器内部错误'''
    pass

class base_method():
    # 返回静态文件
    def handle_file(self, handler, full_path):
        try:
            with open(full_path, 'rb') as f:
                b_content = f.read()
            handler.send_content(b_content)
        except IOError as err:
            err = "'{0}' cannot be read: {1}".format(full_path, err)
            handler.handle_error(err)

    # 返回index.html主页的完整路径
    def index_path(self, handler):
        return os.path.join(handler.full_path, 'index.html')

    # method方法判断，要求子类必须实现该接口
    def test(self, handler):
        assert False, 'Not implemented.'

    # method方法执行，要求子类必须实现该接口
    def act(self, handler):
        assert False, 'Not implemented.'

class case_no_file(base_method):
    '''文件或目录不存在'''
    def test(self, handler):
        return not os.path.exists(handler.full_path)

    def act(self, handler):
        raise ServerException("'{0}' not found".format(handler.path))

class case_cgi_file(base_method):
    '''可执行脚本'''
    def run_cgi(self, handler):
        # b_起首表示数据类型为bytes
        b_data = subprocess.check_output(["python", handler.full_path])
        handler.send_content(b_data)

    def test(self, handler):
        return (os.path.isfile(handler.full_path) and
               handler.full_path.endswith('.py'))

    def act(self, handler):
        self.run_cgi(handler)

class case_existing_file(base_method):
    '''文件存在的情况'''
    def test(self, handler):
        return os.path.isfile(handler.full_path)

    def act(self, handler):
        self.handle_file(handler, handler.full_path)

class case_directory_index_file(base_method):
    '''在根路径下返回主页文件'''
    def test(self, handler):
        return (os.path.isdir(handler.full_path) and
               os.path.isfile(self.index_path(handler)))

    def act(self, handler):
        self.handle_file(handler, self.index_path(handler))

class case_always_fail(base_method):
    '''默认处理'''
    def test(self, handler):
        return True

    def act(self, handler):
        raise ServerException("Unknown object '{0}'".format(handler.path))

class RequestHandler(BaseHTTPRequestHandler):
    '''
    请求路径合法则返回相应处理
    否则返回错误页面
    '''
    Cases = [case_no_file(),
             case_cgi_file(),
             case_existing_file(),
             case_directory_index_file(),
             case_always_fail()]

    # 错误页面模板
    Error_Page = """
    <html>
    <body>
    <h1>Error accessing {path}</h1>
    <p>{msg}</p>
    </body>
    </html>
    """

    def do_GET(self):
        try:
            # 得到完整的请求路径
            self.full_path = os.getcwd() + self.path
            # 遍历所有的情况并处理
            for case in self.Cases:
                if case.test(self):
                    case.act(self)
                    break
        # 处理异常
        except Exception as msg:
            self.handle_error(msg)

    def handle_error(self, msg):
        content = self.Error_Page.format(path=self.path, msg=msg)
        b_content = bytes(content, 'utf-8')
        self.send_content(b_content, 404)

    # 发送数据到客户端
    def send_content(self, content, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

if __name__ == '__main__':
    serverAddress = ('', 8088)
    server = HTTPServer(serverAddress, RequestHandler)
    server.serve_forever()
