"""
Root index.py for Vercel deployment
"""
from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            'message': 'Quantshit Arbitrage Engine API - Root',
            'version': '2.0.0',
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'path': self.path,
            'endpoints': {
                '/api/index': 'Main API endpoint',
                '/api/test': 'Test endpoint',
                '/': 'This root endpoint'
            }
        }
        
        self.wfile.write(json.dumps(response).encode())
        
    def do_POST(self):
        self.do_GET()  # Same response for now