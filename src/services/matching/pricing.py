"""
Pricing utilities for arbitrage calculation.
DRY Principle: Centralize price extraction and fee calculation logic.
Single Responsibility: Each class handles one aspect of pricing.
"""

from dataclasses import dataclass
from typing import Tuple
from ...models import Market
from ...fin_types import Outcome, Price, Exchange
from ...config import constants


@dataclass
class PriceInfo:
    """
    Structured price information for an outcome.
    Value object: immutable and side-effect free.
    """
    buy_price: Price
    sell_price: Price
    buy_exchange: str
    sell_exchange: str
    
    @property
    def spread(self) -> float:
        """Calculate absolute spread between buy and sell prices."""
        return abs(self.sell_price - self.buy_price)


class PriceExtractor:
    """
    Extracts and compares prices across markets.
    Single Responsibility: price extraction only.
    """
    
    @staticmethod
    def get_price_for_outcome(market: Market, outcome: Outcome) -> Price:
        """
        Get price for specific outcome from market.
        DRY: Single implementation used everywhere.
        
        Args:
            market: Market to extract price from
            outcome: YES or NO outcome
            
        Returns:
            Price for the outcome
        """
        return market.yes_price if outcome == Outcome.YES else market.no_price
    
    @staticmethod
    def get_price_info(
        market1: Market,
        market2: Market,
        outcome: Outcome
    ) -> PriceInfo:
        """
        Determine buy/sell prices and exchanges for arbitrage.
        DRY: Eliminates duplicated logic in scorer.
        
        Args:
            market1: First market (e.g., Kalshi)
            market2: Second market (e.g., Polymarket)
            outcome: Outcome to check (YES or NO)
            
        Returns:
            PriceInfo with buy/sell details
        """
        price1 = PriceExtractor.get_price_for_outcome(market1, outcome)
        price2 = PriceExtractor.get_price_for_outcome(market2, outcome)
        
        # Buy low, sell high
        if price1 < price2:
            return PriceInfo(
                buy_price=price1,
                sell_price=price2,
                buy_exchange=market1.exchange.value,
                sell_exchange=market2.exchange.value
            )
        else:
            return PriceInfo(
                buy_price=price2,
                sell_price=price1,
                buy_exchange=market2.exchange.value,
                sell_exchange=market1.exchange.value
            )


class FeeCalculator:
    """
    Calculates fees for different exchanges.
    Open/Closed: Can extend with new exchanges without modification.
    """
    
    def __init__(
        self,
        exchange_fees: dict[str, float] = None
    ):
        """
        Initialize with exchange fee mappings.
        Dependency Injection: fees configurable, easy to test.
        
        Args:
            exchange_fees: Map of exchange name to fee percentage
                          (e.g., {'kalshi': 0.007, 'polymarket': 0.02})
        """
        self.exchange_fees = exchange_fees or {
            Exchange.KALSHI.value: constants.FEE_KALSHI,
            Exchange.POLYMARKET.value: constants.FEE_POLYMARKET
        }
    
    def get_fee(self, exchange: str) -> float:
        """
        Get fee percentage for an exchange.
        
        Args:
            exchange: Exchange name
            
        Returns:
            Fee percentage (e.g., 0.007 for 0.7%)
            
        Raises:
            ValueError: If exchange not recognized
        """
        if exchange not in self.exchange_fees:
            raise ValueError(f"Unknown exchange: {exchange}. Known: {list(self.exchange_fees.keys())}")
        return self.exchange_fees[exchange]
    
    def get_fees_for_trade(
        self,
        buy_exchange: str,
        sell_exchange: str
    ) -> Tuple[float, float]:
        """
        Get buy and sell fees for a cross-exchange trade.
        DRY: Single method for fee lookup.
        
        Args:
            buy_exchange: Exchange to buy on
            sell_exchange: Exchange to sell on
            
        Returns:
            Tuple of (buy_fee, sell_fee) percentages
        """
        buy_fee = self.get_fee(buy_exchange)
        sell_fee = self.get_fee(sell_exchange)
        return buy_fee, sell_fee


class SlippageCalculator:
    """
    Applies slippage adjustments to prices.
    Single Responsibility: slippage calculation only.
    """
    
    def __init__(self, slippage_factor: float = constants.SLIPPAGE_FACTOR):
        """
        Initialize with slippage factor.
        
        Args:
            slippage_factor: Slippage percentage (e.g., 0.005 for 0.5%)
        """
        self.slippage_factor = slippage_factor
    
    def adjust_buy_price(self, price: Price) -> Price:
        """
        Adjust buy price upward for slippage.
        
        Args:
            price: Original buy price
            
        Returns:
            Adjusted price (higher)
        """
        return price * (1 + self.slippage_factor)
    
    def adjust_sell_price(self, price: Price) -> Price:
        """
        Adjust sell price downward for slippage.
        
        Args:
            price: Original sell price
            
        Returns:
            Adjusted price (lower)
        """
        return price * (1 - self.slippage_factor)
    
    def adjust_price_info(self, price_info: PriceInfo) -> PriceInfo:
        """
        Apply slippage to both buy and sell prices.
        
        Args:
            price_info: Original price information
            
        Returns:
            New PriceInfo with adjusted prices
        """
        return PriceInfo(
            buy_price=self.adjust_buy_price(price_info.buy_price),
            sell_price=self.adjust_sell_price(price_info.sell_price),
            buy_exchange=price_info.buy_exchange,
            sell_exchange=price_info.sell_exchange
        )


class PositionSizer:
    """
    Calculates appropriate position sizes based on liquidity and constraints.
    Single Responsibility: position sizing only.
    """
    
    def __init__(
        self,
        min_size: int = constants.MIN_POSITION_SIZE,
        max_size: int = constants.MAX_POSITION_SIZE
    ):
        """
        Initialize with size constraints.
        
        Args:
            min_size: Minimum position size
            max_size: Maximum position size
        """
        self.min_size = min_size
        self.max_size = max_size
    
    def calculate_size(
        self,
        market1_liquidity: float,
        market2_liquidity: float
    ) -> Tuple[int, int]:
        """
        Calculate recommended and maximum position sizes.
        
        Args:
            market1_liquidity: Liquidity on first market
            market2_liquidity: Liquidity on second market
            
        Returns:
            Tuple of (recommended_size, max_size)
        """
        # Maximum is limited by the less liquid market
        max_available = int(min(market1_liquidity, market2_liquidity))
        
        # Cap at configured maximum
        max_size = min(max_available, self.max_size)
        
        # Recommended size is max, but at least minimum
        recommended_size = max(max_size, self.min_size)
        
        return recommended_size, max_size



