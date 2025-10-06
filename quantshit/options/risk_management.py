"""
Risk Management Module

This module provides functions for managing risk in options trading,
including delta and gamma hedging.
"""

import numpy as np


class PortfolioRiskManager:
    """Manages risk for an options portfolio"""
    
    def __init__(self):
        """Initialize portfolio risk manager"""
        self.positions = []
    
    def add_position(self, option_contract, quantity, greeks):
        """
        Add a position to the portfolio
        
        Parameters:
        -----------
        option_contract : dict
            Option contract details (strike, expiry, type, etc.)
        quantity : int
            Number of contracts (positive for long, negative for short)
        greeks : dict
            Greeks for this position (delta, gamma, theta, vega, rho)
        """
        position = {
            'contract': option_contract,
            'quantity': quantity,
            'greeks': greeks
        }
        self.positions.append(position)
    
    def remove_position(self, index):
        """Remove a position from the portfolio"""
        if 0 <= index < len(self.positions):
            self.positions.pop(index)
    
    def clear_positions(self):
        """Clear all positions"""
        self.positions = []
    
    def portfolio_greeks(self):
        """
        Calculate total portfolio Greeks
        
        Returns:
        --------
        dict
            Aggregated Greeks for the entire portfolio
        """
        total_greeks = {
            'delta': 0.0,
            'gamma': 0.0,
            'theta': 0.0,
            'vega': 0.0,
            'rho': 0.0
        }
        
        for position in self.positions:
            quantity = position['quantity']
            greeks = position['greeks']
            
            for greek_name in total_greeks.keys():
                total_greeks[greek_name] += quantity * greeks.get(greek_name, 0.0)
        
        return total_greeks
    
    def delta_hedge_quantity(self, stock_price=None):
        """
        Calculate number of shares needed to delta hedge the portfolio
        
        Parameters:
        -----------
        stock_price : float, optional
            Current stock price (for calculating position value)
        
        Returns:
        --------
        float
            Number of shares to buy (positive) or sell (negative) for delta neutrality
        """
        portfolio_greeks = self.portfolio_greeks()
        # Negative of portfolio delta gives shares needed
        # (stock has delta of 1 per share)
        return -portfolio_greeks['delta']
    
    def gamma_hedge_recommendation(self, available_options):
        """
        Recommend option positions to achieve gamma neutrality
        
        Parameters:
        -----------
        available_options : list of dict
            List of available options with their greeks
            Each dict should have 'contract' and 'greeks' keys
        
        Returns:
        --------
        dict
            Recommended hedging strategy
        """
        portfolio_greeks = self.portfolio_greeks()
        current_gamma = portfolio_greeks['gamma']
        
        if abs(current_gamma) < 1e-6:
            return {
                'action': 'no_hedge_needed',
                'current_gamma': current_gamma
            }
        
        # Find option with highest gamma to use for hedging
        best_option = None
        best_gamma = 0
        
        for option in available_options:
            option_gamma = abs(option['greeks']['gamma'])
            if option_gamma > best_gamma:
                best_gamma = option_gamma
                best_option = option
        
        if best_option is None:
            return {
                'action': 'no_suitable_hedge',
                'current_gamma': current_gamma
            }
        
        # Calculate quantity needed
        hedge_quantity = -current_gamma / best_option['greeks']['gamma']
        
        return {
            'action': 'gamma_hedge',
            'current_gamma': current_gamma,
            'hedge_option': best_option['contract'],
            'hedge_quantity': hedge_quantity,
            'resulting_gamma': current_gamma + hedge_quantity * best_option['greeks']['gamma']
        }
    
    def risk_metrics(self):
        """
        Calculate portfolio risk metrics
        
        Returns:
        --------
        dict
            Portfolio risk metrics
        """
        portfolio_greeks = self.portfolio_greeks()
        
        return {
            'total_delta': portfolio_greeks['delta'],
            'total_gamma': portfolio_greeks['gamma'],
            'total_theta': portfolio_greeks['theta'],
            'total_vega': portfolio_greeks['vega'],
            'total_rho': portfolio_greeks['rho'],
            'is_delta_neutral': abs(portfolio_greeks['delta']) < 0.1,
            'is_gamma_neutral': abs(portfolio_greeks['gamma']) < 0.01,
            'position_count': len(self.positions)
        }


def calculate_var(returns, confidence_level=0.95):
    """
    Calculate Value at Risk (VaR)
    
    Parameters:
    -----------
    returns : array-like
        Historical returns
    confidence_level : float
        Confidence level for VaR (e.g., 0.95 for 95%)
    
    Returns:
    --------
    float
        VaR value
    """
    returns = np.array(returns)
    return np.percentile(returns, (1 - confidence_level) * 100)


def calculate_cvar(returns, confidence_level=0.95):
    """
    Calculate Conditional Value at Risk (CVaR) / Expected Shortfall
    
    Parameters:
    -----------
    returns : array-like
        Historical returns
    confidence_level : float
        Confidence level for CVaR
    
    Returns:
    --------
    float
        CVaR value
    """
    returns = np.array(returns)
    var = calculate_var(returns, confidence_level)
    return returns[returns <= var].mean()


def position_size_kelly(win_prob, win_loss_ratio, max_fraction=0.25):
    """
    Calculate position size using Kelly Criterion
    
    Parameters:
    -----------
    win_prob : float
        Probability of winning (0 to 1)
    win_loss_ratio : float
        Ratio of average win to average loss
    max_fraction : float
        Maximum fraction of capital to risk (safety factor)
    
    Returns:
    --------
    float
        Fraction of capital to allocate (0 to 1)
    """
    kelly_fraction = (win_prob * win_loss_ratio - (1 - win_prob)) / win_loss_ratio
    
    # Apply safety factor and ensure non-negative
    return max(0, min(kelly_fraction * 0.5, max_fraction))


def sharpe_ratio(returns, risk_free_rate=0.02, annualization_factor=252):
    """
    Calculate Sharpe Ratio
    
    Parameters:
    -----------
    returns : array-like
        Series of returns
    risk_free_rate : float
        Annual risk-free rate
    annualization_factor : int
        Number of trading periods per year
    
    Returns:
    --------
    float
        Sharpe ratio
    """
    returns = np.array(returns)
    
    excess_returns = returns - (risk_free_rate / annualization_factor)
    
    if np.std(excess_returns) == 0:
        return 0.0
    
    return np.sqrt(annualization_factor) * np.mean(excess_returns) / np.std(excess_returns)
