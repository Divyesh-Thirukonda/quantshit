"""
Trend Detection Module

This module provides functions for detecting and analyzing trends in price data.
"""

import numpy as np
from scipy import stats
from .indicators import simple_moving_average, exponential_moving_average


class TrendDetector:
    """Detects trends in price data"""
    
    def __init__(self, prices):
        """
        Initialize trend detector
        
        Parameters:
        -----------
        prices : array-like
            Price series
        """
        self.prices = np.array(prices)
    
    def linear_regression_trend(self, window=None):
        """
        Detect trend using linear regression
        
        Parameters:
        -----------
        window : int, optional
            Window size (uses all data if None)
        
        Returns:
        --------
        dict
            Trend information including slope, r-squared, and direction
        """
        if window is None:
            window = len(self.prices)
        
        prices_window = self.prices[-window:]
        x = np.arange(len(prices_window))
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, prices_window)
        
        return {
            'slope': slope,
            'intercept': intercept,
            'r_squared': r_value ** 2,
            'p_value': p_value,
            'std_err': std_err,
            'direction': 'uptrend' if slope > 0 else 'downtrend',
            'strength': abs(r_value)
        }
    
    def moving_average_trend(self, fast_window=20, slow_window=50):
        """
        Detect trend using moving average crossover
        
        Parameters:
        -----------
        fast_window : int
            Fast MA window
        slow_window : int
            Slow MA window
        
        Returns:
        --------
        dict
            Trend signal based on MA crossover
        """
        fast_ma = simple_moving_average(self.prices, fast_window)
        slow_ma = simple_moving_average(self.prices, slow_window)
        
        if len(fast_ma) < 2 or len(slow_ma) < 2:
            return {'signal': 'neutral', 'strength': 0}
        
        # Current position
        current_fast = fast_ma[-1]
        current_slow = slow_ma[-1]
        
        # Previous position
        prev_fast = fast_ma[-2]
        prev_slow = slow_ma[-2]
        
        # Determine signal
        if current_fast > current_slow:
            signal = 'bullish'
            strength = (current_fast - current_slow) / current_slow
        else:
            signal = 'bearish'
            strength = (current_slow - current_fast) / current_fast
        
        # Check for crossover
        crossover = None
        if prev_fast <= prev_slow and current_fast > current_slow:
            crossover = 'golden_cross'  # Bullish
        elif prev_fast >= prev_slow and current_fast < current_slow:
            crossover = 'death_cross'  # Bearish
        
        return {
            'signal': signal,
            'strength': strength,
            'crossover': crossover,
            'fast_ma': current_fast,
            'slow_ma': current_slow
        }
    
    def higher_highs_higher_lows(self, window=10):
        """
        Detect uptrend by checking for higher highs and higher lows
        
        Parameters:
        -----------
        window : int
            Window size for comparison
        
        Returns:
        --------
        dict
            Trend information
        """
        if len(self.prices) < window * 2:
            return {'trend': 'insufficient_data'}
        
        # Split into two periods
        first_period = self.prices[-(window*2):-window]
        second_period = self.prices[-window:]
        
        first_high = np.max(first_period)
        first_low = np.min(first_period)
        
        second_high = np.max(second_period)
        second_low = np.min(second_period)
        
        higher_high = second_high > first_high
        higher_low = second_low > first_low
        lower_high = second_high < first_high
        lower_low = second_low < first_low
        
        if higher_high and higher_low:
            trend = 'strong_uptrend'
        elif higher_high or higher_low:
            trend = 'weak_uptrend'
        elif lower_high and lower_low:
            trend = 'strong_downtrend'
        elif lower_high or lower_low:
            trend = 'weak_downtrend'
        else:
            trend = 'sideways'
        
        return {
            'trend': trend,
            'higher_high': higher_high,
            'higher_low': higher_low,
            'lower_high': lower_high,
            'lower_low': lower_low
        }
    
    def support_resistance_levels(self, num_levels=3, tolerance=0.02):
        """
        Identify support and resistance levels
        
        Parameters:
        -----------
        num_levels : int
            Number of levels to identify
        tolerance : float
            Price tolerance for clustering (as fraction)
        
        Returns:
        --------
        dict
            Support and resistance levels
        """
        # Find local maxima and minima
        highs = []
        lows = []
        
        for i in range(1, len(self.prices) - 1):
            if self.prices[i] > self.prices[i-1] and self.prices[i] > self.prices[i+1]:
                highs.append(self.prices[i])
            if self.prices[i] < self.prices[i-1] and self.prices[i] < self.prices[i+1]:
                lows.append(self.prices[i])
        
        # Cluster similar levels
        def cluster_levels(levels, tolerance):
            if not levels:
                return []
            
            levels = sorted(levels)
            clusters = []
            current_cluster = [levels[0]]
            
            for level in levels[1:]:
                if abs(level - current_cluster[-1]) / current_cluster[-1] <= tolerance:
                    current_cluster.append(level)
                else:
                    clusters.append(np.mean(current_cluster))
                    current_cluster = [level]
            
            clusters.append(np.mean(current_cluster))
            return clusters
        
        resistance_levels = cluster_levels(highs, tolerance)
        support_levels = cluster_levels(lows, tolerance)
        
        # Sort and take top levels
        resistance_levels = sorted(resistance_levels, reverse=True)[:num_levels]
        support_levels = sorted(support_levels)[:num_levels]
        
        return {
            'resistance': resistance_levels,
            'support': support_levels,
            'current_price': self.prices[-1]
        }


def detect_breakout(prices, resistance_level, support_level, threshold=0.01):
    """
    Detect breakout from support/resistance levels
    
    Parameters:
    -----------
    prices : array-like
        Recent price series
    resistance_level : float
        Resistance level
    support_level : float
        Support level
    threshold : float
        Breakout threshold (as fraction)
    
    Returns:
    --------
    dict
        Breakout information
    """
    prices = np.array(prices)
    current_price = prices[-1]
    
    resistance_breakout = current_price > resistance_level * (1 + threshold)
    support_breakout = current_price < support_level * (1 - threshold)
    
    if resistance_breakout:
        return {
            'breakout': True,
            'direction': 'upward',
            'level': resistance_level,
            'current_price': current_price
        }
    elif support_breakout:
        return {
            'breakout': True,
            'direction': 'downward',
            'level': support_level,
            'current_price': current_price
        }
    else:
        return {
            'breakout': False,
            'direction': 'none',
            'current_price': current_price
        }


def trend_strength(prices, window=20):
    """
    Calculate trend strength using ADX-like approach
    
    Parameters:
    -----------
    prices : array-like
        Price series
    window : int
        Window size
    
    Returns:
    --------
    float
        Trend strength (0-100)
    """
    prices = np.array(prices)
    
    if len(prices) < window + 1:
        return 0
    
    # Calculate directional movements
    up_moves = []
    down_moves = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            up_moves.append(change)
            down_moves.append(0)
        else:
            up_moves.append(0)
            down_moves.append(abs(change))
    
    # Calculate average directional movement
    up_moves = np.array(up_moves)
    down_moves = np.array(down_moves)
    
    avg_up = np.mean(up_moves[-window:])
    avg_down = np.mean(down_moves[-window:])
    
    total_movement = avg_up + avg_down
    if total_movement == 0:
        return 0
    
    # Trend strength as percentage
    strength = 100 * abs(avg_up - avg_down) / total_movement
    
    return strength


def identify_pattern(prices, pattern_type='double_top', tolerance=0.02):
    """
    Identify common chart patterns
    
    Parameters:
    -----------
    prices : array-like
        Price series
    pattern_type : str
        Type of pattern to detect
    tolerance : float
        Tolerance for pattern matching
    
    Returns:
    --------
    dict
        Pattern detection result
    """
    prices = np.array(prices)
    
    if pattern_type == 'double_top':
        return _detect_double_top(prices, tolerance)
    elif pattern_type == 'double_bottom':
        return _detect_double_bottom(prices, tolerance)
    elif pattern_type == 'head_shoulders':
        return _detect_head_shoulders(prices, tolerance)
    else:
        return {'detected': False, 'message': 'Unknown pattern type'}


def _detect_double_top(prices, tolerance):
    """Detect double top pattern"""
    if len(prices) < 5:
        return {'detected': False, 'message': 'Insufficient data'}
    
    # Find peaks
    peaks = []
    for i in range(2, len(prices) - 2):
        if (prices[i] > prices[i-1] and prices[i] > prices[i-2] and
            prices[i] > prices[i+1] and prices[i] > prices[i+2]):
            peaks.append((i, prices[i]))
    
    # Check for two similar peaks
    for i in range(len(peaks) - 1):
        for j in range(i + 1, len(peaks)):
            peak1_idx, peak1_val = peaks[i]
            peak2_idx, peak2_val = peaks[j]
            
            if abs(peak1_val - peak2_val) / peak1_val <= tolerance:
                # Found potential double top
                valley_prices = prices[peak1_idx:peak2_idx+1]
                valley_val = np.min(valley_prices)
                
                return {
                    'detected': True,
                    'pattern': 'double_top',
                    'peak1': peak1_val,
                    'peak2': peak2_val,
                    'valley': valley_val,
                    'signal': 'bearish'
                }
    
    return {'detected': False, 'message': 'No double top pattern found'}


def _detect_double_bottom(prices, tolerance):
    """Detect double bottom pattern"""
    if len(prices) < 5:
        return {'detected': False, 'message': 'Insufficient data'}
    
    # Find troughs
    troughs = []
    for i in range(2, len(prices) - 2):
        if (prices[i] < prices[i-1] and prices[i] < prices[i-2] and
            prices[i] < prices[i+1] and prices[i] < prices[i+2]):
            troughs.append((i, prices[i]))
    
    # Check for two similar troughs
    for i in range(len(troughs) - 1):
        for j in range(i + 1, len(troughs)):
            trough1_idx, trough1_val = troughs[i]
            trough2_idx, trough2_val = troughs[j]
            
            if abs(trough1_val - trough2_val) / trough1_val <= tolerance:
                # Found potential double bottom
                peak_prices = prices[trough1_idx:trough2_idx+1]
                peak_val = np.max(peak_prices)
                
                return {
                    'detected': True,
                    'pattern': 'double_bottom',
                    'trough1': trough1_val,
                    'trough2': trough2_val,
                    'peak': peak_val,
                    'signal': 'bullish'
                }
    
    return {'detected': False, 'message': 'No double bottom pattern found'}


def _detect_head_shoulders(prices, tolerance):
    """Detect head and shoulders pattern"""
    # Simplified detection - would need more sophisticated logic for production
    return {'detected': False, 'message': 'Head and shoulders detection not fully implemented'}
