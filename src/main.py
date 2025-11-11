"""
Main entry point - orchestrates the entire arbitrage trading system.
Wires all components together and runs the main trading loop.
"""

import time
from datetime import datetime
from typing import List

# Configuration and utilities
from .config import settings, constants
from .utils import setup_logger, get_logger

# Data layer
from .database import Repository, init_database

# Domain models
from .models import Market, Opportunity, Position

# Services
from .services.matching import Matcher, Scorer
from .services.execution import Validator, Executor
from .services.monitoring import Tracker, Alerter

# Strategy
from .strategies import SimpleArbitrageStrategy, SimpleArbitrageConfig

# Exchange clients
from .exchanges import KalshiClient, PolymarketClient

logger = get_logger(__name__)


class ArbitrageBot:
    """
    Main arbitrage bot - orchestrates all components.
    """

    def __init__(self):
        """Initialize the bot and all its components"""
        logger.info("=" * 60)
        logger.info("Initializing Quantshit Arbitrage Engine")
        logger.info("=" * 60)

        # Validate configuration
        config_errors = settings.validate()
        if config_errors:
            logger.error("Configuration errors:")
            for error in config_errors:
                logger.error(f"  - {error}")
            raise ValueError("Invalid configuration")

        # Initialize database
        init_database(settings.DATABASE_URL)
        self.repository = Repository()

        # Initialize exchange clients
        logger.info("Initializing exchange clients...")
        self.kalshi_client = KalshiClient(settings.KALSHI_API_KEY)
        self.polymarket_client = PolymarketClient(settings.POLYMARKET_API_KEY)
        logger.info("  Kalshi client initialized")
        logger.info("  Polymarket client initialized")

        # Initialize services
        self.matcher = Matcher(
            similarity_threshold=constants.TITLE_SIMILARITY_THRESHOLD
        )
        self.scorer = Scorer(
            min_profit_threshold=constants.MIN_PROFIT_THRESHOLD,
            kalshi_fee=constants.FEE_KALSHI,
            polymarket_fee=constants.FEE_POLYMARKET,
            slippage=constants.SLIPPAGE_FACTOR
        )
        self.validator = Validator(
            available_capital=constants.INITIAL_CAPITAL_PER_EXCHANGE * 2
        )
        self.executor = Executor(
            paper_trading=settings.PAPER_TRADING
        )

        # Initialize monitoring
        self.tracker = Tracker()
        self.alerter = Alerter(enabled=settings.ENABLE_ALERTS)

        # Initialize strategy with config
        # Strategy owns its trading parameters (min_volume, min_spread, etc.)
        strategy_config = SimpleArbitrageConfig(
            min_volume=1000.0,  # Can be overridden by user
            min_profit_pct=constants.MIN_PROFIT_THRESHOLD,
            min_confidence=constants.MIN_CONFIDENCE_SCORE,
            max_position_size=constants.MAX_POSITION_SIZE,
            min_position_size=constants.MIN_POSITION_SIZE
        )
        self.strategy = SimpleArbitrageStrategy(config=strategy_config)

        # Tracking
        self.cycle_count = 0
        self.total_trades = 0

        logger.info("Arbitrage bot initialized successfully")
        logger.info(f"Paper trading: {settings.PAPER_TRADING}")
        logger.info(f"Alerts enabled: {settings.ENABLE_ALERTS}")
        logger.info("=" * 60)

    def run_cycle(self):
        """
        Run one complete arbitrage cycle:
        1. Fetch markets from both exchanges
        2. Find matching markets
        3. Score opportunities
        4. Select best opportunity using strategy
        5. Validate
        6. Execute if valid
        7. Monitor positions
        """
        self.cycle_count += 1
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting cycle #{self.cycle_count} at {datetime.now()}")
        logger.info(f"{'='*60}\n")

        try:
            # Step 1: Fetch markets
            logger.info("=� Step 1: Fetching markets from exchanges...")
            kalshi_markets, polymarket_markets = self.fetch_markets()
            logger.info(f"  Kalshi: {len(kalshi_markets)} markets")
            logger.info(f"  Polymarket: {len(polymarket_markets)} markets")

            # Step 2: Find matches
            logger.info("\n= Step 2: Finding matching markets...")
            matched_pairs = self.matcher.find_matches(kalshi_markets, polymarket_markets)
            logger.info(f"  Found {len(matched_pairs)} matched pairs")

            if not matched_pairs:
                logger.info("No matching markets found - skipping to next cycle")
                return

            # Step 3: Score opportunities
            logger.info("\n=� Step 3: Scoring arbitrage opportunities...")
            opportunities = self.scorer.score_opportunities(matched_pairs)
            logger.info(f"  Found {len(opportunities)} profitable opportunities")

            # Save opportunities to database
            for opp in opportunities:
                self.repository.save_opportunity(opp)

            if not opportunities:
                logger.info("No profitable opportunities - skipping to next cycle")
                return

            # Step 4: Select best opportunity using strategy
            logger.info("\n<� Step 4: Selecting best opportunity...")
            best_opportunity = self.strategy.select_best_opportunity(opportunities)

            if not best_opportunity:
                logger.info("Strategy did not select any opportunity - skipping")
                return

            logger.info(f"  Selected: {best_opportunity.outcome.value}")
            logger.info(f"  Market: {best_opportunity.market_kalshi.title[:50]}...")
            logger.info(f"  Expected profit: ${best_opportunity.expected_profit:.2f} ({best_opportunity.expected_profit_pct:.2%})")

            # Step 5: Validate
            logger.info("\n Step 5: Validating opportunity...")
            validation = self.validator.validate(best_opportunity)

            if not validation.valid:
                logger.warning(f"  Validation failed: {validation.reason}")
                return

            logger.info(f"   Validation passed: {validation.reason}")

            # Step 6: Execute
            logger.info("\n� Step 6: Executing trade...")
            execution = self.executor.execute(best_opportunity)

            if execution.success:
                logger.info("   Trade executed successfully!")

                # Save orders
                if execution.buy_order:
                    self.repository.save_order(execution.buy_order)
                if execution.sell_order:
                    self.repository.save_order(execution.sell_order)

                # Create and track position
                # TODO: Create position from executed orders
                # position = self._create_position_from_execution(execution, best_opportunity)
                # self.tracker.add_position(position)
                # self.repository.save_position(position)

                # Send alert
                self.alerter.alert_trade_executed(
                    profit=best_opportunity.expected_profit,
                    market_title=best_opportunity.market_kalshi.title,
                    success=True
                )

                self.total_trades += 1

            else:
                logger.error(f"   Trade execution failed: {execution.error_message}")
                self.alerter.alert_trade_executed(
                    profit=best_opportunity.expected_profit,
                    market_title=best_opportunity.market_kalshi.title,
                    success=False
                )

            # Step 7: Monitor positions
            logger.info("\n=� Step 7: Monitoring positions...")
            self._monitor_positions()

            logger.info(f"\nCycle #{self.cycle_count} completed")
            logger.info(f"Total trades executed: {self.total_trades}")

        except Exception as e:
            logger.error(f"Error in cycle #{self.cycle_count}: {e}", exc_info=True)
            self.alerter.alert_error(str(e), context=f"Cycle #{self.cycle_count}")

    def fetch_markets(self) -> tuple[List[Market], List[Market]]:
        """
        Fetch markets from both exchanges using the exchange clients.
        Uses min_volume from the strategy configuration.

        Returns:
            Tuple of (kalshi_markets, polymarket_markets)
        """
        # Get min_volume from strategy config (strategy owns trading parameters)
        min_volume = self.strategy.config.min_volume

        # Fetch from Kalshi
        kalshi_markets = self.kalshi_client.get_markets(min_volume=min_volume)

        # Fetch from Polymarket
        polymarket_markets = self.polymarket_client.get_markets(min_volume=min_volume)

        return kalshi_markets, polymarket_markets

    def _monitor_positions(self):
        """Monitor all open positions and check if any should be closed"""
        positions = self.repository.get_positions()

        if not positions:
            logger.info("  No open positions to monitor")
            return

        logger.info(f"  Monitoring {len(positions)} open positions")

        # TODO: Fetch current prices and update positions
        # For each position, check if it should be closed using strategy
        for position in positions:
            if self.strategy.should_close_position(position):
                logger.info(f"  Closing position {position.position_id}")
                # TODO: Execute closing trades
                # self.repository.delete_position(position.position_id)

        # Get and log summary
        summary = self.tracker.get_summary()
        logger.info(f"  Total unrealized P&L: ${summary['total_unrealized_pnl']:+.2f}")
        logger.info(f"  Total realized P&L: ${summary['total_realized_pnl']:+.2f}")

    def run_continuous(self, interval_seconds: int = constants.OPPORTUNITY_SCAN_SECONDS):
        """
        Run continuous trading loop.

        Args:
            interval_seconds: Seconds between cycles
        """
        logger.info(f"Starting continuous trading loop (interval: {interval_seconds}s)")
        logger.info("Press Ctrl+C to stop\n")

        try:
            while True:
                self.run_cycle()
                logger.info(f"\nWaiting {interval_seconds}s until next cycle...\n")
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            logger.info("\n\nBot stopped by user")
            self._shutdown()

    def run_once(self):
        """Run a single cycle then exit"""
        logger.info("Running single cycle mode\n")
        self.run_cycle()
        self._shutdown()

    def _shutdown(self):
        """Clean shutdown"""
        logger.info("\n" + "=" * 60)
        logger.info("Shutting down Quantshit Arbitrage Engine")
        logger.info("=" * 60)

        # Print final statistics
        stats = self.repository.get_stats()
        summary = self.tracker.get_summary()

        logger.info(f"Total cycles run: {self.cycle_count}")
        logger.info(f"Total trades executed: {self.total_trades}")
        logger.info(f"Total opportunities found: {stats['total_opportunities']}")
        logger.info(f"Total realized P&L: ${summary['total_realized_pnl']:+.2f}")
        logger.info(f"Total unrealized P&L: ${summary['total_unrealized_pnl']:+.2f}")

        logger.info("\nGoodbye! =K")


def main():
    """Main entry point"""
    # Setup logging
    setup_logger(
        name="quantshit",
        level=settings.LOG_LEVEL,
        log_file=settings.LOG_FILE
    )

    # Create and run bot
    bot = ArbitrageBot()

    # Run based on environment/args
    # For now, just run once
    bot.run_once()

    # To run continuously:
    # bot.run_continuous()


if __name__ == "__main__":
    main()
