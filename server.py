from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO
import json
import mysql.connector
from datetime import datetime

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        self.send_response(200)
        self.end_headers()
        response = BytesIO()
        response.write(b'Signed In From ')
        response.write(b'Received: ')
        # response.write(body)
        jsonData = json.loads(body)
        name = jsonData['name']
        self.wfile.write(response.getvalue())
        
        csr = mydb.cursor()
        sql = "INSERT INTO signin (name, signin_date, photo) VALUES (%s, %s, %s)"
        
        name = jsonData['name']
        dt = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        photo_b64 = jsonData['photo']

        val = (name, dt, photo_b64)
        csr.execute(sql, val)

        mydb.commit()
        csr.close()

    def list_gen(self):
        csr = mydb.cursor(buffered=True)
        csr.execute("SELECT name, signin_date, photo FROM signin")
        res = csr.fetchall()
        content = open("list.html").read()
        body = "";
        for x in res:
            body += "<tr>"
            body += "<td>" + x[0] + "</td>"
            body += "<td>" + x[1].strftime('%Y-%m-%d %H:%M:%S') + "</td>"
            body += "<td>" + "<img style='display:block; width:100px;height:100px;' src='" + x[2] + "'/> </td>"
            body += "</tr>"
        print body
        content = content.replace("tag", body)
        csr.close()
        return content


    def do_GET(self):
        content = ""
        try:
            if self.path == "/signin":
                content = open("cam.html").read()
            else:
                content = self.list_gen()

            self.send_response(200)
        except:
            content = "Something Wrong..."
            self.send_response(404)
        self.end_headers()
        self.wfile.write(bytes(content))

try:
    mydb = mysql.connector.connect(host = "localhost", port=4000 ,user = "root", password = "", database="signin")
    httpd = HTTPServer(('localhost', 8000), SimpleHTTPRequestHandler)
    httpd.serve_forever()
finally:
    mydb.close()
    print "close"