from eventlet import wsgi
from combine import application
from werkzeug.serving import run_simple  # werkzeug development server
from waitress import serve
import eventlet

HOST = '127.0.0.1'
PORT = 5000


# type /admin in the url to access admin side
if __name__ == '__main__':
    eventlet_socket = eventlet.listen((HOST, PORT))
    eventlet.wsgi.server(eventlet_socket, application)
    run_simple(HOST, PORT, application, use_reloader=True, use_debugger=True, use_evalex=True)
    # serve(application, host=HOST, port=PORT)
