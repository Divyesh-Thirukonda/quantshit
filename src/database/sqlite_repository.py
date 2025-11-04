"""
SQLite Repository - database operations using SQLite.
Replaces in-memory storage with persistent SQLite database.
"""

import sqlite3
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from contextlib import contextmanager

from ..models import Market, Opportunity, Order, Position
from ..types import Exchange, MarketStatus, OrderStatus, OrderSide, Outcome
from ..utils import get_logger

logger = get_logger(__name__)


class SQLiteRepository:
    """
    SQLite-backed repository for persistent storage.
    """

    def __init__(self, db_path: str = 'quantshit.db'):
        """Initialize repository with SQLite database"""
        self.db_path = db_path
        logger.info(f"SQLiteRepository initialized at {db_path}")

    @contextmanager
    def _get_connection(self):
        """Get database connection with context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        try:
            yield conn
        finally:
            conn.close()

    # Market operations
    def save_market(self, market: Market) -> bool:
        """Save or update a market in the database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                now = datetime.now()

                cursor.execute("""
                    INSERT OR REPLACE INTO markets (
                        id, exchange, title, yes_price, no_price, volume,
                        liquidity, status, category, expiry, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                             COALESCE((SELECT created_at FROM markets WHERE id = ?), ?),
                             ?)
                """, (
                    market.id,
                    market.exchange.value,
                    market.title,
                    market.yes_price,
                    market.no_price,
                    market.volume,
                    market.liquidity,
                    market.status.value,
                    market.category,
                    market.expiry,
                    market.id,  # For COALESCE to preserve created_at
                    now,
                    now
                ))

                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to save market {market.id}: {e}")
            return False

    def save_markets_batch(self, markets: List[Market]) -> int:
        """Save multiple markets in a batch (more efficient)"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                now = datetime.now()

                data = [
                    (m.id, m.exchange.value, m.title, m.yes_price, m.no_price,
                     m.volume, m.liquidity, m.status.value, m.category, m.expiry,
                     m.id, now, now)
                    for m in markets
                ]

                cursor.executemany("""
                    INSERT OR REPLACE INTO markets (
                        id, exchange, title, yes_price, no_price, volume,
                        liquidity, status, category, expiry, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                             COALESCE((SELECT created_at FROM markets WHERE id = ?), ?),
                             ?)
                """, data)

                conn.commit()
                logger.info(f"Saved {len(markets)} markets to database")
                return len(markets)
        except Exception as e:
            logger.error(f"Failed to save markets batch: {e}")
            return 0

    def get_markets(
        self,
        exchange: Optional[str] = None,
        status: str = 'open',
        limit: int = 1000
    ) -> List[Market]:
        """Get markets from database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                query = "SELECT * FROM markets WHERE status = ?"
                params = [status]

                if exchange:
                    query += " AND exchange = ?"
                    params.append(exchange)

                query += " ORDER BY updated_at DESC LIMIT ?"
                params.append(limit)

                cursor.execute(query, params)
                rows = cursor.fetchall()

                markets = []
                for row in rows:
                    markets.append(self._row_to_market(row))

                return markets
        except Exception as e:
            logger.error(f"Failed to get markets: {e}")
            return []

    def _row_to_market(self, row: sqlite3.Row) -> Market:
        """Convert database row to Market object"""
        return Market(
            id=row['id'],
            exchange=Exchange(row['exchange']),
            title=row['title'],
            yes_price=row['yes_price'],
            no_price=row['no_price'],
            volume=row['volume'],
            liquidity=row['liquidity'],
            status=MarketStatus(row['status']),
            category=row['category'],
            expiry=datetime.fromisoformat(row['expiry']) if row['expiry'] else None
        )

    # Market match operations
    def save_market_match(
        self,
        kalshi_market: Market,
        polymarket_market: Market,
        confidence_score: float
    ) -> bool:
        """Save a market match (pair of equivalent markets)"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT OR REPLACE INTO market_matches (
                        kalshi_market_id, polymarket_market_id, confidence_score,
                        kalshi_title, polymarket_title, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    kalshi_market.id,
                    polymarket_market.id,
                    confidence_score,
                    kalshi_market.title,
                    polymarket_market.title,
                    datetime.now()
                ))

                conn.commit()
                return True
        except sqlite3.IntegrityError:
            # Match already exists, that's ok
            return True
        except Exception as e:
            logger.error(f"Failed to save market match: {e}")
            return False

    def save_market_matches_batch(
        self,
        matches: List[Tuple[Market, Market, float]]
    ) -> int:
        """Save multiple market matches in a batch"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                now = datetime.now()

                data = [
                    (km.id, pm.id, score, km.title, pm.title, now)
                    for km, pm, score in matches
                ]

                cursor.executemany("""
                    INSERT OR IGNORE INTO market_matches (
                        kalshi_market_id, polymarket_market_id, confidence_score,
                        kalshi_title, polymarket_title, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, data)

                conn.commit()
                count = cursor.rowcount
                logger.info(f"Saved {count} market matches to database")
                return count
        except Exception as e:
            logger.error(f"Failed to save market matches: {e}")
            return 0

    def get_market_matches(
        self,
        min_confidence: float = 0.5,
        limit: int = 1000
    ) -> List[Dict]:
        """Get market matches from database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM market_matches
                    WHERE confidence_score >= ?
                    ORDER BY confidence_score DESC, created_at DESC
                    LIMIT ?
                """, (min_confidence, limit))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get market matches: {e}")
            return []

    # Opportunity operations
    def save_opportunity(self, opportunity: Opportunity) -> bool:
        """Save an opportunity to the database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                opp_id = f"opp_{opportunity.timestamp.timestamp()}"

                cursor.execute("""
                    INSERT OR REPLACE INTO opportunities (
                        id, kalshi_market_id, polymarket_market_id, outcome,
                        spread, expected_profit, expected_profit_pct,
                        confidence_score, recommended_size, max_size,
                        timestamp, expiry, buy_exchange, sell_exchange,
                        buy_price, sell_price
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    opp_id,
                    opportunity.market_kalshi.id,
                    opportunity.market_polymarket.id,
                    opportunity.outcome.value,
                    opportunity.kalshi_price - opportunity.polymarket_price,
                    opportunity.expected_profit,
                    opportunity.expected_profit_pct,
                    opportunity.confidence_score,
                    opportunity.recommended_size,
                    opportunity.max_size,
                    opportunity.timestamp,
                    opportunity.expiry,
                    opportunity.buy_exchange.value if opportunity.buy_exchange else None,
                    opportunity.sell_exchange.value if opportunity.sell_exchange else None,
                    opportunity.buy_price,
                    opportunity.sell_price
                ))

                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to save opportunity: {e}")
            return False

    def get_opportunities(
        self,
        limit: int = 100,
        min_profit: Optional[float] = None
    ) -> List[Dict]:
        """Get opportunities from database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                query = "SELECT * FROM opportunities WHERE 1=1"
                params = []

                if min_profit is not None:
                    query += " AND expected_profit >= ?"
                    params.append(min_profit)

                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)

                cursor.execute(query, params)
                rows = cursor.fetchall()

                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get opportunities: {e}")
            return []

    # Statistics
    def get_stats(self) -> Dict:
        """Get database statistics"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                stats = {}

                # Count markets
                cursor.execute("SELECT exchange, COUNT(*) FROM markets GROUP BY exchange")
                for row in cursor.fetchall():
                    stats[f'{row[0]}_markets'] = row[1]

                # Count matches
                cursor.execute("SELECT COUNT(*) FROM market_matches")
                stats['total_matches'] = cursor.fetchone()[0]

                # Count opportunities
                cursor.execute("SELECT COUNT(*) FROM opportunities")
                stats['total_opportunities'] = cursor.fetchone()[0]

                # Count orders
                cursor.execute("SELECT COUNT(*) FROM orders")
                stats['total_orders'] = cursor.fetchone()[0]

                return stats
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

    def clear_old_data(self, days: int = 7):
        """Clear data older than specified days"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cutoff = datetime.now().timestamp() - (days * 86400)

                # Clear old opportunities
                cursor.execute(
                    "DELETE FROM opportunities WHERE timestamp < ?",
                    (datetime.fromtimestamp(cutoff),)
                )

                conn.commit()
                logger.info(f"Cleared data older than {days} days")
        except Exception as e:
            logger.error(f"Failed to clear old data: {e}")
