"""
Quantshit Arbitrage Engine - Vercel Serverless Deployment
Serverless-friendly version without persistent background threads
"""

import sys
import os
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler

# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_api_response(path, method='GET', body=None):
    """Generate API responses for different endpoints"""
    
    try:
        if path == '/' or path == '/api/index':
            return {
                'message': 'Quantshit Arbitrage Engine - Serverless API',
                'version': '2.0.0',
                'status': 'operational',
                'timestamp': datetime.now().isoformat(),
                'deployment': 'vercel-serverless',
                'note': 'Each request runs independently - call /api/scan to trigger arbitrage detection',
                'endpoints': {
                    '/': 'API status',
                    '/api/scan': 'Run arbitrage scan cycle',
                    '/api/markets': 'Get available markets',
                    '/api/portfolio': 'Portfolio summary',
                    '/api/health': 'System health check'
                }
            }
            
        elif path == '/api/health':
            return {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'api_keys_configured': {
                    'polymarket': bool(os.getenv('POLYMARKET_API_KEY')),
                    'kalshi': bool(os.getenv('KALSHI_API_KEY'))
                }
            }
            
        elif path == '/api/scan':
            try:
                # Import and initialize trading system for this request
                from src.coordinators.trading_orchestrator import TradingOrchestrator
                
                # Run a single scan cycle
                bot = TradingOrchestrator()
                bot.run_strategy_cycle()
                
                return {
                    'message': 'Arbitrage scan completed successfully',
                    'timestamp': datetime.now().isoformat(),
                    'status': 'success',
                    'note': 'Check deployment logs for detailed scan results'
                }
                
            except Exception as e:
                return {
                    'message': 'Scan failed',
                    'error': str(e),
                    'status': 'error',
                    'timestamp': datetime.now().isoformat()
                }
                
        elif path == '/api/markets':
            try:
                # Import and get platforms
                from src.coordinators.trading_orchestrator import TradingOrchestrator
                
                bot = TradingOrchestrator()
                platforms = bot.get_available_platforms()
                
                return {
                    'platforms': platforms,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'success'
                }
                
            except Exception as e:
                return {
                    'message': 'Failed to get markets',
                    'error': str(e),
                    'status': 'error'
                }
                
        elif path == '/api/portfolio':
            try:
                # Import and get portfolio
                from src.coordinators.trading_orchestrator import TradingOrchestrator
                
                bot = TradingOrchestrator()
                portfolio = bot.get_portfolio_summary()
                
                return {
                    'portfolio': portfolio,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'success'
                }
                
            except Exception as e:
                return {
                    'message': 'Failed to get portfolio',
                    'error': str(e),
                    'status': 'error'
                }
                
        else:
            return {
                'message': 'Endpoint not found',
                'status': 'error',
                'available_endpoints': [
                    '/', '/api/scan', '/api/markets', '/api/portfolio', '/api/health'
                ]
            }
            
    except Exception as e:
        return {
            'message': 'Internal server error',
            'error': str(e),
            'status': 'error',
            'timestamp': datetime.now().isoformat()
        }

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = get_api_response(self.path, 'GET')
        self.wfile.write(json.dumps(response, indent=2).encode())
        
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Read POST body if present
        content_length = int(self.headers.get('Content-Length', 0))
        body = None
        if content_length > 0:
            body = self.rfile.read(content_length).decode()
            
        response = get_api_response(self.path, 'POST', body)
        self.wfile.write(json.dumps(response, indent=2).encode())