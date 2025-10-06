"""
Technical Indicators Module

This module provides common technical indicators for momentum trading.
"""

import numpy as np


def simple_moving_average(prices, window):
    """
    Calculate Simple Moving Average (SMA)
    
    Parameters:
    -----------
    prices : array-like
        Price series
    window : int
        Window size
    
    Returns:
    --------
    array
        SMA values
    """
    prices = np.array(prices)
    sma = np.convolve(prices, np.ones(window), 'valid') / window
    return sma


def exponential_moving_average(prices, window):
    """
    Calculate Exponential Moving Average (EMA)
    
    Parameters:
    -----------
    prices : array-like
        Price series
    window : int
        Window size
    
    Returns:
    --------
    array
        EMA values
    """
    prices = np.array(prices)
    alpha = 2 / (window + 1)
    ema = np.zeros(len(prices))
    ema[0] = prices[0]
    
    for i in range(1, len(prices)):
        ema[i] = alpha * prices[i] + (1 - alpha) * ema[i-1]
    
    return ema


def rsi(prices, window=14):
    """
    Calculate Relative Strength Index (RSI)
    
    Parameters:
    -----------
    prices : array-like
        Price series
    window : int
        Lookback window (typically 14)
    
    Returns:
    --------
    array
        RSI values (0-100)
    """
    prices = np.array(prices)
    deltas = np.diff(prices)
    
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gains = np.zeros(len(prices))
    avg_losses = np.zeros(len(prices))
    
    # Initial average
    avg_gains[window] = np.mean(gains[:window])
    avg_losses[window] = np.mean(losses[:window])
    
    # Smoothed averages
    for i in range(window + 1, len(prices)):
        avg_gains[i] = (avg_gains[i-1] * (window - 1) + gains[i-1]) / window
        avg_losses[i] = (avg_losses[i-1] * (window - 1) + losses[i-1]) / window
    
    rs = np.divide(avg_gains, avg_losses, out=np.zeros_like(avg_gains), where=avg_losses!=0)
    rsi_values = 100 - (100 / (1 + rs))
    
    return rsi_values


def macd(prices, fast_period=12, slow_period=26, signal_period=9):
    """
    Calculate MACD (Moving Average Convergence Divergence)
    
    Parameters:
    -----------
    prices : array-like
        Price series
    fast_period : int
        Fast EMA period
    slow_period : int
        Slow EMA period
    signal_period : int
        Signal line EMA period
    
    Returns:
    --------
    dict
        Dictionary with 'macd', 'signal', and 'histogram' arrays
    """
    prices = np.array(prices)
    
    fast_ema = exponential_moving_average(prices, fast_period)
    slow_ema = exponential_moving_average(prices, slow_period)
    
    # MACD line
    macd_line = fast_ema - slow_ema
    
    # Signal line
    signal_line = exponential_moving_average(macd_line, signal_period)
    
    # Histogram
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }


def bollinger_bands(prices, window=20, num_std=2):
    """
    Calculate Bollinger Bands
    
    Parameters:
    -----------
    prices : array-like
        Price series
    window : int
        Window size for moving average
    num_std : float
        Number of standard deviations for bands
    
    Returns:
    --------
    dict
        Dictionary with 'upper', 'middle', and 'lower' bands
    """
    prices = np.array(prices)
    
    middle_band = simple_moving_average(prices, window)
    
    # Calculate rolling standard deviation
    std_dev = np.zeros(len(prices) - window + 1)
    for i in range(len(std_dev)):
        std_dev[i] = np.std(prices[i:i+window])
    
    upper_band = middle_band + (num_std * std_dev)
    lower_band = middle_band - (num_std * std_dev)
    
    return {
        'upper': upper_band,
        'middle': middle_band,
        'lower': lower_band
    }


def stochastic_oscillator(highs, lows, closes, k_period=14, d_period=3):
    """
    Calculate Stochastic Oscillator
    
    Parameters:
    -----------
    highs : array-like
        High prices
    lows : array-like
        Low prices
    closes : array-like
        Close prices
    k_period : int
        %K period
    d_period : int
        %D period (smoothing)
    
    Returns:
    --------
    dict
        Dictionary with 'k' and 'd' values
    """
    highs = np.array(highs)
    lows = np.array(lows)
    closes = np.array(closes)
    
    k_values = np.zeros(len(closes))
    
    for i in range(k_period - 1, len(closes)):
        highest_high = np.max(highs[i-k_period+1:i+1])
        lowest_low = np.min(lows[i-k_period+1:i+1])
        
        if highest_high != lowest_low:
            k_values[i] = 100 * (closes[i] - lowest_low) / (highest_high - lowest_low)
        else:
            k_values[i] = 50
    
    # %D is SMA of %K
    d_values = simple_moving_average(k_values[k_period-1:], d_period)
    
    return {
        'k': k_values,
        'd': d_values
    }


def atr(highs, lows, closes, window=14):
    """
    Calculate Average True Range (ATR)
    
    Parameters:
    -----------
    highs : array-like
        High prices
    lows : array-like
        Low prices
    closes : array-like
        Close prices
    window : int
        Window size
    
    Returns:
    --------
    array
        ATR values
    """
    highs = np.array(highs)
    lows = np.array(lows)
    closes = np.array(closes)
    
    # True Range calculation
    tr = np.zeros(len(closes))
    tr[0] = highs[0] - lows[0]
    
    for i in range(1, len(closes)):
        tr[i] = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i-1]),
            abs(lows[i] - closes[i-1])
        )
    
    # ATR is EMA of True Range
    atr_values = exponential_moving_average(tr, window)
    
    return atr_values


def adx(highs, lows, closes, window=14):
    """
    Calculate Average Directional Index (ADX)
    
    Parameters:
    -----------
    highs : array-like
        High prices
    lows : array-like
        Low prices
    closes : array-like
        Close prices
    window : int
        Window size
    
    Returns:
    --------
    dict
        Dictionary with 'adx', 'plus_di', and 'minus_di'
    """
    highs = np.array(highs)
    lows = np.array(lows)
    closes = np.array(closes)
    
    # Calculate +DM and -DM
    plus_dm = np.zeros(len(highs))
    minus_dm = np.zeros(len(highs))
    
    for i in range(1, len(highs)):
        high_diff = highs[i] - highs[i-1]
        low_diff = lows[i-1] - lows[i]
        
        if high_diff > low_diff and high_diff > 0:
            plus_dm[i] = high_diff
        if low_diff > high_diff and low_diff > 0:
            minus_dm[i] = low_diff
    
    # Calculate True Range
    tr_values = atr(highs, lows, closes, window)
    
    # Calculate smoothed +DM and -DM
    smoothed_plus_dm = exponential_moving_average(plus_dm, window)
    smoothed_minus_dm = exponential_moving_average(minus_dm, window)
    
    # Calculate +DI and -DI
    plus_di = 100 * smoothed_plus_dm / tr_values
    minus_di = 100 * smoothed_minus_dm / tr_values
    
    # Calculate DX and ADX
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
    adx_values = exponential_moving_average(dx, window)
    
    return {
        'adx': adx_values,
        'plus_di': plus_di,
        'minus_di': minus_di
    }


def obv(closes, volumes):
    """
    Calculate On-Balance Volume (OBV)
    
    Parameters:
    -----------
    closes : array-like
        Close prices
    volumes : array-like
        Trading volumes
    
    Returns:
    --------
    array
        OBV values
    """
    closes = np.array(closes)
    volumes = np.array(volumes)
    
    obv_values = np.zeros(len(closes))
    obv_values[0] = volumes[0]
    
    for i in range(1, len(closes)):
        if closes[i] > closes[i-1]:
            obv_values[i] = obv_values[i-1] + volumes[i]
        elif closes[i] < closes[i-1]:
            obv_values[i] = obv_values[i-1] - volumes[i]
        else:
            obv_values[i] = obv_values[i-1]
    
    return obv_values


def momentum(prices, window=10):
    """
    Calculate price momentum
    
    Parameters:
    -----------
    prices : array-like
        Price series
    window : int
        Lookback window
    
    Returns:
    --------
    array
        Momentum values
    """
    prices = np.array(prices)
    momentum_values = np.zeros(len(prices))
    
    for i in range(window, len(prices)):
        momentum_values[i] = prices[i] - prices[i - window]
    
    return momentum_values


def rate_of_change(prices, window=10):
    """
    Calculate Rate of Change (ROC)
    
    Parameters:
    -----------
    prices : array-like
        Price series
    window : int
        Lookback window
    
    Returns:
    --------
    array
        ROC values (percentage)
    """
    prices = np.array(prices)
    roc_values = np.zeros(len(prices))
    
    for i in range(window, len(prices)):
        if prices[i - window] != 0:
            roc_values[i] = 100 * (prices[i] - prices[i - window]) / prices[i - window]
    
    return roc_values
