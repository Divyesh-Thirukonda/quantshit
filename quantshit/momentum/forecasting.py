"""
Time Series Forecasting Module

This module provides functions for forecasting price movements.
"""

import numpy as np
from scipy.optimize import minimize


def simple_forecast(prices, horizon=1, method='last'):
    """
    Simple forecasting methods
    
    Parameters:
    -----------
    prices : array-like
        Historical prices
    horizon : int
        Number of periods to forecast
    method : str
        'last' (use last price) or 'mean' (use average)
    
    Returns:
    --------
    array
        Forecasted prices
    """
    prices = np.array(prices)
    
    if method == 'last':
        forecast = np.full(horizon, prices[-1])
    elif method == 'mean':
        forecast = np.full(horizon, np.mean(prices))
    else:
        raise ValueError("method must be 'last' or 'mean'")
    
    return forecast


def moving_average_forecast(prices, window=20, horizon=1):
    """
    Forecast using moving average
    
    Parameters:
    -----------
    prices : array-like
        Historical prices
    window : int
        Window size for MA
    horizon : int
        Number of periods to forecast
    
    Returns:
    --------
    array
        Forecasted prices
    """
    prices = np.array(prices)
    ma = np.mean(prices[-window:])
    forecast = np.full(horizon, ma)
    return forecast


def exponential_smoothing(prices, alpha=0.3, horizon=1):
    """
    Forecast using exponential smoothing
    
    Parameters:
    -----------
    prices : array-like
        Historical prices
    alpha : float
        Smoothing parameter (0 to 1)
    horizon : int
        Number of periods to forecast
    
    Returns:
    --------
    array
        Forecasted prices
    """
    prices = np.array(prices)
    
    # Calculate current smoothed value
    smoothed = prices[0]
    for price in prices[1:]:
        smoothed = alpha * price + (1 - alpha) * smoothed
    
    # Forecast is the last smoothed value
    forecast = np.full(horizon, smoothed)
    return forecast


def linear_regression_forecast(prices, horizon=1):
    """
    Forecast using linear regression
    
    Parameters:
    -----------
    prices : array-like
        Historical prices
    horizon : int
        Number of periods to forecast
    
    Returns:
    --------
    array
        Forecasted prices
    """
    prices = np.array(prices)
    x = np.arange(len(prices))
    
    # Fit linear regression
    coeffs = np.polyfit(x, prices, 1)
    
    # Forecast future values
    future_x = np.arange(len(prices), len(prices) + horizon)
    forecast = np.polyval(coeffs, future_x)
    
    return forecast


def polynomial_regression_forecast(prices, degree=2, horizon=1):
    """
    Forecast using polynomial regression
    
    Parameters:
    -----------
    prices : array-like
        Historical prices
    degree : int
        Polynomial degree
    horizon : int
        Number of periods to forecast
    
    Returns:
    --------
    array
        Forecasted prices
    """
    prices = np.array(prices)
    x = np.arange(len(prices))
    
    # Fit polynomial regression
    coeffs = np.polyfit(x, prices, degree)
    
    # Forecast future values
    future_x = np.arange(len(prices), len(prices) + horizon)
    forecast = np.polyval(coeffs, future_x)
    
    return forecast


def arima_simple(prices, p=1, d=1, q=1, horizon=1):
    """
    Simplified ARIMA-like forecast
    
    Parameters:
    -----------
    prices : array-like
        Historical prices
    p : int
        Autoregressive order
    d : int
        Differencing order
    q : int
        Moving average order
    horizon : int
        Number of periods to forecast
    
    Returns:
    --------
    array
        Forecasted prices
    """
    prices = np.array(prices)
    
    # Apply differencing
    diff_prices = prices.copy()
    for _ in range(d):
        diff_prices = np.diff(diff_prices)
    
    # Simple AR forecast on differenced data
    if len(diff_prices) < p:
        # Fallback to last value
        return np.full(horizon, prices[-1])
    
    # Use last p values to forecast
    forecast_diff = []
    current_values = list(diff_prices[-p:])
    
    for _ in range(horizon):
        # Simple average of last p values
        next_val = np.mean(current_values)
        forecast_diff.append(next_val)
        current_values = current_values[1:] + [next_val]
    
    # Inverse differencing
    forecast = forecast_diff
    for _ in range(d):
        cumsum = prices[-1]
        integrated = []
        for val in forecast:
            cumsum += val
            integrated.append(cumsum)
        forecast = integrated
    
    return np.array(forecast)


class MomentumForecaster:
    """Forecaster based on momentum signals"""
    
    def __init__(self, prices):
        """
        Initialize momentum forecaster
        
        Parameters:
        -----------
        prices : array-like
            Historical prices
        """
        self.prices = np.array(prices)
    
    def forecast_with_momentum(self, horizon=1, momentum_window=10):
        """
        Forecast using price momentum
        
        Parameters:
        -----------
        horizon : int
            Number of periods to forecast
        momentum_window : int
            Window for calculating momentum
        
        Returns:
        --------
        dict
            Forecast with confidence metrics
        """
        if len(self.prices) < momentum_window:
            return {
                'forecast': np.full(horizon, self.prices[-1]),
                'confidence': 0,
                'direction': 'neutral'
            }
        
        # Calculate momentum
        momentum = self.prices[-1] - self.prices[-momentum_window]
        avg_change = momentum / momentum_window
        
        # Forecast by extending momentum
        forecast = []
        last_price = self.prices[-1]
        
        for i in range(horizon):
            next_price = last_price + avg_change
            forecast.append(next_price)
            last_price = next_price
        
        # Calculate confidence based on consistency
        recent_changes = np.diff(self.prices[-momentum_window:])
        consistency = np.sum(np.sign(recent_changes) == np.sign(avg_change)) / len(recent_changes)
        
        direction = 'bullish' if avg_change > 0 else 'bearish' if avg_change < 0 else 'neutral'
        
        return {
            'forecast': np.array(forecast),
            'confidence': consistency,
            'direction': direction,
            'avg_change': avg_change
        }
    
    def forecast_with_trend(self, horizon=1, fast_ma=10, slow_ma=20):
        """
        Forecast using trend analysis
        
        Parameters:
        -----------
        horizon : int
            Number of periods to forecast
        fast_ma : int
            Fast moving average window
        slow_ma : int
            Slow moving average window
        
        Returns:
        --------
        dict
            Forecast with trend information
        """
        if len(self.prices) < slow_ma:
            return {
                'forecast': np.full(horizon, self.prices[-1]),
                'trend': 'neutral'
            }
        
        # Calculate moving averages
        fast_avg = np.mean(self.prices[-fast_ma:])
        slow_avg = np.mean(self.prices[-slow_ma:])
        
        # Determine trend
        if fast_avg > slow_avg:
            trend = 'bullish'
            momentum = fast_avg - slow_avg
        elif fast_avg < slow_avg:
            trend = 'bearish'
            momentum = fast_avg - slow_avg
        else:
            trend = 'neutral'
            momentum = 0
        
        # Forecast by extending trend
        forecast = []
        last_price = self.prices[-1]
        
        for i in range(horizon):
            next_price = last_price + momentum * 0.1  # Scale momentum
            forecast.append(next_price)
            last_price = next_price
        
        return {
            'forecast': np.array(forecast),
            'trend': trend,
            'momentum': momentum
        }


def ensemble_forecast(prices, horizon=1, methods=None):
    """
    Combine multiple forecasting methods
    
    Parameters:
    -----------
    prices : array-like
        Historical prices
    horizon : int
        Number of periods to forecast
    methods : list, optional
        List of forecasting methods to use
    
    Returns:
    --------
    dict
        Ensemble forecast with individual predictions
    """
    if methods is None:
        methods = ['linear', 'exponential', 'ma']
    
    forecasts = {}
    
    if 'linear' in methods:
        forecasts['linear'] = linear_regression_forecast(prices, horizon)
    
    if 'exponential' in methods:
        forecasts['exponential'] = exponential_smoothing(prices, horizon=horizon)
    
    if 'ma' in methods:
        forecasts['ma'] = moving_average_forecast(prices, horizon=horizon)
    
    if 'polynomial' in methods:
        forecasts['polynomial'] = polynomial_regression_forecast(prices, horizon=horizon)
    
    # Ensemble as average
    all_forecasts = np.array(list(forecasts.values()))
    ensemble = np.mean(all_forecasts, axis=0)
    
    # Calculate variance as measure of uncertainty
    variance = np.var(all_forecasts, axis=0)
    
    return {
        'ensemble': ensemble,
        'individual_forecasts': forecasts,
        'variance': variance,
        'uncertainty': np.sqrt(variance)
    }


def forecast_confidence_interval(prices, horizon=1, confidence=0.95):
    """
    Calculate confidence interval for forecast
    
    Parameters:
    -----------
    prices : array-like
        Historical prices
    horizon : int
        Number of periods to forecast
    confidence : float
        Confidence level (e.g., 0.95 for 95%)
    
    Returns:
    --------
    dict
        Forecast with confidence intervals
    """
    prices = np.array(prices)
    
    # Use linear regression for point forecast
    point_forecast = linear_regression_forecast(prices, horizon)
    
    # Calculate historical volatility
    returns = np.diff(prices) / prices[:-1]
    volatility = np.std(returns)
    
    # Calculate prediction error (simplified)
    # In practice, would use residuals from model fit
    z_score = 1.96 if confidence == 0.95 else 2.576  # For 95% or 99%
    
    margin = z_score * volatility * np.sqrt(np.arange(1, horizon + 1))
    
    upper_bound = point_forecast + margin * point_forecast
    lower_bound = point_forecast - margin * point_forecast
    
    return {
        'forecast': point_forecast,
        'upper_bound': upper_bound,
        'lower_bound': lower_bound,
        'confidence': confidence
    }
