"""
Market Scanner - fetch markets, find matches, identify opportunities, and store in database.
This module can be run standalone or integrated into the bot.
"""

from datetime import datetime
from typing import List, Tuple, Dict

from .exchanges import KalshiClient, PolymarketClient
from .models import Market, Opportunity
from .services.matching import Matcher, Scorer
from .strategies import SimpleArbitrageStrategy, SimpleArbitrageConfig
from .database.sqlite_repository import SQLiteRepository
from .utils import get_logger
from .config import settings

logger = get_logger(__name__)


class MarketScanner:
    """
    Scans markets from exchanges, finds matches, identifies opportunities,
    and stores everything in the database.
    """

    def __init__(
        self,
        db_path: str = 'quantshit.db',
        strategy_config: SimpleArbitrageConfig = None
    ):
        """
        Initialize market scanner.

        Args:
            db_path: Path to SQLite database
            strategy_config: Strategy configuration for filtering opportunities
        """
        logger.info("Initializing MarketScanner")

        # Initialize database
        self.db = SQLiteRepository(db_path)

        # Initialize exchange clients
        self.kalshi_client = KalshiClient(settings.KALSHI_API_KEY or '')
        self.polymarket_client = PolymarketClient(settings.POLYMARKET_API_KEY or '')

        # Initialize matching and scoring services
        self.matcher = Matcher(similarity_threshold=0.5)
        self.scorer = Scorer(min_profit_threshold=0.02)

        # Initialize strategy for filtering
        if strategy_config is None:
            strategy_config = SimpleArbitrageConfig()
        self.strategy_config = strategy_config

        logger.info("MarketScanner initialized")

    def fetch_and_store_markets(self, min_volume: float = None) -> Tuple[int, int]:
        """
        Fetch markets from both exchanges and store in database.

        Args:
            min_volume: Minimum volume filter (uses strategy config if None)

        Returns:
            Tuple of (kalshi_count, polymarket_count)
        """
        if min_volume is None:
            min_volume = self.strategy_config.min_volume

        logger.info(f"Fetching markets (min_volume: ${min_volume:,.0f})")

        # Fetch from Kalshi
        logger.info("Fetching from Kalshi...")
        kalshi_markets = self.kalshi_client.get_markets(min_volume=min_volume)
        kalshi_count = self.db.save_markets_batch(kalshi_markets)

        # Fetch from Polymarket
        logger.info("Fetching from Polymarket...")
        polymarket_markets = self.polymarket_client.get_markets(min_volume=min_volume)
        polymarket_count = self.db.save_markets_batch(polymarket_markets)

        logger.info(
            f"Stored {kalshi_count} Kalshi markets and "
            f"{polymarket_count} Polymarket markets"
        )

        return kalshi_count, polymarket_count

    def find_and_store_matches(self) -> int:
        """
        Find matches between markets and store in database.

        Returns:
            Number of matches found and stored
        """
        logger.info("Finding market matches...")

        # Get markets from database
        kalshi_markets = self.db.get_markets(exchange='kalshi', status='open')
        polymarket_markets = self.db.get_markets(exchange='polymarket', status='open')

        logger.info(
            f"Matching {len(kalshi_markets)} Kalshi markets with "
            f"{len(polymarket_markets)} Polymarket markets"
        )

        # Find matches
        matched_pairs = self.matcher.find_matches(kalshi_markets, polymarket_markets)

        # Store matches
        count = self.db.save_market_matches_batch(matched_pairs)

        logger.info(f"Stored {count} market matches")
        return count

    def find_and_store_opportunities(self) -> int:
        """
        Identify opportunities from matches and store in database.

        Returns:
            Number of opportunities found and stored
        """
        logger.info("Identifying arbitrage opportunities...")

        # Get markets from database
        kalshi_markets = self.db.get_markets(exchange='kalshi', status='open')
        polymarket_markets = self.db.get_markets(exchange='polymarket', status='open')

        # Find matches
        matched_pairs = self.matcher.find_matches(kalshi_markets, polymarket_markets)

        # Score opportunities
        opportunities = self.scorer.score_opportunities(matched_pairs)

        # Filter by strategy config
        filtered_opps = [
            opp for opp in opportunities
            if opp.expected_profit_pct >= self.strategy_config.min_profit_pct
            and opp.confidence_score >= self.strategy_config.min_confidence
        ]

        # Store opportunities
        count = 0
        for opp in filtered_opps:
            if self.db.save_opportunity(opp):
                count += 1

        logger.info(
            f"Found {len(opportunities)} total opportunities, "
            f"stored {count} after filtering"
        )

        return count

    def run_full_scan(self, min_volume: float = None) -> Dict:
        """
        Run a complete scan: fetch markets, find matches, identify opportunities.

        Args:
            min_volume: Minimum volume filter (uses strategy config if None)

        Returns:
            Dict with scan results
        """
        logger.info("=" * 60)
        logger.info("Starting full market scan")
        logger.info("=" * 60)

        start_time = datetime.now()

        # Step 1: Fetch and store markets
        kalshi_count, polymarket_count = self.fetch_and_store_markets(min_volume)

        # Step 2: Find and store matches
        matches_count = self.find_and_store_matches()

        # Step 3: Find and store opportunities
        opportunities_count = self.find_and_store_opportunities()

        # Get stats
        stats = self.db.get_stats()

        duration = (datetime.now() - start_time).total_seconds()

        result = {
            'success': True,
            'scan_time': start_time.isoformat(),
            'duration_seconds': duration,
            'markets_fetched': {
                'kalshi': kalshi_count,
                'polymarket': polymarket_count,
                'total': kalshi_count + polymarket_count
            },
            'matches_found': matches_count,
            'opportunities_found': opportunities_count,
            'database_stats': stats
        }

        logger.info("=" * 60)
        logger.info("Scan completed")
        logger.info(f"  Markets: {kalshi_count} Kalshi + {polymarket_count} Polymarket")
        logger.info(f"  Matches: {matches_count}")
        logger.info(f"  Opportunities: {opportunities_count}")
        logger.info(f"  Duration: {duration:.2f}s")
        logger.info("=" * 60)

        return result

    def get_best_opportunities(self, limit: int = 10) -> List[Dict]:
        """
        Get the best opportunities from the database.

        Args:
            limit: Number of opportunities to return

        Returns:
            List of opportunities sorted by profit
        """
        opportunities = self.db.get_opportunities(limit=limit)

        # Sort by expected profit percentage
        opportunities.sort(
            key=lambda x: x['expected_profit_pct'],
            reverse=True
        )

        return opportunities

    def clear_old_data(self, days: int = 7):
        """Clear opportunities older than specified days"""
        self.db.clear_old_data(days)
        logger.info(f"Cleared data older than {days} days")


def main():
    """Command-line interface for market scanner"""
    import sys

    logger.info("Market Scanner CLI")

    # Initialize scanner
    scanner = MarketScanner()

    # Get min_volume from args or use default
    min_volume = None
    if len(sys.argv) > 1:
        try:
            min_volume = float(sys.argv[1])
            logger.info(f"Using min_volume from args: ${min_volume:,.0f}")
        except ValueError:
            logger.warning("Invalid min_volume argument, using default")

    # Run full scan
    result = scanner.run_full_scan(min_volume=min_volume)

    # Print results
    print("\n" + "=" * 60)
    print("SCAN RESULTS")
    print("=" * 60)
    print(f"Markets fetched: {result['markets_fetched']['total']}")
    print(f"  - Kalshi: {result['markets_fetched']['kalshi']}")
    print(f"  - Polymarket: {result['markets_fetched']['polymarket']}")
    print(f"Matches found: {result['matches_found']}")
    print(f"Opportunities: {result['opportunities_found']}")
    print(f"Scan duration: {result['duration_seconds']:.2f}s")

    # Show best opportunities
    if result['opportunities_found'] > 0:
        print("\n" + "=" * 60)
        print("TOP OPPORTUNITIES")
        print("=" * 60)

        opps = scanner.get_best_opportunities(limit=5)
        for i, opp in enumerate(opps, 1):
            print(f"\n{i}. Profit: {opp['expected_profit_pct']:.2%} "
                  f"(${opp['expected_profit']:.2f})")
            print(f"   Confidence: {opp['confidence_score']:.2f}")
            print(f"   Kalshi: {opp['kalshi_market_id']}")
            print(f"   Polymarket: {opp['polymarket_market_id']}")

    print("\n✓ Scan complete! Data stored in database.")


if __name__ == "__main__":
    main()
