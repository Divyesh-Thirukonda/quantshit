"""
Pure order execution functionality separated from portfolio tracking
Responsible solely for executing trades against platform APIs
"""

from typing import Dict, Any
from ..platforms import get_market_api


class OrderExecutor:
    """
    Responsible solely for executing orders against platform APIs
    Single Responsibility: Trade execution without portfolio concerns
    """
    
    def __init__(self, api_keys: Dict[str, str]):
        """
        Initialize order executor with platform APIs
        
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
                print(f"✗ Failed to initialize {platform} API: {e}")
    
    def execute_buy_order(self, platform: str, market_id: str, outcome: str, 
                         amount: float, price: float) -> Dict[str, Any]:
        """
        Execute a buy order on a specific platform
        
        Args:
            platform: Platform name
            market_id: Market identifier
            outcome: Outcome to buy (YES/NO)
            amount: Number of shares
            price: Price per share
            
        Returns:
            Dictionary with execution result
        """
        try:
            if platform not in self.apis:
                return {
                    'success': False,
                    'error': f'Platform {platform} not available'
                }
            
            api = self.apis[platform]
            result = api.place_buy_order(market_id, outcome, amount, price)
            
            return {
                'success': result.get('success', False),
                'platform': platform,
                'market_id': market_id,
                'outcome': outcome,
                'amount': amount,
                'price': price,
                'action': 'buy',
                'api_result': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'platform': platform,
                'market_id': market_id,
                'outcome': outcome,
                'amount': amount,
                'price': price,
                'action': 'buy',
                'error': str(e)
            }
    
    def execute_sell_order(self, platform: str, market_id: str, outcome: str, 
                          amount: float, price: float) -> Dict[str, Any]:
        """
        Execute a sell order on a specific platform
        
        Args:
            platform: Platform name
            market_id: Market identifier
            outcome: Outcome to sell (YES/NO)
            amount: Number of shares
            price: Price per share
            
        Returns:
            Dictionary with execution result
        """
        try:
            if platform not in self.apis:
                return {
                    'success': False,
                    'error': f'Platform {platform} not available'
                }
            
            api = self.apis[platform]
            result = api.place_sell_order(market_id, outcome, amount, price)
            
            return {
                'success': result.get('success', False),
                'platform': platform,
                'market_id': market_id,
                'outcome': outcome,
                'amount': amount,
                'price': price,
                'action': 'sell',
                'api_result': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'platform': platform,
                'market_id': market_id,
                'outcome': outcome,
                'amount': amount,
                'price': price,
                'action': 'sell',
                'error': str(e)
            }
    
    def is_platform_available(self, platform: str) -> bool:
        """
        Check if a platform is available for trading
        
        Args:
            platform: Platform name
            
        Returns:
            True if platform API is initialized and available
        """
        return platform in self.apis
    
    def get_available_platforms(self) -> list:
        """Get list of available platforms"""
        return list(self.apis.keys())
    
    def execute_arbitrage_legs(self, buy_details: Dict, sell_details: Dict) -> Dict[str, Any]:
        """
        Execute both legs of an arbitrage trade
        
        Args:
            buy_details: Buy order details (platform, market_id, outcome, amount, price)
            sell_details: Sell order details (platform, market_id, outcome, amount, price)
            
        Returns:
            Dictionary with results of both legs
        """
        results = {
            'success': False,
            'buy_result': None,
            'sell_result': None,
            'error': None
        }
        
        try:
            # Execute buy order
            buy_result = self.execute_buy_order(
                buy_details['platform'],
                buy_details['market_id'],
                buy_details['outcome'],
                buy_details['amount'],
                buy_details['price']
            )
            results['buy_result'] = buy_result
            
            # Execute sell order
            sell_result = self.execute_sell_order(
                sell_details['platform'],
                sell_details['market_id'],
                sell_details['outcome'],
                sell_details['amount'],
                sell_details['price']
            )
            results['sell_result'] = sell_result
            
            # Both legs must succeed for arbitrage to be successful
            if buy_result['success'] and sell_result['success']:
                results['success'] = True
            else:
                # Collect any errors
                errors = []
                if not buy_result['success']:
                    errors.append(f"Buy failed: {buy_result.get('error', 'Unknown error')}")
                if not sell_result['success']:
                    errors.append(f"Sell failed: {sell_result.get('error', 'Unknown error')}")
                results['error'] = '; '.join(errors)
            
        except Exception as e:
            results['error'] = f"Exception during execution: {str(e)}"
        
        return results