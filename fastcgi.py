from combine import application
from flup.server.fcgi import WSGIServer

import eventlet
from eventlet import wsgi
eventlet_socket = eventlet.listen(('127.0.0.1', 5000))
eventlet.wsgi.server(eventlet_socket, application)

if __name__ == '__main__':
    WSGIServer(application, bindAddress=('127.0.0.1', 5000)).run()
