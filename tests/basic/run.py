from pygql import HTTPServer

server = HTTPServer('etc/http.yml')

server.start()