"""
Market data collection functionality separated from main bot logic
Responsible for gathering market data from multiple platforms
"""

from typing import Dict, List
from ..platforms import get_market_api


class MarketDataCollector:
    """
    Responsible solely for collecting market data from configured platforms
    Single Responsibility: Data collection and basic validation
    """
    
    def __init__(self, api_keys: Dict[str, str]):
        """
        Initialize collector with platform API keys
        
        Args:
            api_keys: Dictionary mapping platform names to API keys
        """
        self.api_keys = api_keys
        self.apis = {}
        
        # Initialize APIs for each platform
        for platform, api_key in api_keys.items():
            try:
                self.apis[platform] = get_market_api(platform, api_key)
            except Exception as e:
                print(f"   ❌ Failed to initialize {platform} API: {e}")
    
    def collect_market_data(self, min_volume: float) -> Dict[str, List[Dict]]:
        """
        Collect market data from all configured platforms
        
        Args:
            min_volume: Minimum volume threshold for markets
            
        Returns:
            Dictionary mapping platform names to lists of market data
        """
        print(f"\n📊 Collecting market data...")
        
        markets_by_platform = {}
        
        for platform in self.api_keys.keys():
            markets_by_platform[platform] = self._collect_platform_data(platform, min_volume)
        
        total_markets = sum(len(markets) for markets in markets_by_platform.values())
        print(f"   Total: {total_markets} markets collected")
        
        return markets_by_platform
    
    def _collect_platform_data(self, platform: str, min_volume: float) -> List[Dict]:
        """
        Collect data from a specific platform
        
        Args:
            platform: Platform name
            min_volume: Minimum volume threshold
            
        Returns:
            List of market data dictionaries
        """
        try:
            if platform not in self.apis:
                print(f"   ❌ {platform}: API not initialized")
                return []
                
            api = self.apis[platform]
            markets = api.get_recent_markets(min_volume)
            print(f"   {platform}: {len(markets)} markets (volume > ${min_volume})")
            return markets
            
        except Exception as e:
            print(f"   ❌ {platform}: Error - {e}")
            return []
    
    def get_available_platforms(self) -> List[str]:
        """Get list of successfully initialized platforms"""
        return list(self.apis.keys())
    
    def is_platform_available(self, platform: str) -> bool:
        """Check if a specific platform is available"""
        return platform in self.apis