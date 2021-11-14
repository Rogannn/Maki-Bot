# use to combine each Flask app into one app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from flask import request
from main import server as flask_app_1, socket_ as main_socket
from admin import app as flask_app_2, socket_ as admin_socket
from functools import wraps
import os

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


@flask_app_2.route('/shutdown', methods=['GET', 'POST'])
def shutdown():
    os.system("taskkill /im msedge.exe /f")
    os.system("taskkill /im chrome.exe /f")
    os.system("taskkill /im firefox.exe /f")

    return admin_socket.stop(), main_socket.stop(), shutdown_server()


# access admin page through typing /admin in the url beside the localhost
application = DispatcherMiddleware(flask_app_1, {
    '/admin': flask_app_2
})
