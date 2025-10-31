#!/usr/bin/env python
"""
Database Query Tool - Query and manage the quantshit database.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from datetime import datetime


class DatabaseQuery:
    """Simple database query tool"""

    def __init__(self, db_path: str = 'quantshit.db'):
        self.db_path = db_path

    def query(self, sql: str) -> list:
        """Execute SQL query and return results"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        conn.close()
        return results

    def stats(self):
        """Show database statistics"""
        print("\n" + "=" * 60)
        print("DATABASE STATISTICS")
        print("=" * 60)

        # Markets by exchange
        results = self.query("""
            SELECT exchange, COUNT(*) as count,
                   AVG(volume) as avg_volume,
                   SUM(CASE WHEN status='open' THEN 1 ELSE 0 END) as open_markets
            FROM markets
            GROUP BY exchange
        """)

        print("\nMarkets:")
        for r in results:
            print(f"  {r['exchange']:12} Total: {r['count']:3}  Avg Volume: ${r['avg_volume']:>10,.0f}  Open: {r['open_markets']:3}")

        # Matches
        match_count = self.query("SELECT COUNT(*) as count FROM market_matches")[0]['count']
        print(f"\nMarket Matches: {match_count}")

        if match_count > 0:
            avg_confidence = self.query(
                "SELECT AVG(confidence_score) as avg FROM market_matches"
            )[0]['avg']
            print(f"Average Confidence: {avg_confidence:.2f}")

        # Opportunities
        opp_count = self.query("SELECT COUNT(*) as count FROM opportunities")[0]['count']
        print(f"\nOpportunities: {opp_count}")

        if opp_count > 0:
            results = self.query("""
                SELECT
                    MIN(expected_profit_pct) as min_profit,
                    MAX(expected_profit_pct) as max_profit,
                    AVG(expected_profit_pct) as avg_profit
                FROM opportunities
            """)[0]
            print(f"Profit Range: {results['min_profit']:.2%} - {results['max_profit']:.2%}")
            print(f"Average Profit: {results['avg_profit']:.2%}")

        print()

    def top_markets(self, exchange: str = None, limit: int = 10):
        """Show top markets by volume"""
        print("\n" + "=" * 60)
        print(f"TOP MARKETS BY VOLUME" + (f" ({exchange.upper()})" if exchange else ""))
        print("=" * 60)

        sql = """
            SELECT id, title, exchange, yes_price, no_price, volume, liquidity
            FROM markets
            WHERE status = 'open'
        """

        if exchange:
            sql += f" AND exchange = '{exchange}'"

        sql += f" ORDER BY volume DESC LIMIT {limit}"

        results = self.query(sql)

        if not results:
            print("No markets found")
            return

        for i, r in enumerate(results, 1):
            title = r['title'][:60]
            print(f"\n{i}. [{r['exchange']}] {title}")
            print(f"   YES: ${r['yes_price']:.3f}  NO: ${r['no_price']:.3f}  Volume: ${r['volume']:,.0f}")

    def top_opportunities(self, limit: int = 10):
        """Show top opportunities"""
        print("\n" + "=" * 60)
        print("TOP OPPORTUNITIES BY PROFIT")
        print("=" * 60)

        results = self.query(f"""
            SELECT
                id, outcome, expected_profit, expected_profit_pct,
                confidence_score, kalshi_market_id, polymarket_market_id,
                buy_price, sell_price, recommended_size
            FROM opportunities
            ORDER BY expected_profit_pct DESC
            LIMIT {limit}
        """)

        if not results:
            print("No opportunities found")
            return

        for i, r in enumerate(results, 1):
            print(f"\n{i}. {r['outcome']}")
            print(f"   Profit: {r['expected_profit_pct']:.2%} (${r['expected_profit']:.2f})")
            print(f"   Confidence: {r['confidence_score']:.2f}")
            print(f"   Prices: Buy ${r['buy_price']:.3f} → Sell ${r['sell_price']:.3f}")
            print(f"   Size: {r['recommended_size']} contracts")

    def market_matches(self, limit: int = 10):
        """Show market matches"""
        print("\n" + "=" * 60)
        print("MARKET MATCHES")
        print("=" * 60)

        results = self.query(f"""
            SELECT
                kalshi_title, polymarket_title, confidence_score,
                kalshi_market_id, polymarket_market_id
            FROM market_matches
            ORDER BY confidence_score DESC
            LIMIT {limit}
        """)

        if not results:
            print("No matches found")
            return

        for i, r in enumerate(results, 1):
            print(f"\n{i}. Confidence: {r['confidence_score']:.2f}")
            print(f"   Kalshi:      {r['kalshi_title'][:65]}")
            print(f"   Polymarket:  {r['polymarket_title'][:65]}")

    def recent_scans(self):
        """Show info about recent scans"""
        print("\n" + "=" * 60)
        print("RECENT ACTIVITY")
        print("=" * 60)

        # Most recent market updates
        results = self.query("""
            SELECT exchange, MAX(updated_at) as last_update, COUNT(*) as count
            FROM markets
            GROUP BY exchange
        """)

        print("\nLast Market Updates:")
        for r in results:
            print(f"  {r['exchange']}: {r['last_update']} ({r['count']} markets)")

        # Most recent opportunities
        results = self.query("""
            SELECT MAX(timestamp) as last_opp FROM opportunities
        """)

        if results[0]['last_opp']:
            print(f"\nLast Opportunity: {results[0]['last_opp']}")

        print()


def main():
    """CLI interface"""
    if len(sys.argv) < 2:
        print("""
Database Query Tool

Usage:
  python scripts/db_query.py stats              Show database statistics
  python scripts/db_query.py markets [exchange] Show top markets
  python scripts/db_query.py opportunities      Show top opportunities
  python scripts/db_query.py matches            Show market matches
  python scripts/db_query.py recent             Show recent activity

Examples:
  python scripts/db_query.py stats
  python scripts/db_query.py markets kalshi
  python scripts/db_query.py opportunities
        """)
        sys.exit(1)

    command = sys.argv[1]
    db = DatabaseQuery()

    if command == 'stats':
        db.stats()
        db.recent_scans()

    elif command == 'markets':
        exchange = sys.argv[2] if len(sys.argv) > 2 else None
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        db.top_markets(exchange, limit)

    elif command == 'opportunities':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        db.top_opportunities(limit)

    elif command == 'matches':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        db.market_matches(limit)

    elif command == 'recent':
        db.recent_scans()

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
