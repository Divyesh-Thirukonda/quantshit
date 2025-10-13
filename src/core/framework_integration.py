"""
Easy integration examples for the frameworks.
This file shows how to integrate the new frameworks with the existing system.
"""
import asyncio
from typing import List, Dict, Any
from src.data.framework import data_registry, auto_discover_data_sources
from src.strategies.framework import strategy_registry, auto_discover_strategies
from src.execution.framework import QuickTrader
from src.core.logger import get_logger

logger = get_logger(__name__)


class FrameworkIntegration:
    """
    Helper class to integrate the new frameworks with the existing system.
    
    This makes it easy for the main application to discover and use
    user-created data sources, strategies, and execution logic.
    """
    
    def __init__(self):
        self.data_sources_loaded = False
        self.strategies_loaded = False
    
    async def initialize_frameworks(self):
        """Initialize all frameworks and discover user components."""
        logger.info("🔧 Initializing developer frameworks...")
        
        # Discover data sources
        await self._discover_data_sources()
        
        # Discover strategies  
        await self._discover_strategies()
        
        logger.info("✅ Frameworks initialized successfully")
    
    async def _discover_data_sources(self):
        """Discover all data sources."""
        discovery_paths = [
            "src.data.custom",
            "src.data.user", 
            "src.data.examples",
            "plugins.data"  # External plugins
        ]
        
        for path in discovery_paths:
            try:
                auto_discover_data_sources(path)
                logger.debug(f"Discovered data sources from {path}")
            except ImportError:
                # Module doesn't exist, that's fine
                pass
            except Exception as e:
                logger.warning(f"Failed to discover data sources from {path}: {e}")
        
        self.data_sources_loaded = True
        logger.info(f"📊 Loaded {len(data_registry.providers)} data providers")
    
    async def _discover_strategies(self):
        """Discover all strategies."""
        discovery_paths = [
            "src.strategies.custom",
            "src.strategies.user",
            "src.strategies.examples", 
            "plugins.strategies"  # External plugins
        ]
        
        for path in discovery_paths:
            try:
                auto_discover_strategies(path)
                logger.debug(f"Discovered strategies from {path}")
            except ImportError:
                # Module doesn't exist, that's fine
                pass
            except Exception as e:
                logger.warning(f"Failed to discover strategies from {path}: {e}")
        
        self.strategies_loaded = True
        logger.info(f"🧠 Loaded {len(strategy_registry.strategies)} strategies")
    
    def get_available_data_providers(self) -> List[str]:
        """Get list of available data provider names."""
        return data_registry.list_providers()
    
    def get_available_strategies(self) -> Dict[str, Any]:
        """Get list of available strategies with metadata."""
        return strategy_registry.list_all()
    
    def get_strategy_by_name(self, name: str):
        """Get a strategy instance by name."""
        return strategy_registry.strategies.get(name)
    
    def get_data_provider_by_name(self, name: str):
        """Get a data provider instance by name."""
        return data_registry.get_provider(name)
    
    async def create_quick_trader(
        self, 
        initial_cash: float = 10000.0, 
        config: Dict[str, Any] = None
    ) -> QuickTrader:
        """Create a configured QuickTrader instance."""
        trader = QuickTrader(initial_cash=initial_cash)
        
        # Apply any global configuration
        if config:
            trader.executor.config.update(config)
        
        return trader
    
    def get_framework_status(self) -> Dict[str, Any]:
        """Get status of all frameworks."""
        return {
            'data_sources_loaded': self.data_sources_loaded,
            'strategies_loaded': self.strategies_loaded,
            'total_providers': len(data_registry.providers),
            'total_strategies': len(strategy_registry.strategies),
            'available_providers': self.get_available_data_providers(),
            'available_strategies': list(strategy_registry.strategies.keys())
        }


# Global integration instance
framework_integration = FrameworkIntegration()


async def setup_development_environment():
    """
    Setup the development environment with all frameworks.
    Call this in your main application startup.
    """
    await framework_integration.initialize_frameworks()
    
    # Show what's available
    status = framework_integration.get_framework_status()
    
    logger.info("🎯 Development Environment Ready!")
    logger.info(f"   📊 Data Providers: {status['total_providers']}")
    logger.info(f"   🧠 Strategies: {status['total_strategies']}")
    
    if status['available_providers']:
        logger.info(f"   📊 Available providers: {', '.join(status['available_providers'])}")
    
    if status['available_strategies']:
        logger.info(f"   🧠 Available strategies: {', '.join(status['available_strategies'])}")
    
    return framework_integration


# Example integration with main system
async def example_main_integration():
    """
    Example of how to integrate frameworks with the main application.
    """
    # Initialize frameworks
    integration = await setup_development_environment()
    
    # Get available components
    providers = integration.get_available_data_providers()
    strategies = integration.get_available_strategies()
    
    print(f"Available for trading:")
    print(f"  - Data providers: {len(providers)}")
    print(f"  - Strategies: {len(strategies)}")
    
    # Create a trader
    trader = await integration.create_quick_trader(
        initial_cash=5000.0,
        config={'max_position_size': 500.0}
    )
    
    print(f"  - Trader ready with ${trader.cash:.2f}")
    
    return integration


if __name__ == "__main__":
    # Test the integration
    asyncio.run(example_main_integration())