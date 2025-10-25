"""
Vercel-compatible index.py for Quantshit API - MINIMAL VERSION
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
            'message': 'Quantshit Arbitrage Engine API - Working!',
            'version': '2.0.0',
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'path': self.path,
            'note': 'Successfully deployed on Vercel!'
        }
        
        self.wfile.write(json.dumps(response).encode())
        
    def do_POST(self):
        self.do_GET()  # Same response for now