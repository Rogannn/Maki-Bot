from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from combine import application

import eventlet
from eventlet import wsgi
eventlet_socket = eventlet.listen(('127.0.0.1', 5000))
eventlet.wsgi.server(eventlet_socket, application)

http_server = HTTPServer(WSGIContainer(application))
http_server.listen(5000)  # Flask default port
print('run...')
IOLoop.current().start()
