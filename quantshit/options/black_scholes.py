"""
Black-Scholes Option Pricing Model

This module implements the Black-Scholes formula for pricing European options.
"""

import numpy as np
from scipy.stats import norm


class BlackScholes:
    """Black-Scholes option pricing model"""
    
    def __init__(self, S, K, T, r, sigma, option_type='call'):
        """
        Initialize Black-Scholes model
        
        Parameters:
        -----------
        S : float
            Current stock price
        K : float
            Strike price
        T : float
            Time to expiration (in years)
        r : float
            Risk-free rate
        sigma : float
            Volatility (annualized)
        option_type : str
            'call' or 'put'
        """
        self.S = S
        self.K = K
        self.T = T
        self.r = r
        self.sigma = sigma
        self.option_type = option_type.lower()
        
    def _d1(self):
        """Calculate d1 parameter"""
        return (np.log(self.S / self.K) + (self.r + 0.5 * self.sigma ** 2) * self.T) / (self.sigma * np.sqrt(self.T))
    
    def _d2(self):
        """Calculate d2 parameter"""
        return self._d1() - self.sigma * np.sqrt(self.T)
    
    def price(self):
        """
        Calculate option price using Black-Scholes formula
        
        Returns:
        --------
        float
            Option price
        """
        if self.T <= 0:
            # Option has expired
            if self.option_type == 'call':
                return max(0, self.S - self.K)
            else:
                return max(0, self.K - self.S)
        
        d1 = self._d1()
        d2 = self._d2()
        
        if self.option_type == 'call':
            price = self.S * norm.cdf(d1) - self.K * np.exp(-self.r * self.T) * norm.cdf(d2)
        elif self.option_type == 'put':
            price = self.K * np.exp(-self.r * self.T) * norm.cdf(-d2) - self.S * norm.cdf(-d1)
        else:
            raise ValueError("option_type must be 'call' or 'put'")
        
        return price
    
    def delta(self):
        """
        Calculate option delta (rate of change of option price with respect to underlying)
        
        Returns:
        --------
        float
            Delta value
        """
        if self.T <= 0:
            if self.option_type == 'call':
                return 1.0 if self.S > self.K else 0.0
            else:
                return -1.0 if self.S < self.K else 0.0
        
        d1 = self._d1()
        
        if self.option_type == 'call':
            return norm.cdf(d1)
        else:
            return -norm.cdf(-d1)
    
    def gamma(self):
        """
        Calculate option gamma (rate of change of delta with respect to underlying)
        
        Returns:
        --------
        float
            Gamma value
        """
        if self.T <= 0:
            return 0.0
        
        d1 = self._d1()
        return norm.pdf(d1) / (self.S * self.sigma * np.sqrt(self.T))
    
    def theta(self):
        """
        Calculate option theta (rate of change of option price with respect to time)
        
        Returns:
        --------
        float
            Theta value (per year, divide by 365 for daily theta)
        """
        if self.T <= 0:
            return 0.0
        
        d1 = self._d1()
        d2 = self._d2()
        
        term1 = -(self.S * norm.pdf(d1) * self.sigma) / (2 * np.sqrt(self.T))
        
        if self.option_type == 'call':
            term2 = -self.r * self.K * np.exp(-self.r * self.T) * norm.cdf(d2)
            theta = term1 + term2
        else:
            term2 = self.r * self.K * np.exp(-self.r * self.T) * norm.cdf(-d2)
            theta = term1 + term2
        
        return theta
    
    def vega(self):
        """
        Calculate option vega (rate of change of option price with respect to volatility)
        
        Returns:
        --------
        float
            Vega value (for 1% change in volatility)
        """
        if self.T <= 0:
            return 0.0
        
        d1 = self._d1()
        return self.S * norm.pdf(d1) * np.sqrt(self.T) / 100
    
    def rho(self):
        """
        Calculate option rho (rate of change of option price with respect to interest rate)
        
        Returns:
        --------
        float
            Rho value (for 1% change in interest rate)
        """
        if self.T <= 0:
            return 0.0
        
        d2 = self._d2()
        
        if self.option_type == 'call':
            return self.K * self.T * np.exp(-self.r * self.T) * norm.cdf(d2) / 100
        else:
            return -self.K * self.T * np.exp(-self.r * self.T) * norm.cdf(-d2) / 100
    
    def greeks(self):
        """
        Calculate all Greeks at once
        
        Returns:
        --------
        dict
            Dictionary containing all Greeks
        """
        return {
            'delta': self.delta(),
            'gamma': self.gamma(),
            'theta': self.theta(),
            'vega': self.vega(),
            'rho': self.rho()
        }
