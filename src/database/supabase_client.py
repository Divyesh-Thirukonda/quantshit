# Supabase Database Integration
# Handles all database operations for the arbitrage system

import os
from supabase import create_client, Client
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

class SupabaseManager:
    """Manages Supabase database connections and operations"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_KEY environment variables.")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
    
    async def get_markets(self, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all markets or markets from specific platform"""
        try:
            query = self.client.table("markets").select("*")
            if platform:
                query = query.eq("platform", platform)
            
            result = query.execute()
            return result.data
        except Exception as e:
            print(f"Error fetching markets: {e}")
            return []
    
    async def store_arbitrage_opportunity(self, opportunity: Dict[str, Any]) -> bool:
        """Store a new arbitrage opportunity"""
        try:
            opportunity["created_at"] = datetime.now().isoformat()
            result = self.client.table("arbitrage_opportunities").insert(opportunity).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"Error storing arbitrage opportunity: {e}")
            return False
    
    async def get_recent_opportunities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent arbitrage opportunities"""
        try:
            result = self.client.table("arbitrage_opportunities")\
                .select("*")\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            return result.data
        except Exception as e:
            print(f"Error fetching opportunities: {e}")
            return []
    
    async def store_market_data(self, market_data: Dict[str, Any]) -> bool:
        """Store market data update"""
        try:
            market_data["updated_at"] = datetime.now().isoformat()
            
            # Upsert market data (insert or update if exists)
            result = self.client.table("markets")\
                .upsert(market_data, on_conflict="platform,market_id")\
                .execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"Error storing market data: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database connection health"""
        try:
            # Simple query to test connection
            result = self.client.table("markets").select("count", count="exact").execute()
            
            return {
                "database_connected": True,
                "total_markets": result.count if result.count else 0,
                "last_check": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "database_connected": False,
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }

# Global instance
supabase_manager = None

def get_supabase_manager() -> SupabaseManager:
    """Get or create Supabase manager instance"""
    global supabase_manager
    if supabase_manager is None:
        supabase_manager = SupabaseManager()
    return supabase_manager