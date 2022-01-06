from combine import application
from werkzeug import run_simple  # werkzeug development server

import eventlet
from eventlet import wsgi
eventlet_socket = eventlet.listen(('127.0.0.1', 5000))
eventlet.wsgi.server(eventlet_socket, application)

if __name__ == "__main__":
    run_simple('127.0.0.1', 5000, application, use_reloader=True, use_debugger=True, use_evalex=True,
               reloader_type='watchdog')
