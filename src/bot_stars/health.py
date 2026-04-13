import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/health", "/healthz", "/ping"):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()

    # Disable default logging to keep stdout clean
    def log_message(self, format, *args):
        return


def start_health_server(host: str = "0.0.0.0", port: int | None = None) -> HTTPServer:
    """Start a simple HTTP health server in a background thread.

    Returns the HTTPServer instance. The server will run until the process exits.
    """
    if port is None:
        port = int(os.getenv("HEALTHCHECK_PORT", "8000"))

    server = HTTPServer((host, port), _HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
