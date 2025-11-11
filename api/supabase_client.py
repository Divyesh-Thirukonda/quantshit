"""
Supabase Database Client
Handles all database operations for the arbitrage trading bot
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from supabase import create_client, Client

class SupabaseClient:
    """Client for interacting with Supabase database"""
    
    def __init__(self):
        """Initialize Supabase client"""
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables must be set")
        
        self.client: Client = create_client(url, key)
    
    # ========== Markets ==========
    
    def upsert_market(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert or update a market"""
        result = self.client.table('markets').upsert(market_data).execute()
        return result.data[0] if result.data else None
    
    def bulk_upsert_markets(self, markets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Bulk insert/update markets"""
        result = self.client.table('markets').upsert(markets).execute()
        return result.data
    
    def get_active_markets(self, exchange: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all active markets, optionally filtered by exchange"""
        query = self.client.table('markets').select('*').eq('status', 'open')
        if exchange:
            query = query.eq('exchange', exchange)
        result = query.execute()
        return result.data
    
    # ========== Market Matches ==========
    
    def insert_market_match(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new market match"""
        result = self.client.table('market_matches').insert(match_data).execute()
        return result.data[0] if result.data else None
    
    def bulk_insert_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Bulk insert market matches"""
        result = self.client.table('market_matches').insert(matches).execute()
        return result.data
    
    def get_active_matches(self) -> List[Dict[str, Any]]:
        """Get all active market matches with related market data"""
        result = self.client.table('market_matches')\
            .select('*, kalshi_market:kalshi_market_id(*), polymarket_market:polymarket_market_id(*)')\
            .eq('status', 'active')\
            .execute()
        return result.data
    
    def update_match_status(self, match_id: str, status: str) -> Dict[str, Any]:
        """Update market match status"""
        result = self.client.table('market_matches')\
            .update({'status': status, 'last_checked': datetime.utcnow().isoformat()})\
            .eq('id', match_id)\
            .execute()
        return result.data[0] if result.data else None
    
    # ========== Opportunities ==========
    
    def insert_opportunity(self, opp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new opportunity"""
        result = self.client.table('opportunities').insert(opp_data).execute()
        return result.data[0] if result.data else None
    
    def bulk_insert_opportunities(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Bulk insert opportunities"""
        result = self.client.table('opportunities').insert(opportunities).execute()
        return result.data
    
    def get_new_opportunities(self) -> List[Dict[str, Any]]:
        """Get opportunities that haven't been evaluated yet"""
        result = self.client.table('opportunities')\
            .select('*')\
            .eq('status', 'new')\
            .order('profit_pct', desc=True)\
            .execute()
        return result.data
    
    def get_active_opportunities_view(self) -> List[Dict[str, Any]]:
        """Get opportunities using the view (includes market details)"""
        result = self.client.table('active_opportunities').select('*').execute()
        return result.data
    
    def update_opportunity_status(self, opp_id: str, status: str) -> Dict[str, Any]:
        """Update opportunity status"""
        result = self.client.table('opportunities')\
            .update({'status': status})\
            .eq('id', opp_id)\
            .execute()
        return result.data[0] if result.data else None
    
    # ========== Positions ==========
    
    def insert_position(self, position_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new position"""
        result = self.client.table('positions').insert(position_data).execute()
        return result.data[0] if result.data else None
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions"""
        result = self.client.table('positions')\
            .select('*')\
            .in_('status', ['open', 'closing'])\
            .order('opened_at', desc=True)\
            .execute()
        return result.data
    
    def get_open_positions_view(self) -> List[Dict[str, Any]]:
        """Get open positions using the view (includes order count)"""
        result = self.client.table('open_positions').select('*').execute()
        return result.data
    
    def update_position(self, position_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a position"""
        result = self.client.table('positions')\
            .update(updates)\
            .eq('id', position_id)\
            .execute()
        return result.data[0] if result.data else None
    
    def close_position(self, position_id: str, exit_prices: Dict[str, float], realized_pnl: float) -> Dict[str, Any]:
        """Close a position"""
        updates = {
            'status': 'closed',
            'exit_price_buy': exit_prices['buy'],
            'exit_price_sell': exit_prices['sell'],
            'realized_pnl': realized_pnl,
            'closed_at': datetime.utcnow().isoformat()
        }
        return self.update_position(position_id, updates)
    
    # ========== Orders ==========
    
    def insert_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new order"""
        result = self.client.table('orders').insert(order_data).execute()
        return result.data[0] if result.data else None
    
    def update_order(self, order_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an order"""
        result = self.client.table('orders')\
            .update(updates)\
            .eq('id', order_id)\
            .execute()
        return result.data[0] if result.data else None
    
    def get_orders_for_position(self, position_id: str) -> List[Dict[str, Any]]:
        """Get all orders for a specific position"""
        result = self.client.table('orders')\
            .select('*')\
            .eq('position_id', position_id)\
            .order('created_at')\
            .execute()
        return result.data
    
    # ========== Scan Logs ==========
    
    def start_scan_log(self, scan_type: str = 'scheduled') -> Dict[str, Any]:
        """Create a new scan log entry"""
        log_data = {
            'scan_type': scan_type,
            'status': 'running',
            'started_at': datetime.utcnow().isoformat()
        }
        result = self.client.table('scan_logs').insert(log_data).execute()
        return result.data[0] if result.data else None
    
    def complete_scan_log(self, log_id: str, metrics: Dict[str, Any], error: Optional[str] = None) -> Dict[str, Any]:
        """Complete a scan log entry"""
        completed_at = datetime.utcnow()
        started_at = datetime.fromisoformat(metrics.get('started_at', completed_at.isoformat()))
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)
        
        updates = {
            'status': 'failed' if error else 'completed',
            'completed_at': completed_at.isoformat(),
            'duration_ms': duration_ms,
            'kalshi_markets_found': metrics.get('kalshi_markets', 0),
            'polymarket_markets_found': metrics.get('polymarket_markets', 0),
            'matches_found': metrics.get('matches', 0),
            'opportunities_detected': metrics.get('opportunities', 0),
            'error_message': error
        }
        
        result = self.client.table('scan_logs')\
            .update(updates)\
            .eq('id', log_id)\
            .execute()
        return result.data[0] if result.data else None
    
    def get_recent_scans(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent scan logs"""
        result = self.client.table('scan_logs')\
            .select('*')\
            .order('started_at', desc=True)\
            .limit(limit)\
            .execute()
        return result.data
    
    # ========== Stats ==========
    
    def get_trading_stats(self) -> Dict[str, Any]:
        """Get trading statistics using the view"""
        result = self.client.table('trading_stats').select('*').execute()
        return result.data[0] if result.data else {}
