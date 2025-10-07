"""
Example trading strategies for prediction markets
"""

from typing import List, Dict
from datetime import datetime

from .base import Strategy
from ..backtesting.models import Market, Order, OrderType, Position
from ..backtesting.portfolio import Portfolio


class MeanReversionStrategy(Strategy):
    """
    Simple mean reversion strategy for prediction markets
    
    This strategy looks for markets where the YES price has deviated
    significantly from a threshold (e.g., 50%) and bets on reversion.
    
    Parameters:
        threshold: Price threshold for mean reversion (default 0.5)
        deviation: Required deviation from threshold to trigger trade (default 0.2)
        position_size: Fraction of portfolio to use per trade (default 0.1)
        max_price: Maximum price to buy at (default 0.8)
        min_price: Minimum price to sell at (default 0.2)
    """
    
    def __init__(self):
        super().__init__(name="MeanReversionStrategy")
        self.set_params(
            threshold=0.5,
            deviation=0.2,
            position_size=0.1,
            max_price=0.8,
            min_price=0.2
        )
    
    def generate_signals(
        self,
        markets: Dict[str, Market],
        portfolio: Portfolio,
        timestamp: datetime
    ) -> List[Order]:
        """Generate mean reversion trading signals"""
        orders = []
        
        threshold = self.params["threshold"]
        deviation = self.params["deviation"]
        position_size = self.params["position_size"]
        max_price = self.params["max_price"]
        min_price = self.params["min_price"]
        
        for market_id, market in markets.items():
            # Skip resolved markets
            if market.resolved:
                continue
            
            yes_price = market.current_yes_price
            
            # Check if we already have a position
            has_yes_position = portfolio.get_position(market_id, True) is not None
            has_no_position = portfolio.get_position(market_id, False) is not None
            
            # Buy YES if price is significantly below threshold
            if yes_price < (threshold - deviation) and yes_price < max_price:
                if not has_yes_position:
                    # Calculate shares based on position size
                    capital_to_use = portfolio.cash * position_size
                    shares = capital_to_use / yes_price
                    
                    if shares > 0:
                        orders.append(Order(
                            market_id=market_id,
                            order_type=OrderType.BUY,
                            outcome=True,
                            shares=shares,
                            price=yes_price,
                            timestamp=timestamp
                        ))
            
            # Buy NO (equivalent to selling YES) if price is significantly above threshold
            elif yes_price > (threshold + deviation) and yes_price > min_price:
                if not has_no_position:
                    no_price = market.current_no_price
                    capital_to_use = portfolio.cash * position_size
                    shares = capital_to_use / no_price
                    
                    if shares > 0:
                        orders.append(Order(
                            market_id=market_id,
                            order_type=OrderType.BUY,
                            outcome=False,
                            shares=shares,
                            price=no_price,
                            timestamp=timestamp
                        ))
            
            # Take profit on YES position if price reverted
            elif has_yes_position and yes_price >= threshold:
                position = portfolio.get_position(market_id, True)
                if position and position.shares > 0:
                    orders.append(Order(
                        market_id=market_id,
                        order_type=OrderType.SELL,
                        outcome=True,
                        shares=position.shares,
                        price=yes_price,
                        timestamp=timestamp
                    ))
            
            # Take profit on NO position if price reverted
            elif has_no_position and yes_price <= threshold:
                position = portfolio.get_position(market_id, False)
                if position and position.shares > 0:
                    no_price = market.current_no_price
                    orders.append(Order(
                        market_id=market_id,
                        order_type=OrderType.SELL,
                        outcome=False,
                        shares=position.shares,
                        price=no_price,
                        timestamp=timestamp
                    ))
        
        return orders


class MomentumStrategy(Strategy):
    """
    Momentum strategy that follows price trends
    
    This strategy buys when prices are rising and sells when falling.
    
    Parameters:
        lookback_periods: Number of periods to look back for momentum (default 5)
        momentum_threshold: Minimum price change to trigger trade (default 0.1)
        position_size: Fraction of portfolio to use per trade (default 0.1)
    """
    
    def __init__(self):
        super().__init__(name="MomentumStrategy")
        self.set_params(
            lookback_periods=5,
            momentum_threshold=0.1,
            position_size=0.1
        )
        self.price_history: Dict[str, List[float]] = {}
    
    def generate_signals(
        self,
        markets: Dict[str, Market],
        portfolio: Portfolio,
        timestamp: datetime
    ) -> List[Order]:
        """Generate momentum trading signals"""
        orders = []
        
        lookback = self.params["lookback_periods"]
        threshold = self.params["momentum_threshold"]
        position_size = self.params["position_size"]
        
        for market_id, market in markets.items():
            # Skip resolved markets
            if market.resolved:
                continue
            
            # Update price history
            if market_id not in self.price_history:
                self.price_history[market_id] = []
            
            self.price_history[market_id].append(market.current_yes_price)
            
            # Keep only lookback periods
            if len(self.price_history[market_id]) > lookback:
                self.price_history[market_id] = self.price_history[market_id][-lookback:]
            
            # Need enough history to calculate momentum
            if len(self.price_history[market_id]) < lookback:
                continue
            
            # Calculate momentum
            old_price = self.price_history[market_id][0]
            current_price = market.current_yes_price
            momentum = (current_price - old_price) / old_price if old_price > 0 else 0
            
            has_position = portfolio.get_position(market_id, True) is not None
            
            # Buy on positive momentum
            if momentum > threshold and not has_position:
                capital_to_use = portfolio.cash * position_size
                shares = capital_to_use / current_price
                
                if shares > 0:
                    orders.append(Order(
                        market_id=market_id,
                        order_type=OrderType.BUY,
                        outcome=True,
                        shares=shares,
                        price=current_price,
                        timestamp=timestamp
                    ))
            
            # Sell on negative momentum
            elif momentum < -threshold and has_position:
                position = portfolio.get_position(market_id, True)
                if position and position.shares > 0:
                    orders.append(Order(
                        market_id=market_id,
                        order_type=OrderType.SELL,
                        outcome=True,
                        shares=position.shares,
                        price=current_price,
                        timestamp=timestamp
                    ))
        
        return orders
