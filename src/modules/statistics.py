"""
Statistical analysis utilities for trading strategies.
"""
import numpy as np
import pandas as pd
from typing import List, Tuple, Optional, Dict, Any
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from src.core.logger import get_logger

logger = get_logger(__name__)


class StatisticalAnalyzer:
    """Statistical analysis utilities for market data and trading."""
    
    def __init__(self):
        self.scaler = StandardScaler()
    
    def calculate_correlation_matrix(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate correlation matrix for price data.
        
        Args:
            price_data: DataFrame with columns as markets and rows as timestamps
            
        Returns:
            Correlation matrix
        """
        try:
            return price_data.corr()
        except Exception as e:
            logger.error(f"Error calculating correlation matrix: {e}")
            return pd.DataFrame()
    
    def detect_cointegration(
        self,
        series1: pd.Series,
        series2: pd.Series,
        significance_level: float = 0.05
    ) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Test for cointegration between two price series using Engle-Granger test.
        
        Args:
            series1: First price series
            series2: Second price series
            significance_level: Significance level for test
            
        Returns:
            Tuple of (is_cointegrated, p_value, details)
        """
        try:
            from statsmodels.tsa.stattools import coint
            
            # Align series
            aligned_data = pd.concat([series1, series2], axis=1).dropna()
            if len(aligned_data) < 10:
                return False, 1.0, {"error": "Insufficient data"}
            
            s1, s2 = aligned_data.iloc[:, 0], aligned_data.iloc[:, 1]
            
            # Perform cointegration test
            coint_t, p_value, crit_values = coint(s1, s2)
            
            is_cointegrated = p_value < significance_level
            
            details = {
                "test_statistic": coint_t,
                "critical_values": crit_values,
                "series1_name": series1.name,
                "series2_name": series2.name,
                "data_points": len(aligned_data)
            }
            
            return is_cointegrated, p_value, details
        
        except Exception as e:
            logger.error(f"Error in cointegration test: {e}")
            return False, 1.0, {"error": str(e)}
    
    def calculate_rolling_correlation(
        self,
        series1: pd.Series,
        series2: pd.Series,
        window: int = 20
    ) -> pd.Series:
        """
        Calculate rolling correlation between two series.
        
        Args:
            series1: First series
            series2: Second series
            window: Rolling window size
            
        Returns:
            Rolling correlation series
        """
        try:
            aligned_data = pd.concat([series1, series2], axis=1).dropna()
            if len(aligned_data) < window:
                return pd.Series()
            
            return aligned_data.iloc[:, 0].rolling(window).corr(aligned_data.iloc[:, 1])
        
        except Exception as e:
            logger.error(f"Error calculating rolling correlation: {e}")
            return pd.Series()
    
    def detect_statistical_arbitrage_opportunity(
        self,
        series1: pd.Series,
        series2: pd.Series,
        lookback_period: int = 20,
        entry_threshold: float = 2.0,
        exit_threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Detect statistical arbitrage opportunity using mean reversion.
        
        Args:
            series1: First price series
            series2: Second price series
            lookback_period: Period for calculating statistics
            entry_threshold: Z-score threshold for entry
            exit_threshold: Z-score threshold for exit
            
        Returns:
            Dictionary with opportunity details
        """
        try:
            # Align series
            aligned_data = pd.concat([series1, series2], axis=1).dropna()
            if len(aligned_data) < lookback_period * 2:
                return {"opportunity": False, "reason": "Insufficient data"}
            
            s1, s2 = aligned_data.iloc[:, 0], aligned_data.iloc[:, 1]
            
            # Calculate spread
            spread = s1 - s2
            
            # Calculate rolling statistics
            rolling_mean = spread.rolling(lookback_period).mean()
            rolling_std = spread.rolling(lookback_period).std()
            
            # Calculate Z-score
            z_score = (spread - rolling_mean) / rolling_std
            
            current_z_score = z_score.iloc[-1]
            
            if abs(current_z_score) >= entry_threshold:
                # Determine trade direction
                if current_z_score > entry_threshold:
                    # Spread is too high, sell s1 and buy s2
                    signal = {
                        "long_asset": series2.name,
                        "short_asset": series1.name,
                        "direction": "short_spread"
                    }
                else:
                    # Spread is too low, buy s1 and sell s2
                    signal = {
                        "long_asset": series1.name,
                        "short_asset": series2.name,
                        "direction": "long_spread"
                    }
                
                return {
                    "opportunity": True,
                    "z_score": current_z_score,
                    "signal": signal,
                    "entry_threshold": entry_threshold,
                    "exit_threshold": exit_threshold,
                    "spread_mean": rolling_mean.iloc[-1],
                    "spread_std": rolling_std.iloc[-1],
                    "current_spread": spread.iloc[-1]
                }
            
            return {
                "opportunity": False,
                "z_score": current_z_score,
                "reason": f"Z-score {current_z_score:.2f} below threshold {entry_threshold}"
            }
        
        except Exception as e:
            logger.error(f"Error detecting stat arb opportunity: {e}")
            return {"opportunity": False, "error": str(e)}
    
    def calculate_sharpe_ratio(
        self,
        returns: pd.Series,
        risk_free_rate: float = 0.02
    ) -> float:
        """
        Calculate Sharpe ratio for a return series.
        
        Args:
            returns: Return series
            risk_free_rate: Annual risk-free rate
            
        Returns:
            Annualized Sharpe ratio
        """
        try:
            if len(returns) == 0:
                return 0.0
            
            # Convert to daily risk-free rate
            daily_rf_rate = risk_free_rate / 252
            
            # Calculate excess returns
            excess_returns = returns - daily_rf_rate
            
            # Calculate Sharpe ratio
            if excess_returns.std() == 0:
                return 0.0
            
            sharpe = excess_returns.mean() / excess_returns.std()
            
            # Annualize
            return sharpe * np.sqrt(252)
        
        except Exception as e:
            logger.error(f"Error calculating Sharpe ratio: {e}")
            return 0.0
    
    def calculate_maximum_drawdown(self, equity_curve: pd.Series) -> Dict[str, float]:
        """
        Calculate maximum drawdown and related metrics.
        
        Args:
            equity_curve: Equity curve series
            
        Returns:
            Dictionary with drawdown metrics
        """
        try:
            if len(equity_curve) == 0:
                return {"max_drawdown": 0.0, "max_drawdown_duration": 0}
            
            # Calculate running maximum
            running_max = equity_curve.expanding().max()
            
            # Calculate drawdown
            drawdown = (equity_curve - running_max) / running_max
            
            # Find maximum drawdown
            max_drawdown = drawdown.min()
            
            # Calculate drawdown duration
            in_drawdown = drawdown < 0
            drawdown_periods = []
            start = None
            
            for i, is_dd in enumerate(in_drawdown):
                if is_dd and start is None:
                    start = i
                elif not is_dd and start is not None:
                    drawdown_periods.append(i - start)
                    start = None
            
            # Handle case where we're still in drawdown
            if start is not None:
                drawdown_periods.append(len(in_drawdown) - start)
            
            max_drawdown_duration = max(drawdown_periods) if drawdown_periods else 0
            
            return {
                "max_drawdown": abs(max_drawdown),
                "max_drawdown_duration": max_drawdown_duration,
                "current_drawdown": abs(drawdown.iloc[-1]),
                "drawdown_series": drawdown
            }
        
        except Exception as e:
            logger.error(f"Error calculating drawdown: {e}")
            return {"max_drawdown": 0.0, "max_drawdown_duration": 0}
    
    def calculate_var(
        self,
        returns: pd.Series,
        confidence_level: float = 0.95
    ) -> float:
        """
        Calculate Value at Risk (VaR).
        
        Args:
            returns: Return series
            confidence_level: Confidence level (e.g., 0.95 for 95% VaR)
            
        Returns:
            VaR value
        """
        try:
            if len(returns) == 0:
                return 0.0
            
            # Calculate percentile
            alpha = 1 - confidence_level
            var = np.percentile(returns, alpha * 100)
            
            return abs(var)
        
        except Exception as e:
            logger.error(f"Error calculating VaR: {e}")
            return 0.0
    
    def perform_pca_analysis(
        self,
        price_data: pd.DataFrame,
        n_components: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Perform Principal Component Analysis on price data.
        
        Args:
            price_data: DataFrame with price data
            n_components: Number of components to keep
            
        Returns:
            Dictionary with PCA results
        """
        try:
            if price_data.empty:
                return {"error": "Empty data"}
            
            # Calculate returns
            returns = price_data.pct_change().dropna()
            
            if len(returns) < 2:
                return {"error": "Insufficient data for PCA"}
            
            # Standardize data
            scaled_data = self.scaler.fit_transform(returns)
            
            # Perform PCA
            pca = PCA(n_components=n_components)
            components = pca.fit_transform(scaled_data)
            
            # Calculate explained variance
            explained_variance_ratio = pca.explained_variance_ratio_
            cumulative_variance = np.cumsum(explained_variance_ratio)
            
            return {
                "components": components,
                "explained_variance_ratio": explained_variance_ratio,
                "cumulative_variance": cumulative_variance,
                "principal_components": pca.components_,
                "feature_names": returns.columns.tolist(),
                "n_components_95": np.argmax(cumulative_variance >= 0.95) + 1
            }
        
        except Exception as e:
            logger.error(f"Error in PCA analysis: {e}")
            return {"error": str(e)}
    
    def detect_regime_change(
        self,
        series: pd.Series,
        window: int = 20,
        threshold: float = 2.0
    ) -> List[int]:
        """
        Detect regime changes in a time series using rolling statistics.
        
        Args:
            series: Time series data
            window: Rolling window for statistics
            threshold: Z-score threshold for regime change
            
        Returns:
            List of indices where regime changes occur
        """
        try:
            if len(series) < window * 2:
                return []
            
            # Calculate rolling mean and std
            rolling_mean = series.rolling(window).mean()
            rolling_std = series.rolling(window).std()
            
            # Calculate z-scores for mean changes
            mean_changes = rolling_mean.diff().abs()
            mean_z_scores = mean_changes / rolling_std
            
            # Find regime changes
            regime_changes = []
            for i in range(window, len(mean_z_scores)):
                if mean_z_scores.iloc[i] > threshold:
                    regime_changes.append(i)
            
            return regime_changes
        
        except Exception as e:
            logger.error(f"Error detecting regime changes: {e}")
            return []