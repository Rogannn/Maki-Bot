from flask import request
# use to combine each Flask app into a larger one that is dispatched based on prefix
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from main import server as flask_app_1, socket_ as main_socket
from admin import app as flask_app_2, socket_ as admin_socket
import time


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


@flask_app_2.route('/shutdown', methods=['GET', 'POST'])
def shutdown():
    flask_app_2.route("/admin-logout")
    time.sleep(5)
    admin_socket.stop()
    main_socket.stop()
    shutdown_server()


# access admin page through typing /admin in the url beside the localhost
application = DispatcherMiddleware(flask_app_1, {
    '/admin': flask_app_2
})
