"""
Volatility Calculation Module

This module provides functions for calculating historical and implied volatility.
"""

import numpy as np
from scipy.optimize import minimize_scalar
from .black_scholes import BlackScholes


def historical_volatility(prices, window=30, annualization_factor=252):
    """
    Calculate historical volatility from price series
    
    Parameters:
    -----------
    prices : array-like
        Series of historical prices
    window : int
        Lookback window for volatility calculation
    annualization_factor : int
        Number of trading periods per year (252 for daily, 52 for weekly)
    
    Returns:
    --------
    float
        Annualized historical volatility
    """
    prices = np.array(prices)
    
    if len(prices) < 2:
        raise ValueError("Need at least 2 prices to calculate volatility")
    
    # Calculate log returns
    log_returns = np.log(prices[1:] / prices[:-1])
    
    # Use last 'window' returns if available
    if len(log_returns) > window:
        log_returns = log_returns[-window:]
    
    # Calculate standard deviation and annualize
    volatility = np.std(log_returns) * np.sqrt(annualization_factor)
    
    return volatility


def rolling_historical_volatility(prices, window=30, annualization_factor=252):
    """
    Calculate rolling historical volatility
    
    Parameters:
    -----------
    prices : array-like
        Series of historical prices
    window : int
        Lookback window for volatility calculation
    annualization_factor : int
        Number of trading periods per year
    
    Returns:
    --------
    array
        Series of rolling volatility values
    """
    prices = np.array(prices)
    log_returns = np.log(prices[1:] / prices[:-1])
    
    volatilities = []
    for i in range(window, len(log_returns) + 1):
        window_returns = log_returns[i-window:i]
        vol = np.std(window_returns) * np.sqrt(annualization_factor)
        volatilities.append(vol)
    
    return np.array(volatilities)


def implied_volatility(option_price, S, K, T, r, option_type='call', 
                       initial_guess=0.3, tolerance=1e-6):
    """
    Calculate implied volatility using numerical optimization
    
    Parameters:
    -----------
    option_price : float
        Market price of the option
    S : float
        Current stock price
    K : float
        Strike price
    T : float
        Time to expiration (in years)
    r : float
        Risk-free rate
    option_type : str
        'call' or 'put'
    initial_guess : float
        Initial volatility guess
    tolerance : float
        Convergence tolerance
    
    Returns:
    --------
    float
        Implied volatility
    """
    def objective(sigma):
        """Objective function to minimize"""
        try:
            bs = BlackScholes(S, K, T, r, sigma, option_type)
            theoretical_price = bs.price()
            return abs(theoretical_price - option_price)
        except:
            return float('inf')
    
    # Use scipy's minimize_scalar for bounded optimization
    result = minimize_scalar(objective, bounds=(0.001, 5.0), method='bounded')
    
    if result.fun > tolerance:
        raise ValueError(f"Could not converge to implied volatility. Error: {result.fun}")
    
    return result.x


def volatility_surface(option_data, S, r):
    """
    Build a volatility surface from market option prices
    
    Parameters:
    -----------
    option_data : list of dict
        List of options with 'strike', 'expiry', 'price', 'type' keys
    S : float
        Current stock price
    r : float
        Risk-free rate
    
    Returns:
    --------
    dict
        Dictionary mapping (strike, expiry) to implied volatility
    """
    surface = {}
    
    for option in option_data:
        K = option['strike']
        T = option['expiry']
        price = option['price']
        option_type = option['type']
        
        try:
            iv = implied_volatility(price, S, K, T, r, option_type)
            surface[(K, T)] = iv
        except ValueError:
            # Skip options where IV cannot be calculated
            continue
    
    return surface


def volatility_smile(option_data, S, r, expiry):
    """
    Extract volatility smile for a specific expiry
    
    Parameters:
    -----------
    option_data : list of dict
        List of options with 'strike', 'expiry', 'price', 'type' keys
    S : float
        Current stock price
    r : float
        Risk-free rate
    expiry : float
        Time to expiration for the smile
    
    Returns:
    --------
    dict
        Dictionary mapping strike to implied volatility
    """
    smile = {}
    
    for option in option_data:
        if abs(option['expiry'] - expiry) < 1e-6:  # Match expiry
            K = option['strike']
            price = option['price']
            option_type = option['type']
            
            try:
                iv = implied_volatility(price, S, K, expiry, r, option_type)
                smile[K] = iv
            except ValueError:
                continue
    
    return smile


def realized_volatility(returns, annualization_factor=252):
    """
    Calculate realized volatility from returns
    
    Parameters:
    -----------
    returns : array-like
        Series of returns
    annualization_factor : int
        Number of trading periods per year
    
    Returns:
    --------
    float
        Annualized realized volatility
    """
    returns = np.array(returns)
    return np.std(returns) * np.sqrt(annualization_factor)
