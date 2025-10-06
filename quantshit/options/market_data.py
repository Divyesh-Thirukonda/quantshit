"""
Market Data Module

This module provides functionality for order book management and market data feeds.
"""

import numpy as np
from collections import defaultdict
from datetime import datetime


class OrderBook:
    """Order book for tracking bids and asks"""
    
    def __init__(self, symbol):
        """
        Initialize order book
        
        Parameters:
        -----------
        symbol : str
            Trading symbol
        """
        self.symbol = symbol
        self.bids = defaultdict(float)  # price -> quantity
        self.asks = defaultdict(float)  # price -> quantity
        self.last_update = None
    
    def add_bid(self, price, quantity):
        """Add or update a bid"""
        self.bids[price] = quantity
        self.last_update = datetime.now()
    
    def add_ask(self, price, quantity):
        """Add or update an ask"""
        self.asks[price] = quantity
        self.last_update = datetime.now()
    
    def remove_bid(self, price):
        """Remove a bid"""
        if price in self.bids:
            del self.bids[price]
            self.last_update = datetime.now()
    
    def remove_ask(self, price):
        """Remove an ask"""
        if price in self.asks:
            del self.asks[price]
            self.last_update = datetime.now()
    
    def update_from_snapshot(self, bids, asks):
        """
        Update order book from snapshot
        
        Parameters:
        -----------
        bids : list of tuples
            List of (price, quantity) for bids
        asks : list of tuples
            List of (price, quantity) for asks
        """
        self.bids.clear()
        self.asks.clear()
        
        for price, quantity in bids:
            self.bids[price] = quantity
        
        for price, quantity in asks:
            self.asks[price] = quantity
        
        self.last_update = datetime.now()
    
    def best_bid(self):
        """Get best bid (highest price)"""
        if not self.bids:
            return None
        return max(self.bids.keys())
    
    def best_ask(self):
        """Get best ask (lowest price)"""
        if not self.asks:
            return None
        return min(self.asks.keys())
    
    def bid_ask_spread(self):
        """Calculate bid-ask spread"""
        best_bid = self.best_bid()
        best_ask = self.best_ask()
        
        if best_bid is None or best_ask is None:
            return None
        
        return best_ask - best_bid
    
    def mid_price(self):
        """Calculate mid price"""
        best_bid = self.best_bid()
        best_ask = self.best_ask()
        
        if best_bid is None or best_ask is None:
            return None
        
        return (best_bid + best_ask) / 2
    
    def get_bids(self, depth=10):
        """
        Get top bids sorted by price (descending)
        
        Parameters:
        -----------
        depth : int
            Number of levels to return
        
        Returns:
        --------
        list of tuples
            List of (price, quantity) sorted by price descending
        """
        sorted_bids = sorted(self.bids.items(), key=lambda x: x[0], reverse=True)
        return sorted_bids[:depth]
    
    def get_asks(self, depth=10):
        """
        Get top asks sorted by price (ascending)
        
        Parameters:
        -----------
        depth : int
            Number of levels to return
        
        Returns:
        --------
        list of tuples
            List of (price, quantity) sorted by price ascending
        """
        sorted_asks = sorted(self.asks.items(), key=lambda x: x[0])
        return sorted_asks[:depth]
    
    def liquidity_at_level(self, price, side='bid'):
        """Get liquidity available at a specific price level"""
        if side == 'bid':
            return self.bids.get(price, 0.0)
        else:
            return self.asks.get(price, 0.0)
    
    def total_liquidity(self, side='bid', depth=10):
        """Calculate total liquidity on one side of the book"""
        if side == 'bid':
            levels = self.get_bids(depth)
        else:
            levels = self.get_asks(depth)
        
        return sum(quantity for price, quantity in levels)
    
    def vwap(self, side='bid', depth=10):
        """
        Calculate Volume Weighted Average Price
        
        Parameters:
        -----------
        side : str
            'bid' or 'ask'
        depth : int
            Number of levels to include
        
        Returns:
        --------
        float
            VWAP or None if no liquidity
        """
        if side == 'bid':
            levels = self.get_bids(depth)
        else:
            levels = self.get_asks(depth)
        
        if not levels:
            return None
        
        total_value = sum(price * quantity for price, quantity in levels)
        total_volume = sum(quantity for price, quantity in levels)
        
        if total_volume == 0:
            return None
        
        return total_value / total_volume


class MarketDataFeed:
    """Simulated market data feed for testing"""
    
    def __init__(self, symbol, initial_price=100.0, volatility=0.2):
        """
        Initialize market data feed
        
        Parameters:
        -----------
        symbol : str
            Trading symbol
        initial_price : float
            Starting price
        volatility : float
            Price volatility for simulation
        """
        self.symbol = symbol
        self.current_price = initial_price
        self.volatility = volatility
        self.order_book = OrderBook(symbol)
        self.trade_history = []
    
    def generate_tick(self, dt=1/252):
        """
        Generate next price tick using geometric Brownian motion
        
        Parameters:
        -----------
        dt : float
            Time step (in years)
        
        Returns:
        --------
        float
            New price
        """
        # Geometric Brownian motion
        drift = 0.0  # Assume no drift for simplicity
        shock = np.random.normal(0, 1)
        
        self.current_price *= np.exp((drift - 0.5 * self.volatility**2) * dt + 
                                      self.volatility * np.sqrt(dt) * shock)
        
        # Update order book with new prices
        self._update_order_book()
        
        return self.current_price
    
    def _update_order_book(self):
        """Update order book based on current price"""
        # Generate simple order book around current price
        spread = self.current_price * 0.001  # 0.1% spread
        
        bid_price = self.current_price - spread / 2
        ask_price = self.current_price + spread / 2
        
        # Generate random quantities
        bids = [
            (bid_price, np.random.uniform(10, 100)),
            (bid_price - spread, np.random.uniform(20, 150)),
            (bid_price - 2 * spread, np.random.uniform(30, 200)),
        ]
        
        asks = [
            (ask_price, np.random.uniform(10, 100)),
            (ask_price + spread, np.random.uniform(20, 150)),
            (ask_price + 2 * spread, np.random.uniform(30, 200)),
        ]
        
        self.order_book.update_from_snapshot(bids, asks)
    
    def get_current_price(self):
        """Get current market price"""
        return self.current_price
    
    def get_order_book(self):
        """Get current order book"""
        return self.order_book
    
    def record_trade(self, price, quantity, side):
        """
        Record a trade
        
        Parameters:
        -----------
        price : float
            Trade price
        quantity : float
            Trade quantity
        side : str
            'buy' or 'sell'
        """
        trade = {
            'timestamp': datetime.now(),
            'price': price,
            'quantity': quantity,
            'side': side
        }
        self.trade_history.append(trade)
    
    def get_trades(self, limit=100):
        """Get recent trades"""
        return self.trade_history[-limit:]


class OptionChainData:
    """Container for option chain data"""
    
    def __init__(self, underlying_symbol, underlying_price):
        """
        Initialize option chain
        
        Parameters:
        -----------
        underlying_symbol : str
            Symbol of underlying asset
        underlying_price : float
            Current price of underlying
        """
        self.underlying_symbol = underlying_symbol
        self.underlying_price = underlying_price
        self.options = []
    
    def add_option(self, strike, expiry, option_type, bid, ask, volume=0, open_interest=0):
        """
        Add option to chain
        
        Parameters:
        -----------
        strike : float
            Strike price
        expiry : float
            Time to expiration (years)
        option_type : str
            'call' or 'put'
        bid : float
            Bid price
        ask : float
            Ask price
        volume : int
            Trading volume
        open_interest : int
            Open interest
        """
        option = {
            'strike': strike,
            'expiry': expiry,
            'type': option_type,
            'bid': bid,
            'ask': ask,
            'mid': (bid + ask) / 2,
            'spread': ask - bid,
            'volume': volume,
            'open_interest': open_interest,
            'moneyness': strike / self.underlying_price
        }
        self.options.append(option)
    
    def get_options(self, option_type=None, min_expiry=None, max_expiry=None):
        """
        Filter options by criteria
        
        Parameters:
        -----------
        option_type : str, optional
            Filter by 'call' or 'put'
        min_expiry : float, optional
            Minimum time to expiration
        max_expiry : float, optional
            Maximum time to expiration
        
        Returns:
        --------
        list
            Filtered list of options
        """
        filtered = self.options
        
        if option_type:
            filtered = [opt for opt in filtered if opt['type'] == option_type]
        
        if min_expiry is not None:
            filtered = [opt for opt in filtered if opt['expiry'] >= min_expiry]
        
        if max_expiry is not None:
            filtered = [opt for opt in filtered if opt['expiry'] <= max_expiry]
        
        return filtered
    
    def find_mispriced_options(self, theoretical_prices, threshold=0.05):
        """
        Find potentially mispriced options
        
        Parameters:
        -----------
        theoretical_prices : dict
            Dictionary mapping (strike, expiry, type) to theoretical price
        threshold : float
            Minimum price difference to consider mispriced (as fraction)
        
        Returns:
        --------
        list
            List of mispriced options with details
        """
        mispriced = []
        
        for option in self.options:
            key = (option['strike'], option['expiry'], option['type'])
            
            if key in theoretical_prices:
                theoretical = theoretical_prices[key]
                market_mid = option['mid']
                
                if theoretical > 0:
                    diff_pct = abs(market_mid - theoretical) / theoretical
                    
                    if diff_pct > threshold:
                        mispriced.append({
                            'option': option,
                            'theoretical_price': theoretical,
                            'market_price': market_mid,
                            'difference_pct': diff_pct,
                            'overpriced': market_mid > theoretical
                        })
        
        return mispriced
