from combine import application
from werkzeug import run_simple  # werkzeug development server

import eventlet
from eventlet import wsgi

try:
    eventlet_socket = eventlet.listen(('127.0.0.1', 5000))
    eventlet.wsgi.server(eventlet_socket, application)
except OSError:
    print("Cannot use the port. Try running this in your command prompt as an administrator: \n"
          'netstat -ano | find ":<port>" \n'
          "This will show you the processes using that port.\n"
          "Run TASKKILL /F /PID <process id>. The process id is in the right most column.\n"
          "Try starting the server again.")

# TO LOGIN IN ADMIN PAGE: admin1, Samplepassword123
if __name__ == "__main__":
    run_simple('127.0.0.1', 5000, application, use_debugger=True)
