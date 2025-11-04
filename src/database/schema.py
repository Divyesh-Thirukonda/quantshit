"""
Database schema definitions.
When changing DB structure, only modify this file. Services don't care about schema.

Note: Currently using in-memory storage. This file defines the schema
for when we migrate to a real database (SQLite, PostgreSQL, etc.)
"""

from typing import Optional
from ..utils import get_logger

logger = get_logger(__name__)


# Schema definitions for SQL implementation

# Markets table - stores all markets from both exchanges
MARKETS_TABLE = """
CREATE TABLE IF NOT EXISTS markets (
    id TEXT PRIMARY KEY,
    exchange TEXT NOT NULL,
    title TEXT NOT NULL,
    yes_price REAL NOT NULL,
    no_price REAL NOT NULL,
    volume REAL DEFAULT 0.0,
    liquidity REAL DEFAULT 0.0,
    status TEXT NOT NULL,
    category TEXT,
    expiry TIMESTAMP,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_markets_exchange ON markets(exchange);
CREATE INDEX IF NOT EXISTS idx_markets_status ON markets(status);
CREATE INDEX IF NOT EXISTS idx_markets_updated ON markets(updated_at);
"""

# Market matches table - stores pairs of equivalent markets
MARKET_MATCHES_TABLE = """
CREATE TABLE IF NOT EXISTS market_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kalshi_market_id TEXT NOT NULL,
    polymarket_market_id TEXT NOT NULL,
    confidence_score REAL NOT NULL,
    kalshi_title TEXT NOT NULL,
    polymarket_title TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    UNIQUE(kalshi_market_id, polymarket_market_id)
);

CREATE INDEX IF NOT EXISTS idx_matches_confidence ON market_matches(confidence_score);
CREATE INDEX IF NOT EXISTS idx_matches_created ON market_matches(created_at);
"""

# Opportunities table
OPPORTUNITIES_TABLE = """
CREATE TABLE IF NOT EXISTS opportunities (
    id TEXT PRIMARY KEY,
    kalshi_market_id TEXT NOT NULL,
    polymarket_market_id TEXT NOT NULL,
    outcome TEXT NOT NULL,
    spread REAL NOT NULL,
    expected_profit REAL NOT NULL,
    expected_profit_pct REAL NOT NULL,
    confidence_score REAL NOT NULL,
    recommended_size INTEGER NOT NULL,
    max_size INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    expiry TIMESTAMP,
    buy_exchange TEXT,
    sell_exchange TEXT,
    buy_price REAL,
    sell_price REAL
);

CREATE INDEX IF NOT EXISTS idx_opportunities_timestamp ON opportunities(timestamp);
CREATE INDEX IF NOT EXISTS idx_opportunities_profit ON opportunities(expected_profit);
"""

ORDERS_TABLE = """
CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    platform_order_id TEXT,
    exchange TEXT NOT NULL,
    market_id TEXT NOT NULL,
    outcome TEXT NOT NULL,
    side TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    filled_quantity INTEGER DEFAULT 0,
    average_fill_price REAL DEFAULT 0.0,
    status TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    filled_at TIMESTAMP,
    fees REAL DEFAULT 0.0
);

CREATE INDEX IF NOT EXISTS idx_orders_timestamp ON orders(timestamp);
CREATE INDEX IF NOT EXISTS idx_orders_exchange ON orders(exchange);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
"""

POSITIONS_TABLE = """
CREATE TABLE IF NOT EXISTS positions (
    position_id TEXT PRIMARY KEY,
    market_id TEXT NOT NULL,
    exchange TEXT NOT NULL,
    outcome TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    avg_entry_price REAL NOT NULL,
    current_price REAL NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    total_cost REAL DEFAULT 0.0,
    target_exit_price REAL
);

CREATE INDEX IF NOT EXISTS idx_positions_exchange ON positions(exchange);
CREATE INDEX IF NOT EXISTS idx_positions_market ON positions(market_id);
"""


def init_database(db_url: Optional[str] = None):
    """
    Initialize database with schema.

    Args:
        db_url: Database connection URL (SQLite path)
    """
    import sqlite3
    import os

    # Use SQLite by default
    db_path = db_url or 'quantshit.db'

    # Create directory if needed
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    logger.info(f"Initializing database at {db_path}")

    # Connect and create tables
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Create all tables
        cursor.executescript(MARKETS_TABLE)
        cursor.executescript(MARKET_MATCHES_TABLE)
        cursor.executescript(OPPORTUNITIES_TABLE)
        cursor.executescript(ORDERS_TABLE)
        cursor.executescript(POSITIONS_TABLE)

        conn.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

    logger.info("Database ready")


# Migration functions (for future use)
def migrate_to_v2():
    """Example migration function"""
    pass


def rollback_to_v1():
    """Example rollback function"""
    pass
