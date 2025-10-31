"""
Database schema definitions.
When changing DB structure, only modify this file. Services don't care about schema.

Note: Currently using in-memory storage. This file defines the schema
for when we migrate to a real database (SQLite, PostgreSQL, etc.)
"""

from typing import Optional
from ..utils import get_logger

logger = get_logger(__name__)


# Schema definitions for future SQL implementation
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
        db_url: Database connection URL (for future SQL implementation)
    """
    logger.info("Database initialization (currently in-memory mode)")

    # For now, we're using in-memory storage via Repository class
    # When we migrate to SQL, this function will:
    # 1. Connect to database
    # 2. Create tables if they don't exist
    # 3. Run migrations

    # Example (for future SQL implementation):
    # import sqlite3
    # conn = sqlite3.connect(db_url or 'quantshit.db')
    # cursor = conn.cursor()
    # cursor.executescript(OPPORTUNITIES_TABLE)
    # cursor.executescript(ORDERS_TABLE)
    # cursor.executescript(POSITIONS_TABLE)
    # conn.commit()
    # conn.close()

    logger.info("Database ready")


# Migration functions (for future use)
def migrate_to_v2():
    """Example migration function"""
    pass


def rollback_to_v1():
    """Example rollback function"""
    pass
