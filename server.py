# usr/bin/python3.4
#-*- coding:utf-8 -*-
from http.server import BaseHTTPRequestHandler, HTTPServer
import sys
import os
import subprocess

class case_no_file(object):
    '''该路径不存在'''
    def test(self, handler):
        return not os.path.exists(handler.full_path)
    def act(self, handler):
        raise ServerException("'{0}' not found".format(handler.path))

class case_existing_file(object):
    '''该路径是文件'''
    def test(self, handler):
        return os.path.isfile(handler.full_path)
    def act(self, handler):
        handler.handle_file(handler.full_path)

class case_directory_index_file(object):
    def index_path(self, handler):
        return os.path.join(handler.full_path, 'index.html')

    def test(self, handler):
        return (os.path.isdir(handler.full_path) and
                os.path.isfile(self.index_path(handler)))

    def act(self, handler):
        handler.handle_file(self.index_path(handler))

class case_cgi_file(object):
    def test(self, handler):
        return (os.path.isfile(handler.full_path) and
                handler.full_path.endswith('.py'))

    def act(self, handler):
        handler.run_cgi(handler.full_path)

class case_always_fail(object):
    '''所有情况都不符合时的默认处理类'''
    def test(self, handler):
        return True
    def act(self, handler):
        raise ServerException("Unknown object '{0}'".format(handler.path))

class ServerException(Exception):
    # 服务器内部错误
    pass

class RequestHandler(BaseHTTPRequestHandler):
    '''处理请求并返回页面'''

    # 页面模板
    Error_Page = '''
    <html>
    <body>
    <h1>Error accessing {path}</h1>
    <p>{msg}</p>
    </body>
    </html>
    '''

    Cases = [case_no_file,
             case_cgi_file,
             case_existing_file,
             case_directory_index_file,
             case_always_fail]

    # 处理一个GET请求
    def do_GET(self):
        try:
            self.full_path = os.getcwd() + self.path
            for case in self.Cases:
                handler = case();
                if handler.test(self):
                    handler.act(self)
                    break
        except Exception as e:
            self.handle_error(e)

    def send_content(self, page, status = 200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page)

    def handle_file(self, full_path):
        try:
            with open(full_path, 'rb') as reader:
                content = reader.read()
            self.send_content(content)
        except IOError as e:
            e = "'{0}' cannot be read: {1}".format(self.path, msg)
            self.handle_error(e)

    def handle_error(self, msg):
        content = self.Error_Page.format(path = self.path, msg = msg)
        self.send_content(bytes(content, 'UTF-8'), 404)

    def run_cgi(self, full_path):
        data = subprocess.check_output(["python", full_path])
        self.send_content(data)
#----------------------------------------------------------------------

if __name__ == '__main__':
    serverAddress = ('', 8088)
    server = HTTPServer(serverAddress, RequestHandler)
    server.serve_forever()
