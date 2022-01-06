from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from combine import application

http_server = HTTPServer(WSGIContainer(application))
http_server.listen(5000)  # Flask default port
print('run...')
IOLoop.current().start()
