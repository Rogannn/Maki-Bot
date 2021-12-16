# use to combine each Flask app into one app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from main import server as flask_app_1
from admin import app as flask_app_2

HOST = '127.0.0.1'
PORT = 5000

# access admin page through typing /admin in the url beside the localhost
application = DispatcherMiddleware(flask_app_1, {
    '/admin': flask_app_2
})
