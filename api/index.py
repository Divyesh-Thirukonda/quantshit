"""
Main API Handler for Arbitrage Trading Bot
Handles all API endpoints for the trading pipeline and frontend
"""

from http.server import BaseHTTPRequestHandler
import json
import sys
import os
from urllib.parse import urlparse, parse_qs

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import database client and handlers
from api.supabase_client import SupabaseClient
from api.api_handlers import (
    scan_markets_handler,
    detect_opportunities_handler,
    manage_portfolio_handler,
    execute_trades_handler,
    get_markets_handler,
    get_opportunities_handler,
    get_positions_handler,
    get_orders_handler,
    get_stats_handler,
    get_scan_logs_handler
)

class handler(BaseHTTPRequestHandler):
    """Main API handler - routes requests to appropriate handlers"""
    
    def _send_json_response(self, status_code: int, data: dict):
        """Helper to send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')  # CORS for frontend
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def _send_error(self, status_code: int, message: str):
        """Helper to send error response"""
        self._send_json_response(status_code, {
            'success': False,
            'error': message
        })
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests - frontend data endpoints"""
        parsed = urlparse(self.path)
        path = parsed.path
        
        try:
            # Health check
            if path == '/' or path == '/health':
                self._send_json_response(200, {
                    'success': True,
                    'message': 'Arbitrage Trading Bot API',
                    'version': '1.0.0',
                    'endpoints': {
                        'cron': ['/api/scan-markets'],
                        'pipeline': ['/api/detect-opportunities', '/api/manage-portfolio', '/api/execute-trades'],
                        'frontend': ['/api/markets', '/api/opportunities', '/api/positions', '/api/orders', '/api/stats', '/api/scans']
                    }
                })
                return
            
            # Initialize DB client
            db = SupabaseClient()
            
            # Frontend GET endpoints
            if path == '/api/markets':
                result = get_markets_handler(db, parse_qs(parsed.query))
                self._send_json_response(200, result)
                
            elif path == '/api/opportunities':
                result = get_opportunities_handler(db)
                self._send_json_response(200, result)
                
            elif path == '/api/positions':
                result = get_positions_handler(db)
                self._send_json_response(200, result)
                
            elif path == '/api/orders':
                result = get_orders_handler(db, parse_qs(parsed.query))
                self._send_json_response(200, result)
                
            elif path == '/api/stats':
                result = get_stats_handler(db)
                self._send_json_response(200, result)
                
            elif path == '/api/scans':
                result = get_scan_logs_handler(db, parse_qs(parsed.query))
                self._send_json_response(200, result)
                
            else:
                self._send_error(404, f"Endpoint not found: {path}")
                
        except Exception as e:
            self._send_error(500, f"Internal server error: {str(e)}")
    
    def do_POST(self):
        """Handle POST requests - trading pipeline endpoints"""
        parsed = urlparse(self.path)
        path = parsed.path
        
        try:
            # Read request body if present
            content_length = int(self.headers.get('Content-Length', 0))
            body = {}
            if content_length > 0:
                body_str = self.rfile.read(content_length).decode('utf-8')
                body = json.loads(body_str) if body_str else {}
            
            # Initialize DB client
            db = SupabaseClient()
            
            # Trading pipeline endpoints
            if path == '/api/scan-markets':
                result = scan_markets_handler(db, body)
                self._send_json_response(200, result)
                
            elif path == '/api/detect-opportunities':
                result = detect_opportunities_handler(db, body)
                self._send_json_response(200, result)
                
            elif path == '/api/manage-portfolio':
                result = manage_portfolio_handler(db, body)
                self._send_json_response(200, result)
                
            elif path == '/api/execute-trades':
                result = execute_trades_handler(db, body)
                self._send_json_response(200, result)
                
            else:
                self._send_error(404, f"Endpoint not found: {path}")
                
        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON in request body")
        except Exception as e:
            self._send_error(500, f"Internal server error: {str(e)}")
