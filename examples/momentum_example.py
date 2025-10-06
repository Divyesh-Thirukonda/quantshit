"""
Momentum Trading Example

This example demonstrates how to use the momentum module for trend following
and time series forecasting.
"""

import numpy as np
from quantshit.momentum import (
    simple_moving_average,
    exponential_moving_average,
    rsi,
    macd,
    bollinger_bands,
    TrendDetector,
    detect_breakout,
    MomentumForecaster,
    ensemble_forecast,
    forecast_confidence_interval
)


def example_moving_averages():
    """Example: Calculate moving averages"""
    print("=" * 60)
    print("Moving Averages Example")
    print("=" * 60)
    
    # Generate sample price data
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.normal(0.1, 1, 100))
    
    # Calculate moving averages
    sma_20 = simple_moving_average(prices, window=20)
    ema_20 = exponential_moving_average(prices, window=20)
    
    print(f"\nCurrent Price: ${prices[-1]:.2f}")
    print(f"20-day SMA: ${sma_20[-1]:.2f}")
    print(f"20-day EMA: ${ema_20[-1]:.2f}")
    
    # Trading signal
    if prices[-1] > sma_20[-1]:
        print("\nSignal: BULLISH (Price above SMA)")
    else:
        print("\nSignal: BEARISH (Price below SMA)")


def example_rsi():
    """Example: Calculate RSI indicator"""
    print("\n" + "=" * 60)
    print("RSI Indicator Example")
    print("=" * 60)
    
    # Generate trending price data
    np.random.seed(42)
    trend = np.linspace(0, 10, 50)
    noise = np.random.normal(0, 2, 50)
    prices = 100 + trend + noise
    
    # Calculate RSI
    rsi_values = rsi(prices, window=14)
    current_rsi = rsi_values[-1]
    
    print(f"\nCurrent RSI: {current_rsi:.2f}")
    
    # Interpret RSI
    if current_rsi > 70:
        print("Signal: OVERBOUGHT - Consider selling")
    elif current_rsi < 30:
        print("Signal: OVERSOLD - Consider buying")
    else:
        print("Signal: NEUTRAL - No strong signal")


def example_macd():
    """Example: Calculate MACD indicator"""
    print("\n" + "=" * 60)
    print("MACD Indicator Example")
    print("=" * 60)
    
    # Generate sample data
    np.random.seed(42)
    prices = 100 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, 100)))
    
    # Calculate MACD
    macd_data = macd(prices)
    
    current_macd = macd_data['macd'][-1]
    current_signal = macd_data['signal'][-1]
    current_histogram = macd_data['histogram'][-1]
    
    print(f"\nMACD Line: {current_macd:.4f}")
    print(f"Signal Line: {current_signal:.4f}")
    print(f"Histogram: {current_histogram:.4f}")
    
    # Interpret MACD
    if current_macd > current_signal and current_histogram > 0:
        print("\nSignal: BULLISH (MACD above signal)")
    elif current_macd < current_signal and current_histogram < 0:
        print("\nSignal: BEARISH (MACD below signal)")
    else:
        print("\nSignal: NEUTRAL")


def example_bollinger_bands():
    """Example: Calculate Bollinger Bands"""
    print("\n" + "=" * 60)
    print("Bollinger Bands Example")
    print("=" * 60)
    
    # Generate sample data
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.normal(0, 1, 50))
    
    # Calculate Bollinger Bands
    bb = bollinger_bands(prices, window=20, num_std=2)
    
    current_price = prices[-1]
    upper_band = bb['upper'][-1]
    middle_band = bb['middle'][-1]
    lower_band = bb['lower'][-1]
    
    print(f"\nCurrent Price: ${current_price:.2f}")
    print(f"Upper Band: ${upper_band:.2f}")
    print(f"Middle Band: ${middle_band:.2f}")
    print(f"Lower Band: ${lower_band:.2f}")
    
    # Interpret position
    if current_price > upper_band:
        print("\nSignal: Price above upper band - Potentially overbought")
    elif current_price < lower_band:
        print("\nSignal: Price below lower band - Potentially oversold")
    else:
        print("\nSignal: Price within bands - Normal range")


def example_trend_detection():
    """Example: Detect trends in price data"""
    print("\n" + "=" * 60)
    print("Trend Detection Example")
    print("=" * 60)
    
    # Generate uptrending data
    np.random.seed(42)
    trend = np.linspace(0, 20, 100)
    noise = np.random.normal(0, 2, 100)
    prices = 100 + trend + noise
    
    # Create trend detector
    detector = TrendDetector(prices)
    
    # Linear regression trend
    lr_trend = detector.linear_regression_trend(window=50)
    print(f"\nLinear Regression Trend:")
    print(f"  Direction: {lr_trend['direction']}")
    print(f"  Slope: {lr_trend['slope']:.4f}")
    print(f"  R-squared: {lr_trend['r_squared']:.4f}")
    print(f"  Strength: {lr_trend['strength']:.4f}")
    
    # Moving average trend
    ma_trend = detector.moving_average_trend(fast_window=20, slow_window=50)
    print(f"\nMoving Average Trend:")
    print(f"  Signal: {ma_trend['signal']}")
    print(f"  Strength: {ma_trend['strength']*100:.2f}%")
    if ma_trend['crossover']:
        print(f"  Crossover: {ma_trend['crossover']}")
    
    # Higher highs and higher lows
    hh_hl = detector.higher_highs_higher_lows(window=20)
    print(f"\nHigher Highs/Lows Analysis:")
    print(f"  Trend: {hh_hl['trend']}")
    
    # Support and resistance
    levels = detector.support_resistance_levels(num_levels=3)
    print(f"\nSupport Levels: {[f'${x:.2f}' for x in levels['support']]}")
    print(f"Resistance Levels: {[f'${x:.2f}' for x in levels['resistance']]}")


def example_breakout_detection():
    """Example: Detect price breakouts"""
    print("\n" + "=" * 60)
    print("Breakout Detection Example")
    print("=" * 60)
    
    # Generate data with breakout
    np.random.seed(42)
    prices_consolidation = 100 + np.random.normal(0, 1, 50)
    prices_breakout = np.linspace(100, 120, 20)
    prices = np.concatenate([prices_consolidation, prices_breakout])
    
    resistance = 105
    support = 95
    
    # Detect breakout
    breakout = detect_breakout(prices, resistance, support)
    
    print(f"\nResistance Level: ${resistance:.2f}")
    print(f"Support Level: ${support:.2f}")
    print(f"Current Price: ${breakout['current_price']:.2f}")
    
    if breakout['breakout']:
        print(f"\nBREAKOUT DETECTED!")
        print(f"  Direction: {breakout['direction']}")
        print(f"  Level broken: ${breakout['level']:.2f}")
    else:
        print(f"\nNo breakout - price within range")


def example_forecasting():
    """Example: Forecast future prices"""
    print("\n" + "=" * 60)
    print("Price Forecasting Example")
    print("=" * 60)
    
    # Generate sample data with trend
    np.random.seed(42)
    trend = np.linspace(0, 10, 100)
    noise = np.random.normal(0, 1, 100)
    prices = 100 + trend + noise
    
    # Momentum forecaster
    forecaster = MomentumForecaster(prices)
    
    # Forecast with momentum
    momentum_forecast = forecaster.forecast_with_momentum(horizon=5, momentum_window=20)
    print(f"\nMomentum Forecast (5 periods):")
    print(f"  Direction: {momentum_forecast['direction']}")
    print(f"  Confidence: {momentum_forecast['confidence']*100:.1f}%")
    print(f"  Forecasted prices: {[f'${x:.2f}' for x in momentum_forecast['forecast']]}")
    
    # Ensemble forecast
    ensemble = ensemble_forecast(prices, horizon=5, methods=['linear', 'exponential', 'ma'])
    print(f"\nEnsemble Forecast (5 periods):")
    print(f"  Forecasted prices: {[f'${x:.2f}' for x in ensemble['ensemble']]}")
    print(f"  Uncertainty: {[f'±${x:.2f}' for x in ensemble['uncertainty']]}")
    
    # Confidence interval
    ci = forecast_confidence_interval(prices, horizon=5, confidence=0.95)
    print(f"\nForecast with 95% Confidence Interval:")
    for i, (point, lower, upper) in enumerate(zip(ci['forecast'], ci['lower_bound'], ci['upper_bound'])):
        print(f"  Period {i+1}: ${point:.2f} (${lower:.2f} - ${upper:.2f})")


def example_trading_strategy():
    """Example: Simple momentum trading strategy"""
    print("\n" + "=" * 60)
    print("Momentum Trading Strategy Example")
    print("=" * 60)
    
    # Generate sample data
    np.random.seed(42)
    prices = 100 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, 200)))
    
    # Calculate indicators
    sma_fast = simple_moving_average(prices, window=20)
    sma_slow = simple_moving_average(prices, window=50)
    rsi_values = rsi(prices, window=14)
    
    # Align arrays (account for different lengths due to windows)
    min_len = min(len(sma_fast), len(sma_slow), len(rsi_values))
    
    # Trading signals
    signals = []
    for i in range(1, min_len):
        # Golden cross (bullish)
        if sma_fast[-i-1] <= sma_slow[-i-1] and sma_fast[-i] > sma_slow[-i]:
            if rsi_values[-i] < 70:  # Not overbought
                signals.append(('BUY', i))
        
        # Death cross (bearish)
        if sma_fast[-i-1] >= sma_slow[-i-1] and sma_fast[-i] < sma_slow[-i]:
            if rsi_values[-i] > 30:  # Not oversold
                signals.append(('SELL', i))
    
    print(f"\nAnalyzed {len(prices)} periods")
    print(f"Generated {len(signals)} trading signals")
    
    if signals:
        print(f"\nRecent signals:")
        for signal_type, periods_ago in signals[-5:]:
            print(f"  {signal_type} signal {periods_ago} periods ago")
    
    # Current position
    current_rsi = rsi_values[-1]
    fast_above_slow = sma_fast[-1] > sma_slow[-1]
    
    print(f"\nCurrent Market Conditions:")
    print(f"  Price: ${prices[-1]:.2f}")
    print(f"  Fast SMA: ${sma_fast[-1]:.2f}")
    print(f"  Slow SMA: ${sma_slow[-1]:.2f}")
    print(f"  RSI: {current_rsi:.2f}")
    print(f"  Trend: {'Bullish' if fast_above_slow else 'Bearish'}")


if __name__ == '__main__':
    example_moving_averages()
    example_rsi()
    example_macd()
    example_bollinger_bands()
    example_trend_detection()
    example_breakout_detection()
    example_forecasting()
    example_trading_strategy()
    
    print("\n" + "=" * 60)
    print("Examples completed successfully!")
    print("=" * 60)
