from eventlet import wsgi
from werkzeug.serving import run_simple  # werkzeug development server
from combine import application

import eventlet
eventlet_socket = eventlet.listen(('localhost', 5000))
eventlet.wsgi.server(eventlet_socket, application)

# type /admin in the url to access admin side
if __name__ == '__main__':
    run_simple('localhost', 5000, application, use_reloader=True, use_debugger=True, use_evalex=True)
