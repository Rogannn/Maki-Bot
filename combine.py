# use to combine each Flask app into one app
from flask_socketio import SocketIO
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from flask import request
from main import server as flask_app_1, socket_ as main_socket
from admin import app as flask_app_2, socket_ as admin_socket
from eventlet import wsgi
import eventlet
from functools import wraps


@flask_app_2.route('/shutdown', methods=['GET', 'POST'])
def shutdown():
    test('TESTING SERVER SHUTDOWN IF WORKING..')
    request.environ.get('werkzeug.server.shutdown')
    return admin_socket.stop(), main_socket.stop(), print("Shutdown..")


def test(data):
    return data


HOST = '127.0.0.1'
PORT = 5000


def extension(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        ...  # Extension logic
        return flask_app_2.ensure_sync(func)(*args, **kwargs)

    return wrapper


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


# access admin page through typing /admin in the url beside the localhost
application = DispatcherMiddleware(flask_app_1, {
    '/admin': flask_app_2
})

eventlet_socket = eventlet.listen((HOST, PORT))
eventlet.wsgi.server(eventlet_socket, application)
