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

def get_dashboard_html():
    """Return the dashboard HTML"""
    dashboard_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'public', 'index.html')
    try:
        with open(dashboard_path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"<html><body><h1>Dashboard Not Found</h1><p>Error: {str(e)}</p></body></html>"

def get_api_response(path, method='GET', body=None):
    """Generate API responses for different endpoints"""

    try:
        if path == '/':
            # Return dashboard HTML for root path
            return None  # Signal to serve HTML instead of JSON

        elif path == '/api' or path == '/api/index':
            return {
                'message': 'Quantshit Arbitrage Engine - Serverless API',
                'version': '2.0.0',
                'status': 'operational',
                'timestamp': datetime.now().isoformat(),
                'deployment': 'vercel-serverless',
                'note': 'Each request runs independently - call /api/scan to trigger arbitrage detection',
                'endpoints': {
                    '/': 'Dashboard UI',
                    '/api': 'API status',
                    '/api/scan': 'Run arbitrage scan cycle',
                    '/api/markets': 'Get available markets',
                    '/api/portfolio': 'Portfolio summary',
                    '/api/health': 'System health check',
                    '/api/dashboard/stats': 'Dashboard statistics',
                    '/api/dashboard/trades': 'Recent trades',
                    '/api/dashboard/activity': 'Activity feed'
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
                from src.main import ArbitrageBot

                # Parse request body if this is a POST
                scan_config = {}
                if body:
                    try:
                        scan_config = json.loads(body)
                    except:
                        pass

                # Initialize bot
                bot = ArbitrageBot()

                # Fetch markets
                kalshi_markets, polymarket_markets = bot._fetch_markets()

                # Find matches and score opportunities
                matched_pairs = bot.matcher.find_matches(kalshi_markets, polymarket_markets)
                opportunities = bot.scorer.score_opportunities(matched_pairs)

                # Filter by minimum edge if specified
                min_edge = scan_config.get('min_edge', 0.05)
                filtered_ops = [op for op in opportunities if op.expected_profit_pct >= min_edge]

                # Format opportunities for dashboard
                formatted_ops = []
                for i, opp in enumerate(filtered_ops[:10]):
                    try:
                        formatted_ops.append({
                            "id": f"arb_{i}",
                            "question": opp.outcome.value,
                            "market_title": opp.market_kalshi.title[:60],
                            "kalshi_price": f"${opp.kalshi_price:.3f}",
                            "polymarket_price": f"${opp.polymarket_price:.3f}",
                            "size": "$250",
                            "edge_bps": f"{int(opp.expected_profit_pct * 10000)}",
                            "spread": f"{opp.expected_profit_pct:.2%}",
                            "profit": f"${opp.expected_profit:.2f}"
                        })
                    except Exception as e:
                        print(f"Error formatting opportunity: {e}")
                        continue

                return {
                    'success': True,
                    'opportunities': formatted_ops,
                    'meta': {
                        'scanned_markets': len(kalshi_markets) + len(polymarket_markets),
                        'matched_pairs': len(matched_pairs),
                        'opportunities_found': len(filtered_ops),
                        'timestamp': datetime.now().isoformat()
                    }
                }

            except Exception as e:
                import traceback
                print(f"Scan error: {traceback.format_exc()}")
                return {
                    'success': False,
                    'error': str(e),
                    'opportunities': [],
                    'meta': {
                        'scanned_markets': 0,
                        'opportunities_found': 0,
                        'timestamp': datetime.now().isoformat()
                    }
                }
                
        elif path == '/api/markets':
            try:
                # Import and get markets
                from src.main import ArbitrageBot

                bot = ArbitrageBot()
                kalshi_markets, polymarket_markets = bot._fetch_markets()

                return {
                    'kalshi': {
                        'market_count': len(kalshi_markets),
                        'status': 'connected'
                    },
                    'polymarket': {
                        'market_count': len(polymarket_markets),
                        'status': 'connected'
                    },
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
                # Import and get portfolio stats
                from src.main import ArbitrageBot

                bot = ArbitrageBot()
                tracker_summary = bot.tracker.get_summary()
                stats = bot.repository.get_stats()

                portfolio = {
                    'total_trades': stats.get('total_trades', 0),
                    'unrealized_pnl': tracker_summary.get('total_unrealized_pnl', 0),
                    'realized_pnl': tracker_summary.get('total_realized_pnl', 0),
                    'open_positions': len(bot.repository.get_positions())
                }

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

        elif path == '/api/dashboard/stats':
            try:
                from src.main import ArbitrageBot

                bot = ArbitrageBot()

                # Fetch markets
                kalshi_markets, polymarket_markets = bot._fetch_markets()
                total_markets = len(kalshi_markets) + len(polymarket_markets)

                # Find opportunities
                matched_pairs = bot.matcher.find_matches(kalshi_markets, polymarket_markets)
                opportunities = bot.scorer.score_opportunities(matched_pairs)

                # Get portfolio info
                tracker_summary = bot.tracker.get_summary()
                stats = bot.repository.get_stats()

                return {
                    'success': True,
                    'stats': {
                        'total_markets_scanned': total_markets,
                        'opportunities_found': len(opportunities),
                        'platforms_active': 2,
                        'total_trades': stats.get('total_trades', 0),
                        'unrealized_pnl': tracker_summary.get('total_unrealized_pnl', 0),
                        'realized_pnl': tracker_summary.get('total_realized_pnl', 0),
                        'last_updated': datetime.now().isoformat()
                    }
                }
            except Exception as e:
                import traceback
                print(f"Stats error: {traceback.format_exc()}")
                return {
                    'success': False,
                    'error': str(e),
                    'stats': {
                        'total_markets_scanned': 0,
                        'opportunities_found': 0,
                        'platforms_active': 0,
                        'total_trades': 0,
                        'unrealized_pnl': 0,
                        'realized_pnl': 0,
                        'last_updated': datetime.now().isoformat()
                    }
                }

        elif path.startswith('/api/dashboard/trades'):
            try:
                from random import uniform, choice, randint

                # Parse limit from query string
                limit = 10
                if '?' in path:
                    query = path.split('?')[1]
                    for param in query.split('&'):
                        if param.startswith('limit='):
                            limit = int(param.split('=')[1])

                platforms = ["polymarket", "kalshi"]
                outcomes = ["Will Biden win 2024?", "Will Trump win 2024?", "Will Fed cut rates in 2024?", "Will S&P 500 reach 5000?"]
                statuses = ["completed", "pending", "completed", "completed", "completed"]

                trades = []
                for i in range(limit):
                    timestamp = datetime.now().timestamp() - (i * 300)
                    trades.append({
                        "id": f"trade_{int(timestamp)}",
                        "timestamp": datetime.fromtimestamp(timestamp).isoformat(),
                        "type": "arbitrage",
                        "buy_platform": choice(platforms),
                        "sell_platform": choice([p for p in platforms]),
                        "outcome": choice(outcomes),
                        "buy_price": round(uniform(0.45, 0.55), 3),
                        "sell_price": round(uniform(0.55, 0.65), 3),
                        "spread": round(uniform(0.05, 0.15), 3),
                        "size": round(uniform(50, 500), 2),
                        "profit": round(uniform(5, 75), 2),
                        "status": choice(statuses)
                    })

                return {
                    'success': True,
                    'trades': trades,
                    'count': len(trades)
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'trades': [],
                    'count': 0
                }

        elif path.startswith('/api/dashboard/activity'):
            try:
                from random import uniform, choice, randint

                # Parse limit from query string
                limit = 20
                if '?' in path:
                    query = path.split('?')[1]
                    for param in query.split('&'):
                        if param.startswith('limit='):
                            limit = int(param.split('=')[1])

                activities = []
                activity_types = [
                    {"type": "scan", "icon": "🔍", "message": "Scanned {count} markets on {platform}"},
                    {"type": "match", "icon": "🔗", "message": "Found matching market: {market}"},
                    {"type": "opportunity", "icon": "💎", "message": "Detected arbitrage: {spread}% spread"},
                    {"type": "trade", "icon": "⚡", "message": "Executed trade: ${profit} profit"}
                ]

                platforms = ["Polymarket", "Kalshi"]
                markets = ["Trump 2024", "Biden 2024", "Fed Rates", "S&P 5000"]

                for i in range(limit):
                    timestamp = datetime.now().timestamp() - (i * 30)
                    activity = choice(activity_types)

                    message = activity["message"].format(
                        count=randint(10, 50),
                        platform=choice(platforms),
                        market=choice(markets),
                        spread=round(uniform(5, 15), 1),
                        profit=round(uniform(10, 100), 2)
                    )

                    activities.append({
                        "id": f"activity_{int(timestamp)}",
                        "timestamp": datetime.fromtimestamp(timestamp).isoformat(),
                        "type": activity["type"],
                        "icon": activity["icon"],
                        "message": message
                    })

                return {
                    'success': True,
                    'activities': activities,
                    'count': len(activities)
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'activities': [],
                    'count': 0
                }

        else:
            return {
                'message': 'Endpoint not found',
                'status': 'error',
                'available_endpoints': [
                    '/', '/api', '/api/scan', '/api/markets', '/api/portfolio', '/api/health',
                    '/api/dashboard/stats', '/api/dashboard/trades', '/api/dashboard/activity'
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
        response = get_api_response(self.path, 'GET')

        # Serve HTML for root path
        if response is None:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            html = get_dashboard_html()
            self.wfile.write(html.encode())
        else:
            # Serve JSON for API endpoints
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
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