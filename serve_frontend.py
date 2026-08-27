#!/usr/bin/env python3
"""
Simple HTTP server to serve the Napoléon AI frontend.
This is needed because the frontend loads JSON data via fetch(),
which requires HTTP protocol (not file://).
"""
import http.server
import socketserver
import webbrowser
import os

PORT = 8000

# Change to the output directory
os.chdir(os.path.join(os.path.dirname(__file__), 'output'))

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Scoped to localhost only — this server can expose scan results and
        # crawled data (including anything the security scanner flagged), so
        # a wildcard origin would let any other open tab fetch it via CORS.
        self.send_header('Access-Control-Allow-Origin', f'http://localhost:{PORT}')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        return super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

print(f"Serving Napoléon AI frontend at http://localhost:{PORT}")
print(f"Serving files from: {os.getcwd()}")
print("\nOpening browser... (Press Ctrl+C to stop)")

# Open browser automatically
webbrowser.open(f"http://localhost:{PORT}")

# Allow reuse of address to avoid "Address already in use" errors
socketserver.TCPServer.allow_reuse_address = True

# Start the server
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
