from combine import application
from flup.server.fcgi import WSGIServer
from eventlet import wsgi
import eventlet

try:
    eventlet_socket = eventlet.listen(('127.0.0.1', 5000))
    eventlet.wsgi.server(eventlet_socket, application)
except OSError:
    print("Cannot use the port. Try running this in your command prompt as an administrator: \n"
          'netstat -ano | find ":<port>" \n'
          "This will show you the processes using that port.\n"
          "Run TASKKILL /F /PID <process id>. The process id is in the right most column.\n"
          "Try starting the server again.")


if __name__ == '__main__':
    WSGIServer(application, bindAddress=('127.0.0.1', 5000)).run()

