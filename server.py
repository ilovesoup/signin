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


    def do_GET(self):
        if self.path == '/':
            self.path = '/cam.html'
        try:
            file_to_open = open(self.path[1:]).read()
            self.send_response(200)
        except:
            file_to_open = "File not found"
            self.send_response(404)
        self.end_headers()
        self.wfile.write(bytes(file_to_open))

try:
    mydb = mysql.connector.connect(host = "localhost", port=4000 ,user = "root", password = "", database="signin")
    httpd = HTTPServer(('localhost', 8000), SimpleHTTPRequestHandler)
    httpd.serve_forever()
finally:
    mydb.close()
    print "close"