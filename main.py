"""
Main application entry point for the arbitrage trading system.
"""
import asyncio
import argparse
import signal
import sys
from typing import Optional
from datetime import datetime

from src.core.config import get_settings
from src.core.logger import get_logger, setup_logging
from src.core.database import create_tables
from src.data.providers import DataAggregator
from src.platforms.kalshi import KalshiDataProvider, KalshiTradingClient
from src.strategies.base import StrategyManager
from src.strategies.cross_platform import CrossPlatformArbitrageStrategy
from src.strategies.correlation import CorrelationArbitrageStrategy
from src.execution.engine import OrderManager
from src.risk.manager import RiskManager

logger = get_logger(__name__)


class ArbitrageSystem:
    """Main arbitrage trading system."""
    
    def __init__(self):
        self.settings = get_settings()
        self.running = False
        
        # Initialize components
        self.data_aggregator = DataAggregator()
        self.strategy_manager = StrategyManager()
        self.order_manager = OrderManager()
        self.risk_manager = RiskManager()
        
        # Add data providers
        self._setup_data_providers()
        
        # Add trading clients
        self._setup_trading_clients()
        
        # Add strategies
        self._setup_strategies()
    
    def _setup_data_providers(self):
        """Setup data providers."""
        try:
            # Add Kalshi data provider
            kalshi_provider = KalshiDataProvider()
            self.data_aggregator.add_provider(kalshi_provider)
            
            logger.info("Data providers initialized")
        
        except Exception as e:
            logger.error(f"Error setting up data providers: {e}")
    
    def _setup_trading_clients(self):
        """Setup trading clients."""
        try:
            # Add Kalshi trading client
            kalshi_client = KalshiTradingClient()
            self.order_manager.add_trading_client(kalshi_client)
            
            logger.info("Trading clients initialized")
        
        except Exception as e:
            logger.error(f"Error setting up trading clients: {e}")
    
    def _setup_strategies(self):
        """Setup trading strategies."""
        try:
            # Cross-platform arbitrage strategy
            cross_platform_config = {
                "min_spread": self.settings.cross_platform_min_spread,
                "max_position_size": self.settings.max_position_size,
                "similarity_threshold": 0.8
            }
            cross_platform_strategy = CrossPlatformArbitrageStrategy(cross_platform_config)
            self.strategy_manager.add_strategy(cross_platform_strategy)
            
            # Correlation arbitrage strategy
            correlation_config = {
                "min_correlation": self.settings.correlation_min_threshold,
                "max_correlation": self.settings.correlation_max_threshold,
                "price_deviation_threshold": 0.05
            }
            correlation_strategy = CorrelationArbitrageStrategy(correlation_config)
            self.strategy_manager.add_strategy(correlation_strategy)
            
            logger.info("Trading strategies initialized")
        
        except Exception as e:
            logger.error(f"Error setting up strategies: {e}")
    
    async def start(self):
        """Start the arbitrage system."""
        try:
            logger.info("Starting arbitrage system...")
            
            # Create database tables
            create_tables()
            logger.info("Database initialized")
            
            # Connect to data providers
            connection_results = await self.data_aggregator.connect_all()
            logger.info(f"Data provider connections: {connection_results}")
            
            # Connect to trading clients
            trading_connections = await self.order_manager.connect_all_clients()
            logger.info(f"Trading client connections: {trading_connections}")
            
            self.running = True
            logger.info("Arbitrage system started successfully")
            
            # Start main trading loop
            await self._run_trading_loop()
        
        except Exception as e:
            logger.error(f"Error starting system: {e}")
            raise
    
    async def stop(self):
        """Stop the arbitrage system."""
        try:
            logger.info("Stopping arbitrage system...")
            
            self.running = False
            
            # Cancel all active orders
            cancel_results = await self.order_manager.cancel_all_orders()
            logger.info(f"Cancelled orders: {cancel_results}")
            
            # Stop strategies
            self.strategy_manager.stop_all()
            
            # Disconnect from providers
            await self.data_aggregator.disconnect_all()
            await self.order_manager.disconnect_all_clients()
            
            logger.info("Arbitrage system stopped")
        
        except Exception as e:
            logger.error(f"Error stopping system: {e}")
    
    async def _run_trading_loop(self):
        """Main trading loop."""
        logger.info("Starting main trading loop")
        
        loop_count = 0
        
        while self.running:
            try:
                loop_count += 1
                loop_start = datetime.utcnow()
                
                # Get market data from all providers
                markets = await self.data_aggregator.get_all_markets()
                
                if not markets:
                    logger.warning("No market data available")
                    await asyncio.sleep(10)
                    continue
                
                logger.debug(f"Loop {loop_count}: Got market data from {len(markets)} platforms")
                
                # Run strategies
                signals, opportunities = await self.strategy_manager.run_all_strategies(markets)
                
                if signals:
                    logger.info(f"Generated {len(signals)} trading signals")
                
                if opportunities:
                    logger.info(f"Found {len(opportunities)} arbitrage opportunities")
                
                # Execute signals
                for signal in signals:
                    # Check risk limits
                    risk_check, risk_message = self.risk_manager.check_signal_risk(signal)
                    
                    if risk_check:
                        result = await self.order_manager.execute_signal(signal)
                        if result.success:
                            logger.info(f"Executed signal: {signal.market_id} {signal.signal_type.value}")
                        else:
                            logger.warning(f"Failed to execute signal: {result.error_message}")
                    else:
                        logger.debug(f"Signal rejected by risk manager: {risk_message}")
                
                # Execute opportunities
                for opportunity in opportunities:
                    # Check risk limits
                    risk_check, risk_message = self.risk_manager.check_opportunity_risk(opportunity)
                    
                    if risk_check:
                        results = await self.order_manager.execute_arbitrage_opportunity(opportunity)
                        successful_executions = sum(1 for r in results if r.success)
                        logger.info(f"Executed opportunity {opportunity.opportunity_id}: {successful_executions}/{len(results)} orders successful")
                    else:
                        logger.debug(f"Opportunity rejected by risk manager: {risk_message}")
                
                # Update risk metrics
                active_orders = list(self.order_manager.get_active_orders().values())
                order_history = self.order_manager.get_order_history()
                all_orders = active_orders + order_history
                
                self.risk_manager.update_positions(all_orders)
                risk_metrics = self.risk_manager.calculate_risk_metrics()
                
                # Generate risk alerts
                alerts = self.risk_manager.generate_risk_alerts(risk_metrics)
                if alerts:
                    for alert in alerts:
                        logger.warning(f"Risk Alert: {alert.message}")
                
                # Log loop performance
                loop_duration = (datetime.utcnow() - loop_start).total_seconds()
                logger.debug(f"Loop {loop_count} completed in {loop_duration:.2f}s")
                
                # Sleep before next iteration
                await asyncio.sleep(5)  # 5-second intervals
            
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(10)  # Longer sleep on error
    
    def get_status(self) -> dict:
        """Get system status."""
        return {
            "running": self.running,
            "data_providers": len(self.data_aggregator.providers),
            "trading_clients": len(self.order_manager.trading_clients),
            "strategies": self.strategy_manager.get_all_status(),
            "active_orders": len(self.order_manager.get_active_orders()),
            "risk_level": self.risk_manager.calculate_risk_metrics().risk_level.value,
            "emergency_stop": self.risk_manager.emergency_stop
        }


async def run_system():
    """Run the arbitrage system."""
    system = ArbitrageSystem()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(system.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await system.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        await system.stop()


def run_dashboard():
    """Run the Streamlit dashboard."""
    import subprocess
    import os
    
    dashboard_path = os.path.join(os.path.dirname(__file__), "src", "frontend", "dashboard.py")
    
    try:
        subprocess.run([
            "streamlit", "run", dashboard_path,
            "--server.port", str(get_settings().dashboard_port)
        ])
    except Exception as e:
        logger.error(f"Error running dashboard: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Arbitrage Trading System")
    parser.add_argument(
        "command",
        choices=["run", "dashboard", "status"],
        help="Command to execute"
    )
    parser.add_argument(
        "--config",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(log_level=args.log_level)
    
    logger.info(f"Starting arbitrage system - Command: {args.command}")
    
    if args.command == "run":
        # Run the main system
        try:
            asyncio.run(run_system())
        except KeyboardInterrupt:
            logger.info("System stopped by user")
        except Exception as e:
            logger.error(f"System error: {e}")
            sys.exit(1)
    
    elif args.command == "dashboard":
        # Run the dashboard
        run_dashboard()
    
    elif args.command == "status":
        # Show system status
        print("System Status:")
        print("- Configuration loaded")
        print("- Database accessible")
        print("- Ready to start")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()