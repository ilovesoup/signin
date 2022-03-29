from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO
import json
import mysql.connector
from datetime import datetime
import jwt
# python3
import urllib.parse as urlparse
# python2
# import urlparse


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_auth(self, token, refertag):
        try:
            decodedToken = jwt.decode(token, "", algorithms=[
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
        content = open("cam.html").read()
        self.wfile.write(bytes(content, encoding='utf8'))

    def auth(self, reftag):
        if reftag == None:
            return
        self.send_response(200)
        self.end_headers()
        content = open("auth.html").read()
        content = content.replace("reftag", reftag)
        self.wfile.write(bytes(content, encoding='utf8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])

        body = self.rfile.read(content_length)
        jsonData = json.loads(body)

        res = self.do_auth(jsonData['token'], None)
        if not res[0]:
            return

        # self.send_response(200)
        # self.end_headers()
        # response = BytesIO()
        # self.wfile.write(response.getvalue())

        csr = mydb.cursor()
        sql = "REPLACE INTO signin (name, signin_date, photo) VALUES (%s, %s, %s)"
        name = res[1]
        dt = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        photoB64 = jsonData['photo']

        val = (name, dt, photoB64)
        csr.execute(sql, val)

        mydb.commit()
        csr.close()

        self.send_response(302)
        new_path = '%s%s' % (
            'http://localhost:8000/list?token=', jsonData['token'])
        self.send_header('Location', new_path)
        self.end_headers()

    def list_gen(self, token):
        if not self.do_auth(token, "list")[0]:
            return

        self.send_response(200)
        self.end_headers()

        csr = mydb.cursor(buffered=True)
        csr.execute("SELECT name, signin_date, photo FROM signin")
        res = csr.fetchall()
        content = open("list.html").read()
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
        csr.close()
        self.wfile.write(bytes(content, encoding='utf8'))

    def do_GET(self):
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


if __name__ == "__main__":
    try:
        mydb = mysql.connector.connect(
            host="localhost", port=3306, user="root", password="",
            database="signin", auth_plugin='mysql_native_password')
        httpd = HTTPServer(('localhost', 8000), SimpleHTTPRequestHandler)
        httpd.serve_forever()
    finally:
        mydb.close()
        print("server close")
