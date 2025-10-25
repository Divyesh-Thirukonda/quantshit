"""
Quantshit Arbitrage Engine - Full Vercel Deployment
Includes both API endpoints and background trading bot
"""

import sys
import os
import json
import asyncio
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Global bot instance and status
bot_instance = None
bot_thread = None
bot_status = {
    'running': False,
    'last_cycle': None,
    'opportunities_found': 0,
    'trades_executed': 0,
    'error': None
}

def start_bot_background():
    """Start the trading bot in a background thread"""
    global bot_instance, bot_status
    
    try:
        # Import trading system
        from src.coordinators.trading_orchestrator import TradingOrchestrator
        
        # Initialize bot
        bot_instance = TradingOrchestrator()
        bot_status['running'] = True
        bot_status['error'] = None
        
        # Run bot cycles
        while bot_status['running']:
            try:
                bot_instance.run_strategy_cycle()
                bot_status['last_cycle'] = datetime.now().isoformat()
                # Wait 30 minutes between cycles (for faster iteration)
                import time
                time.sleep(1800)  # 30 minutes
            except Exception as e:
                bot_status['error'] = str(e)
                print(f"Bot cycle error: {e}")
                time.sleep(300)  # Wait 5 minutes before retry
                
    except Exception as e:
        bot_status['error'] = f"Bot startup failed: {str(e)}"
        bot_status['running'] = False
        print(f"Bot startup error: {e}")

def get_api_response(path, method='GET', body=None):
    """Generate API responses for different endpoints"""
    global bot_instance, bot_status
    
    try:
        if path == '/' or path == '/api/index':
            return {
                'message': 'Quantshit Arbitrage Engine - Full System',
                'version': '2.0.0',
                'status': 'operational',
                'timestamp': datetime.now().isoformat(),
                'bot_status': bot_status,
                'endpoints': {
                    '/': 'API status',
                    '/api/scan': 'Manual arbitrage scan',
                    '/api/markets': 'Get available markets',
                    '/api/portfolio': 'Portfolio summary',
                    '/api/bot/start': 'Start trading bot',
                    '/api/bot/stop': 'Stop trading bot',
                    '/api/bot/status': 'Bot status'
                }
            }
            
        elif path == '/api/bot/status':
            return {
                'bot_status': bot_status,
                'timestamp': datetime.now().isoformat()
            }
            
        elif path == '/api/bot/start' and method == 'POST':
            global bot_thread
            if not bot_status['running']:
                bot_thread = threading.Thread(target=start_bot_background, daemon=True)
                bot_thread.start()
                return {'message': 'Trading bot started', 'status': 'success'}
            else:
                return {'message': 'Trading bot already running', 'status': 'warning'}
                
        elif path == '/api/bot/stop' and method == 'POST':
            bot_status['running'] = False
            return {'message': 'Trading bot stopped', 'status': 'success'}
            
        elif path == '/api/scan':
            if bot_instance:
                try:
                    # Run a manual scan
                    bot_instance.run_strategy_cycle()
                    return {
                        'message': 'Manual scan completed',
                        'timestamp': datetime.now().isoformat(),
                        'status': 'success'
                    }
                except Exception as e:
                    return {
                        'message': 'Scan failed',
                        'error': str(e),
                        'status': 'error'
                    }
            else:
                return {
                    'message': 'Bot not initialized',
                    'error': 'Start the bot first',
                    'status': 'error'
                }
                
        elif path == '/api/markets':
            if bot_instance:
                try:
                    platforms = bot_instance.get_available_platforms()
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
            else:
                return {
                    'message': 'Bot not initialized',
                    'status': 'error'
                }
                
        elif path == '/api/portfolio':
            if bot_instance:
                try:
                    portfolio = bot_instance.get_portfolio_summary()
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
                    'message': 'Bot not initialized',
                    'status': 'error'
                }
                
        else:
            return {
                'message': 'Endpoint not found',
                'status': 'error',
                'available_endpoints': [
                    '/', '/api/scan', '/api/markets', '/api/portfolio',
                    '/api/bot/start', '/api/bot/stop', '/api/bot/status'
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

# Auto-start the bot when the module is loaded
if not bot_status['running']:
    try:
        bot_thread = threading.Thread(target=start_bot_background, daemon=True)
        bot_thread.start()
        print("🤖 Trading bot auto-started on deployment")
    except Exception as e:
        print(f"❌ Failed to auto-start bot: {e}")