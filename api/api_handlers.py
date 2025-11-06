"""
API Handler Functions
Each function handles a specific API endpoint
"""

import sys
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.matching.matcher import Matcher
from src.strategies.simple_arb import SimpleArbitrageStrategy
from src.services.execution.executor import Executor
from src.exchanges.kalshi_client import KalshiClient
from src.exchanges.polymarket_client import PolymarketClient
from src.models import Market, Opportunity
from src.types import Exchange, Outcome

# ========== Pipeline Endpoints ==========

def scan_markets_handler(db, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scan markets from both exchanges and find matches
    Called by cron job hourly
    """
    try:
        # Start scan log
        scan_log = db.start_scan_log(body.get('scan_type', 'scheduled'))
        scan_id = scan_log['id']
        
        metrics = {
            'started_at': scan_log['started_at'],
            'kalshi_markets': 0,
            'polymarket_markets': 0,
            'matches': 0,
            'opportunities': 0
        }
        
        # Initialize exchange clients
        kalshi = KalshiClient()
        polymarket = PolymarketClient()
        
        # Fetch markets from both exchanges
        kalshi_markets = kalshi.get_markets()
        polymarket_markets = polymarket.get_markets()
        
        metrics['kalshi_markets'] = len(kalshi_markets)
        metrics['polymarket_markets'] = len(polymarket_markets)
        
        # Store markets in database
        kalshi_market_records = []
        for km in kalshi_markets:
            for outcome in [Outcome.YES, Outcome.NO]:
                kalshi_market_records.append({
                    'market_id': km.market_id,
                    'exchange': 'kalshi',
                    'title': km.title,
                    'outcome': outcome.value,
                    'price': km.yes_price if outcome == Outcome.YES else km.no_price,
                    'volume': km.volume,
                    'liquidity': km.liquidity,
                    'status': km.status.value,
                    'close_date': km.close_date.isoformat() if km.close_date else None,
                })
        
        polymarket_market_records = []
        for pm in polymarket_markets:
            for outcome in [Outcome.YES, Outcome.NO]:
                polymarket_market_records.append({
                    'market_id': pm.market_id,
                    'exchange': 'polymarket',
                    'title': pm.title,
                    'outcome': outcome.value,
                    'price': pm.yes_price if outcome == Outcome.YES else pm.no_price,
                    'volume': pm.volume,
                    'liquidity': pm.liquidity,
                    'status': pm.status.value,
                    'close_date': pm.close_date.isoformat() if pm.close_date else None,
                })
        
        # Bulk upsert markets
        db.bulk_upsert_markets(kalshi_market_records + polymarket_market_records)
        
        # Find matches using Matcher
        matcher = Matcher()
        matches = matcher.find_matches(kalshi_markets, polymarket_markets)
        
        metrics['matches'] = len(matches)
        
        # Store matches in database
        match_records = []
        for kalshi_market, poly_market, confidence in matches:
            # Get the DB IDs for these markets
            # We'll need to query back - for now just store market_id references
            match_records.append({
                'kalshi_market_id': kalshi_market.market_id,
                'polymarket_market_id': poly_market.market_id,
                'similarity_score': confidence,
                'status': 'active'
            })
        
        if match_records:
            # Note: This requires a lookup to convert market_id to UUID
            # For now, we'll handle this differently
            pass
        
        # Complete scan log
        db.complete_scan_log(scan_id, metrics)
        
        return {
            'success': True,
            'scan_id': scan_id,
            'metrics': metrics,
            'message': f"Scan complete: found {metrics['matches']} matches from {metrics['kalshi_markets']} Kalshi and {metrics['polymarket_markets']} Polymarket markets"
        }
        
    except Exception as e:
        # Try to update scan log with error if we have scan_id
        if 'scan_id' in locals():
            db.complete_scan_log(scan_id, metrics, str(e))
        
        return {
            'success': False,
            'error': str(e)
        }


def detect_opportunities_handler(db, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze matched markets for arbitrage opportunities
    Uses strategy logic to find profitable trades
    """
    try:
        # Get active matches from database
        matches = db.get_active_matches()
        
        if not matches:
            return {
                'success': True,
                'opportunities_found': 0,
                'message': 'No active matches to analyze'
            }
        
        # Initialize strategy
        strategy = SimpleArbitrageStrategy()
        
        opportunities_found = []
        
        # For each match, check for arbitrage opportunities
        for match in matches:
            kalshi_market_data = match['kalshi_market']
            poly_market_data = match['polymarket_market']
            
            # Reconstruct Market objects
            # This is simplified - in production you'd properly reconstruct from DB
            kalshi_market = Market(
                market_id=kalshi_market_data['market_id'],
                exchange=Exchange.KALSHI,
                title=kalshi_market_data['title'],
                yes_price=kalshi_market_data.get('price'),
                # ... other fields
            )
            
            poly_market = Market(
                market_id=poly_market_data['market_id'],
                exchange=Exchange.POLYMARKET,
                title=poly_market_data['title'],
                yes_price=poly_market_data.get('price'),
                # ... other fields
            )
            
            # Check both YES and NO outcomes for opportunities
            for outcome in [Outcome.YES, Outcome.NO]:
                # Calculate if there's an arbitrage opportunity
                # This would use your existing opportunity detection logic
                pass
        
        # Store opportunities in database
        if opportunities_found:
            db.bulk_insert_opportunities(opportunities_found)
        
        return {
            'success': True,
            'opportunities_found': len(opportunities_found),
            'opportunities': opportunities_found
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def manage_portfolio_handler(db, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Portfolio management - position sizing, risk management
    Reviews open positions and determines actions
    """
    try:
        # Get open positions
        open_positions = db.get_open_positions()
        
        actions_taken = []
        
        # For each open position, check if we should:
        # 1. Close it (target reached or stop loss hit)
        # 2. Adjust it (rebalance)
        # 3. Hold it
        
        for position in open_positions:
            # Get current market prices
            # Calculate current P&L
            # Decide action based on strategy rules
            
            # Example: Check if position should be closed
            # if current_spread < close_threshold:
            #     actions_taken.append({
            #         'position_id': position['id'],
            #         'action': 'close',
            #         'reason': 'spread_converged'
            #     })
            pass
        
        return {
            'success': True,
            'positions_reviewed': len(open_positions),
            'actions_taken': actions_taken
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def execute_trades_handler(db, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute trades based on opportunities
    Places orders on exchanges and updates database
    """
    try:
        # Get new opportunities (not yet executed)
        opportunities = db.get_new_opportunities()
        
        if not opportunities:
            return {
                'success': True,
                'trades_executed': 0,
                'message': 'No new opportunities to execute'
            }
        
        # Initialize executor
        executor = Executor(paper_trading=True)  # Use paper trading for now
        
        executions = []
        
        # Execute each opportunity
        for opp_data in opportunities:
            # Reconstruct Opportunity object
            # This is simplified
            # opportunity = Opportunity(...)
            
            # Execute the trade
            # result = executor.execute(opportunity)
            
            # if result.success:
            #     # Create position record
            #     position = db.insert_position({...})
            #     
            #     # Create order records
            #     db.insert_order({...})  # Buy order
            #     db.insert_order({...})  # Sell order
            #     
            #     # Update opportunity status
            #     db.update_opportunity_status(opp_data['id'], 'executed')
            #     
            #     executions.append({
            #         'opportunity_id': opp_data['id'],
            #         'position_id': position['id'],
            #         'success': True
            #     })
            
            pass
        
        return {
            'success': True,
            'trades_executed': len(executions),
            'executions': executions
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# ========== Frontend GET Endpoints ==========

def get_markets_handler(db, query_params: Dict[str, List[str]]) -> Dict[str, Any]:
    """Get markets, optionally filtered by exchange"""
    try:
        exchange = query_params.get('exchange', [None])[0]
        markets = db.get_active_markets(exchange)
        
        return {
            'success': True,
            'count': len(markets),
            'markets': markets
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_opportunities_handler(db) -> Dict[str, Any]:
    """Get active opportunities"""
    try:
        opportunities = db.get_active_opportunities_view()
        
        return {
            'success': True,
            'count': len(opportunities),
            'opportunities': opportunities
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_positions_handler(db) -> Dict[str, Any]:
    """Get open positions"""
    try:
        positions = db.get_open_positions_view()
        
        return {
            'success': True,
            'count': len(positions),
            'positions': positions
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_orders_handler(db, query_params: Dict[str, List[str]]) -> Dict[str, Any]:
    """Get orders, optionally filtered by position_id"""
    try:
        position_id = query_params.get('position_id', [None])[0]
        
        if position_id:
            orders = db.get_orders_for_position(position_id)
        else:
            # Get recent orders
            orders = []  # Implement get_recent_orders if needed
        
        return {
            'success': True,
            'count': len(orders),
            'orders': orders
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_stats_handler(db) -> Dict[str, Any]:
    """Get trading statistics"""
    try:
        stats = db.get_trading_stats()
        
        return {
            'success': True,
            'stats': stats
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_scan_logs_handler(db, query_params: Dict[str, List[str]]) -> Dict[str, Any]:
    """Get recent scan logs"""
    try:
        limit = int(query_params.get('limit', ['10'])[0])
        scans = db.get_recent_scans(limit)
        
        return {
            'success': True,
            'count': len(scans),
            'scans': scans
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
