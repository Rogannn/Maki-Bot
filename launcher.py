from combine import application
from werkzeug import Request, Response, run_simple  # werkzeug development server
from eventlet import wsgi
import eventlet
import multiprocessing

HOST = '127.0.0.1'
PORT = 5000


def get_token(q: multiprocessing.Queue) -> None:
    @Request.application
    def app(request: Request) -> Response:
        q.put(request.args["token"])
        return Response("", 204)

    run_simple(HOST, PORT, application, use_reloader=True, use_debugger=True, use_evalex=True,
               reloader_type='watchdog')


if __name__ == "__main__":
    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=get_token, args=(q,))
    eventlet_socket = eventlet.listen((HOST, PORT))
    eventlet.wsgi.server(eventlet_socket, application)
    p.start()
    print("waiting")
    token = q.get(block=True)
    if p.is_alive():
        p.terminate()
    print(token)
