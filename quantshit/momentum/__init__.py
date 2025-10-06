"""
Momentum Trading Module

This module provides functionality for momentum trading and trend following.
"""

from .indicators import (
    simple_moving_average,
    exponential_moving_average,
    rsi,
    macd,
    bollinger_bands,
    stochastic_oscillator,
    atr,
    adx,
    obv,
    momentum,
    rate_of_change
)
from .trend_detection import (
    TrendDetector,
    detect_breakout,
    trend_strength,
    identify_pattern
)
from .forecasting import (
    simple_forecast,
    moving_average_forecast,
    exponential_smoothing,
    linear_regression_forecast,
    polynomial_regression_forecast,
    arima_simple,
    MomentumForecaster,
    ensemble_forecast,
    forecast_confidence_interval
)

__all__ = [
    # Indicators
    'simple_moving_average',
    'exponential_moving_average',
    'rsi',
    'macd',
    'bollinger_bands',
    'stochastic_oscillator',
    'atr',
    'adx',
    'obv',
    'momentum',
    'rate_of_change',
    # Trend detection
    'TrendDetector',
    'detect_breakout',
    'trend_strength',
    'identify_pattern',
    # Forecasting
    'simple_forecast',
    'moving_average_forecast',
    'exponential_smoothing',
    'linear_regression_forecast',
    'polynomial_regression_forecast',
    'arima_simple',
    'MomentumForecaster',
    'ensemble_forecast',
    'forecast_confidence_interval'
]
