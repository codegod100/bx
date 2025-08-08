#!/usr/bin/env python3
"""
A simple HTTP server that serves static files and supports SPA routing.
For any route that doesn't correspond to a file, it serves index.html.
"""

import http.server
import socketserver
import os
import sys
from urllib.parse import urlparse

class SPAServer(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.getcwd(), **kwargs)
    
    def do_GET(self):
        # Parse the URL to get the path
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        # If the path corresponds to a file that exists, serve it
        if path != '/' and os.path.exists(os.path.join(os.getcwd(), path.lstrip('/'))):
            return super().do_GET()
        
        # For all other routes, serve index.html (SPA routing)
        self.path = '/'
        return super().do_GET()

def main():
    port = 4000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    with socketserver.TCPServer(("", port), SPAServer) as httpd:
        print(f"Serving at http://localhost:{port}")
        print("Press Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped")

if __name__ == "__main__":
    main()