# use to combine each Flask app into one app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from main import server as flask_app_1
from admin import app as flask_app_2

# access admin page through typing /admin in the url beside the localhost
application = DispatcherMiddleware(flask_app_1, {
    '/admin': flask_app_2
})

print("To go to the admin side of the website, go to 127.0.0.1:5000/admin \n"
      "To login, type this: \n"
      "Username: admin1 \n"
      "Password: Samplepassword123 \n")
