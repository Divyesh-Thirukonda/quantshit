"""
Database configuration and initialization.
"""

import os
from typing import Optional
from dotenv import load_dotenv

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Global supabase client
supabase = None


async def init_database():
    """Initialize database connection."""
    global supabase
    
    if not SUPABASE_AVAILABLE:
        print("⚠️  Supabase not available - running without database")
        return
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Missing Supabase configuration")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Database initialized successfully")


def get_supabase():
    """Get Supabase client instance."""
    if not SUPABASE_AVAILABLE:
        raise RuntimeError("Supabase not available")
    if supabase is None:
        raise RuntimeError("Database not initialized")
    return supabase


# Database schema creation SQL (to be run manually in Supabase)
DATABASE_SCHEMA = """
-- Markets table
CREATE TABLE IF NOT EXISTS markets (
    id TEXT PRIMARY KEY,
    platform TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    close_date TIMESTAMP NOT NULL,
    status TEXT NOT NULL,
    category TEXT,
    tags TEXT[],
    volume_24h DECIMAL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Quotes table
CREATE TABLE IF NOT EXISTS quotes (
    id SERIAL PRIMARY KEY,
    market_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    outcome TEXT NOT NULL,
    bid_price DECIMAL NOT NULL,
    ask_price DECIMAL NOT NULL,
    bid_size DECIMAL NOT NULL,
    ask_size DECIMAL NOT NULL,
    last_price DECIMAL,
    volume DECIMAL,
    timestamp TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (market_id) REFERENCES markets(id)
);

-- Arbitrage opportunities table
CREATE TABLE IF NOT EXISTS arbitrage_opportunities (
    id TEXT PRIMARY KEY,
    market_1_id TEXT NOT NULL,
    market_2_id TEXT NOT NULL,
    platform_1 TEXT NOT NULL,
    platform_2 TEXT NOT NULL,
    outcome TEXT NOT NULL,
    buy_platform TEXT NOT NULL,
    sell_platform TEXT NOT NULL,
    buy_price DECIMAL NOT NULL,
    sell_price DECIMAL NOT NULL,
    spread DECIMAL NOT NULL,
    spread_percentage DECIMAL NOT NULL,
    max_profit DECIMAL NOT NULL,
    estimated_profit DECIMAL NOT NULL,
    confidence_score DECIMAL NOT NULL,
    risk_level TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);

-- Positions table
CREATE TABLE IF NOT EXISTS positions (
    id TEXT PRIMARY KEY,
    market_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    outcome TEXT NOT NULL,
    order_type TEXT NOT NULL,
    quantity DECIMAL NOT NULL,
    entry_price DECIMAL NOT NULL,
    current_price DECIMAL,
    unrealized_pnl DECIMAL,
    realized_pnl DECIMAL,
    status TEXT NOT NULL,
    opened_at TIMESTAMP DEFAULT NOW(),
    closed_at TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_markets_platform ON markets(platform);
CREATE INDEX IF NOT EXISTS idx_markets_status ON markets(status);
CREATE INDEX IF NOT EXISTS idx_quotes_market_id ON quotes(market_id);
CREATE INDEX IF NOT EXISTS idx_quotes_timestamp ON quotes(timestamp);
CREATE INDEX IF NOT EXISTS idx_arbitrage_created_at ON arbitrage_opportunities(created_at);
CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);
"""