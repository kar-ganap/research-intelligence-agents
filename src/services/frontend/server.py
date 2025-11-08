"""Simple HTTP server for serving static frontend files."""
import http.server
import socketserver
import os

PORT = int(os.environ.get('PORT', 8080))
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Frontend server running on port {PORT}")
    httpd.serve_forever()
