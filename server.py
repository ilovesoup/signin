from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from io import BytesIO
import json
from matplotlib.font_manager import json_load
import mysql.connector.pooling
from datetime import datetime
import jwt
from threading import Semaphore
import threading
# python3
import urllib.parse as urlparse

from pendulum import date
# python2
# import urlparse


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_auth(self, token, refertag):
        try:
            decodedToken = jwt.decode(token, cfg['app_secret'], algorithms=[
                                      "HS256"], options={"verify_aud": False})
            curDateTime = datetime.utcnow().microsecond * 1000
            if curDateTime > decodedToken['exp']:
                self.auth(refertag)
                return False, None
        except:
            self.auth(refertag)
            return False, None
        return True, decodedToken['data']['email']

    def signin(self, token):
        if not self.do_auth(token, "signin")[0]:
            return
        self.send_response(200)
        self.end_headers()
        self.wfile.write(bytes(camHtml, encoding='utf8'))

    def auth(self, reftag):
        if reftag == None:
            return
        self.send_response(200)
        self.end_headers()
        content = authHtml
        content = content.replace("reftag", reftag)
        self.wfile.write(bytes(content, encoding='utf8'))

    def health(self):
        self.send_response(200)
        self.end_headers()

    def thanks(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(bytes(thanksHtml, encoding='utf8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])

        body = self.rfile.read(content_length)
        jsonData = json.loads(body)

        # res = self.do_auth(jsonData['token'], None)
        # if not res[0]:
        #     return

        self.send_response(302)
        # new_path = '%s%s' % (
        #     'http://localhost:8000/list?token=', jsonData['token'])
        # self.send_header('Location', 'https://7th.pingcap.net/thanks')
        self.send_header('Location', cfg['host']+'/thanks')
        self.end_headers()

        try:
            conn = mydbpool.get_connection()
            cursor = conn.cursor()
            sql = "REPLACE INTO signin (name, signin_date, photo) VALUES (%s, %s, %s)"
            name = jsonData['name']
            dt = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            photoB64 = jsonData['photo']

            val = (name, dt, photoB64)
            cursor.execute(sql, val)
            conn.commit()
            print(name, "done")
        except Exception as e:
            print(e)
        finally:
            cursor.close()
            mydbpool.put_connection(conn)

    def list_gen(self, token):
        if not self.do_auth(token, "list")[0]:
            return

        self.send_response(200)
        self.end_headers()

        try:
            conn = mydbpool.get_connection()
            cursor = conn.cursor(buffered=True)
            cursor.execute("SELECT name, signin_date, photo FROM signin")
            res = cursor.fetchall()
            print("table length :", len(res))
            content = listHtml
            body = ""
            for x in res:
                if x[0] == None or x[1] == None or x[2] == None:
                    continue
                body += "<tr>"
                body += "<td>" + x[0] + "</td>"
                body += "<td>" + x[1].strftime('%Y-%m-%d %H:%M:%S') + "</td>"
                body += "<td>" + "<img style='display:block; width:100px;height:100px;' src='" + \
                    x[2] + "'/> </td>"
                body += "</tr>"
            content = content.replace("tag", body)
            self.wfile.write(bytes(content, encoding='utf8'))
        except Exception as e:
            print(e)
        finally:
            cursor.close()
            mydbpool.put_connection(conn)

    def do_GET(self):
        thread = threading.current_thread()
        print(thread)
        content = ""
        token = ""
        pr = urlparse.urlparse(self.path)
        if pr.query != "":
            query = urlparse.parse_qs(pr.query)
            if "token" in query:
                token = query['token'][0]

        try:
            if pr.path == "/signin":
                self.signin(token)
            elif pr.path == "/login":
                self.auth('signin')
            elif pr.path == "/list":
                self.list_gen(token)
            elif pr.path == "/health":
                self.health()
            elif pr.path == "/thanks":
                self.thanks()
            else:
                content = "Unknown Path"
                self.send_response(404)
                self.end_headers()
                self.wfile.write(bytes(content, encoding='utf8'))
        except Exception as e:
            print(e)
            content = "Something Wrong..."
            self.send_response(404)
            self.end_headers()
            self.wfile.write(bytes(content, encoding='utf8'))


class ThreadingHttpServer (ThreadingMixIn, HTTPServer):
    pass


class ReallyMySQLConnectionPool(mysql.connector.pooling.MySQLConnectionPool):
    def __init__(self, **mysql_config):
        pool_size = mysql_config.get('pool_size', 10)
        self._semaphore = Semaphore(pool_size)
        super().__init__(**mysql_config)

    def get_connection(self):
        self._semaphore.acquire()
        return super().get_connection()

    def put_connection(self, con):
        con.close()  # con是PooledMySQLConnection的实例
        self._semaphore.release()


if __name__ == "__main__":
    try:
        cfgfile = open("config.json", "r")
        cfg = json.load(cfgfile)
        cfgfile.close()
        print(cfg)

        mydbpool = ReallyMySQLConnectionPool(pool_name="signin",
                                             pool_size=32,
                                             pool_reset_session=True,
                                             host=cfg['db'], port=3306, user="root", password="123456",
                                             database="signin", auth_plugin='mysql_native_password')

        authHtml = open("auth.html").read()
        authHtml = authHtml.replace("app_id", cfg['app_id'])
        camHtml = open("cam.html").read()
        camHtml = camHtml.replace("pingcap_host", cfg['host'])
        listHtml = open("list.html").read()
        thanksHtml = open("thanks.html").read()
        myServer = ThreadingHttpServer(
            ('0.0.0.0', 8000), SimpleHTTPRequestHandler)
        myServer.serve_forever()
    finally:
        myServer.server_close()
        print("server close")
