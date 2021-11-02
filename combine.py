from werkzeug.middleware.dispatcher import \
    DispatcherMiddleware  # use to combine each Flask app into a larger one that is dispatched based on prefix
from main import server as flask_app_1
from admin import app as flask_app_2

# access admin page through typing /admin in the url beside the localhost
application = DispatcherMiddleware(flask_app_1, {
    '/admin': flask_app_2
})
