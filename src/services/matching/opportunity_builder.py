"""
Opportunity builder - constructs Opportunity objects using Builder pattern.
Removes business logic from Opportunity model (Single Responsibility).
"""

from datetime import datetime
from typing import Optional
from ...models import Market, Opportunity
from ...fin_types import Outcome, Quantity
from ...utils import calculate_profit
from .pricing import PriceInfo, PriceExtractor, FeeCalculator, SlippageCalculator, PositionSizer


class OpportunityBuilder:
    """
    Builder pattern for creating Opportunity objects.
    Single Responsibility: construction logic separate from the model.
    Removes business logic from Opportunity.__post_init__.
    """
    
    def __init__(
        self,
        fee_calculator: FeeCalculator = None,
        slippage_calculator: SlippageCalculator = None,
        position_sizer: PositionSizer = None
    ):
        """
        Initialize with calculation utilities.
        Dependency Injection: easy to test and configure.
        
        Args:
            fee_calculator: Calculator for exchange fees
            slippage_calculator: Calculator for slippage adjustment
            position_sizer: Calculator for position sizes
        """
        self.fee_calculator = fee_calculator or FeeCalculator()
        self.slippage_calculator = slippage_calculator or SlippageCalculator()
        self.position_sizer = position_sizer or PositionSizer()
    
    def build(
        self,
        market_kalshi: Market,
        market_polymarket: Market,
        outcome: Outcome,
        confidence_score: float,
        timestamp: datetime = None
    ) -> Opportunity:
        """
        Build an Opportunity object with all calculations applied.
        
        Args:
            market_kalshi: Kalshi market
            market_polymarket: Polymarket market
            outcome: YES or NO outcome
            confidence_score: Confidence in market match (0-1)
            timestamp: Opportunity timestamp (default: now)
            
        Returns:
            Fully constructed Opportunity object
        """
        # Extract price information
        price_info = PriceExtractor.get_price_info(
            market_kalshi,
            market_polymarket,
            outcome
        )
        
        # Apply slippage
        adjusted_price_info = self.slippage_calculator.adjust_price_info(price_info)
        
        # Get fees
        buy_fee, sell_fee = self.fee_calculator.get_fees_for_trade(
            adjusted_price_info.buy_exchange,
            adjusted_price_info.sell_exchange
        )
        
        # Calculate position size
        recommended_size, max_size = self.position_sizer.calculate_size(
            market_kalshi.liquidity,
            market_polymarket.liquidity
        )
        
        # Calculate profit
        expected_profit = calculate_profit(
            buy_price=adjusted_price_info.buy_price,
            sell_price=adjusted_price_info.sell_price,
            quantity=recommended_size,
            buy_fee_pct=buy_fee,
            sell_fee_pct=sell_fee
        )
        
        # Calculate profit percentage
        capital_required = (
            recommended_size * 
            adjusted_price_info.buy_price * 
            (1 + buy_fee)
        )
        expected_profit_pct = (
            expected_profit / capital_required 
            if capital_required > 0 
            else 0.0
        )
        
        # Determine expiry (earliest of the two markets)
        expiry = self._determine_expiry(market_kalshi, market_polymarket)
        
        # Create opportunity with all fields populated
        opportunity = Opportunity(
            market_kalshi=market_kalshi,
            market_polymarket=market_polymarket,
            outcome=outcome,
            spread=price_info.spread,
            expected_profit=expected_profit,
            expected_profit_pct=expected_profit_pct,
            confidence_score=confidence_score,
            recommended_size=recommended_size,
            max_size=max_size,
            timestamp=timestamp or datetime.now(),
            expiry=expiry,
            buy_exchange=adjusted_price_info.buy_exchange,
            sell_exchange=adjusted_price_info.sell_exchange,
            buy_price=adjusted_price_info.buy_price,
            sell_price=adjusted_price_info.sell_price
        )
        
        return opportunity
    
    @staticmethod
    def _determine_expiry(
        market1: Market,
        market2: Market
    ) -> Optional[datetime]:
        """
        Determine expiry time (earliest of the two markets).
        
        Args:
            market1: First market
            market2: Second market
            
        Returns:
            Earliest expiry, or None if neither has expiry
        """
        if market1.expiry and market2.expiry:
            return min(market1.expiry, market2.expiry)
        elif market1.expiry:
            return market1.expiry
        elif market2.expiry:
            return market2.expiry
        else:
            return None


class OpportunityValidator:
    """
    Validates that opportunities meet minimum requirements.
    Single Responsibility: validation logic separate from construction.
    """
    
    def __init__(self, min_profit_threshold: float = 0.0):
        """
        Initialize with validation thresholds.
        
        Args:
            min_profit_threshold: Minimum profit percentage required
        """
        self.min_profit_threshold = min_profit_threshold
    
    def is_valid(self, opportunity: Opportunity) -> bool:
        """
        Check if opportunity meets minimum requirements.
        
        Args:
            opportunity: Opportunity to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Must be profitable
        if not opportunity.is_profitable:
            return False
        
        # Must meet minimum profit threshold
        if opportunity.expected_profit_pct < self.min_profit_threshold:
            return False
        
        # Must not be expired
        if opportunity.is_expired:
            return False
        
        # Must have positive confidence
        if opportunity.confidence_score <= 0:
            return False
        
        return True
    
    def filter_valid(self, opportunities: list[Opportunity]) -> list[Opportunity]:
        """
        Filter list to only valid opportunities.
        
        Args:
            opportunities: List of opportunities
            
        Returns:
            Filtered list of valid opportunities
        """
        return [opp for opp in opportunities if self.is_valid(opp)]



