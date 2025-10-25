"""
Strategic planning layer for position sizing and risk management
"""

import math
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


class PortfolioPlanner:
    """Plans position sizing and manages portfolio-level risk"""
    
    def __init__(self, max_position_pct: float = 0.1, max_platform_pct: float = 0.6, 
                 correlation_threshold: float = 0.7, min_cash_reserve: float = 0.2):
        self.max_position_pct = max_position_pct  # Max 10% per position
        self.max_platform_pct = max_platform_pct  # Max 60% per platform  
        self.correlation_threshold = correlation_threshold  # High correlation warning
        self.min_cash_reserve = min_cash_reserve  # Keep 20% cash
        
    def plan_trades(self, opportunities: List[Dict], portfolio_summary: Dict) -> List[Dict]:
        """Plan optimized trades with position sizing and risk management"""
        if not opportunities:
            return []
        
        total_portfolio_value = portfolio_summary['total_portfolio_value']
        
        print(f"\nStrategic Planning:")
        print(f"   Portfolio Value: ${total_portfolio_value:,.2f}")
        print(f"   Available Opportunities: {len(opportunities)}")
        
        # Step 1: Filter opportunities by risk criteria
        filtered_ops = self._filter_by_risk(opportunities, portfolio_summary)
        print(f"   After Risk Filter: {len(filtered_ops)}")
        
        # Step 2: Assess correlation risks
        correlation_groups = self._assess_correlation_risk(filtered_ops)
        print(f"   Correlation Groups: {len(correlation_groups)}")
        
        # Step 3: Calculate optimal position sizes
        sized_opportunities = self._calculate_position_sizes(
            filtered_ops, portfolio_summary, correlation_groups
        )
        
        # Step 4: Prioritize and sequence trades
        planned_trades = self._prioritize_trades(sized_opportunities, portfolio_summary)
        
        print(f"   Final Planned Trades: {len(planned_trades)}")
        if planned_trades:
            total_capital_used = sum(trade['position_size'] * trade['avg_price'] for trade in planned_trades)
            print(f"   Total Capital to Deploy: ${total_capital_used:,.2f}")
            print(f"   Capital Utilization: {(total_capital_used/total_portfolio_value)*100:.1f}%")
        
        return planned_trades
    
    def _filter_by_risk(self, opportunities: List[Dict], portfolio: Dict) -> List[Dict]:
        """Filter opportunities by basic risk criteria"""
        filtered = []
        
        for opp in opportunities:
            # Check minimum spread (already handled in strategy)
            if opp['spread'] < 0.02:  # Less than 2% spread is risky
                continue
                
            # Check if we already have position in these markets
            risk_level = self._assess_market_risk(opp, portfolio)
            if risk_level > 0.8:  # High risk threshold
                continue
                
            # Check platform concentration
            platform_risk = self._assess_platform_concentration(opp, portfolio)
            if platform_risk > self.max_platform_pct:
                continue
                
            filtered.append(opp)
        
        return filtered
    
    def _assess_market_risk(self, opportunity: Dict, portfolio: Dict) -> float:
        """Assess risk of adding position in these specific markets"""
        risk_score = 0.0
        
        buy_market = opportunity['buy_market']
        sell_market = opportunity['sell_market']
        
        # Check if we already have positions in these markets
        for platform, data in portfolio.items():
            if platform == 'total_portfolio_value':
                continue
                
            for position in data.get('positions', []):
                market_id = position['market'].split('_')[0] + '_' + position['market'].split('_')[1]
                
                # High risk if we already have positions in same markets
                if (buy_market['id'] in market_id or sell_market['id'] in market_id):
                    risk_score += 0.3
                    
                # Medium risk if similar market themes
                if self._markets_related(buy_market, position) or self._markets_related(sell_market, position):
                    risk_score += 0.1
        
        return min(risk_score, 1.0)
    
    def _assess_platform_concentration(self, opportunity: Dict, portfolio: Dict) -> float:
        """Check if adding this trade would over-concentrate on platforms"""
        buy_platform = opportunity['buy_market']['platform']
        sell_platform = opportunity['sell_market']['platform']
        
        total_value = portfolio['total_portfolio_value']
        
        buy_platform_pct = portfolio.get(buy_platform, {}).get('total_value', 0) / total_value
        sell_platform_pct = portfolio.get(sell_platform, {}).get('total_value', 0) / total_value
        
        return max(buy_platform_pct, sell_platform_pct)
    
    def _assess_correlation_risk(self, opportunities: List[Dict]) -> Dict[str, List[Dict]]:
        """Group opportunities by correlation to manage correlated risk"""
        correlation_groups = defaultdict(list)
        
        # Group by market themes/entities
        for opp in opportunities:
            buy_market = opp['buy_market']
            sell_market = opp['sell_market']
            
            # Extract theme/entity from market titles
            theme = self._extract_market_theme(buy_market['title'], sell_market['title'])
            correlation_groups[theme].append(opp)
        
        # Warn about high correlation groups
        for theme, ops in correlation_groups.items():
            if len(ops) > 2:
                print(f"   ⚠️  High correlation: {len(ops)} opportunities in '{theme}' theme")
        
        return dict(correlation_groups)
    
    def _extract_market_theme(self, title1: str, title2: str) -> str:
        """Extract common theme from market titles"""
        # Common themes and their keywords
        themes = {
            'trump': ['trump', 'donald', 'president', 'election'],
            'fed': ['fed', 'interest', 'rate', 'powell', 'fomc'],
            'tech_stocks': ['apple', 'tesla', 'meta', 'google', 'amazon'],
            'earnings': ['earnings', 'revenue', 'profit', 'beats', 'misses'],
            'crypto': ['bitcoin', 'ethereum', 'crypto', 'btc', 'eth'],
        }
        
        combined_text = (title1 + ' ' + title2).lower()
        
        for theme, keywords in themes.items():
            if any(keyword in combined_text for keyword in keywords):
                return theme
        
        # Default theme based on first significant word
        words = combined_text.split()
        significant_words = [w for w in words if len(w) > 4]
        return significant_words[0] if significant_words else 'misc'
    
    def _calculate_position_sizes(self, opportunities: List[Dict], portfolio: Dict, 
                                correlation_groups: Dict[str, List[Dict]]) -> List[Dict]:
        """Calculate optimal position sizes using Kelly criterion and risk limits"""
        sized_opportunities = []
        total_portfolio_value = portfolio['total_portfolio_value']
        
        for opp in opportunities:
            # Base Kelly calculation
            win_prob = self._estimate_win_probability(opp)
            payoff_ratio = opp['expected_profit'] / (opp['buy_price'] * 100)  # Current fixed size
            
            # Kelly fraction: f = (bp - q) / b where b=payoff ratio, p=win prob, q=lose prob
            kelly_fraction = ((payoff_ratio * win_prob) - (1 - win_prob)) / payoff_ratio
            kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%
            
            # Apply risk adjustments
            risk_adjustment = self._calculate_risk_adjustment(opp, portfolio, correlation_groups)
            adjusted_fraction = kelly_fraction * risk_adjustment
            
            # Calculate position size
            max_position_value = total_portfolio_value * self.max_position_pct
            kelly_position_value = total_portfolio_value * adjusted_fraction
            
            position_value = min(max_position_value, kelly_position_value)
            position_size = position_value / opp['buy_price']
            position_size = max(10, round(position_size))  # Minimum 10 shares
            
            # Update opportunity with sizing info
            sized_opp = opp.copy()
            sized_opp.update({
                'position_size': position_size,
                'position_value': position_size * opp['buy_price'],
                'kelly_fraction': kelly_fraction,
                'risk_adjustment': risk_adjustment,
                'win_probability': win_prob,
                'avg_price': (opp['buy_price'] + opp['sell_price']) / 2
            })
            
            sized_opportunities.append(sized_opp)
        
        return sized_opportunities
    
    def _estimate_win_probability(self, opportunity: Dict) -> float:
        """Estimate probability of successful arbitrage"""
        base_prob = 0.85  # 85% base success rate for arbitrage
        
        # Adjust based on spread size (larger spreads = higher confidence)
        spread_bonus = min(0.1, opportunity['spread'] * 0.5)
        
        # Adjust based on market liquidity (mock calculation)
        buy_liquidity = opportunity['buy_market'].get('liquidity', 10000)
        sell_liquidity = opportunity['sell_market'].get('liquidity', 10000)
        min_liquidity = min(buy_liquidity, sell_liquidity)
        
        liquidity_bonus = min(0.05, min_liquidity / 100000)  # Up to 5% bonus for high liquidity
        
        return min(0.95, base_prob + spread_bonus + liquidity_bonus)
    
    def _calculate_risk_adjustment(self, opportunity: Dict, portfolio: Dict, 
                                 correlation_groups: Dict[str, List[Dict]]) -> float:
        """Calculate risk adjustment factor (0-1)"""
        adjustment = 1.0
        
        # Correlation penalty
        theme = self._extract_market_theme(
            opportunity['buy_market']['title'], 
            opportunity['sell_market']['title']
        )
        
        correlated_trades = len(correlation_groups.get(theme, []))
        if correlated_trades > 2:
            correlation_penalty = 1 - (0.1 * (correlated_trades - 2))  # 10% penalty per extra correlated trade
            adjustment *= max(0.5, correlation_penalty)
        
        # Platform concentration penalty
        platform_conc = self._assess_platform_concentration(opportunity, portfolio)
        if platform_conc > 0.4:
            concentration_penalty = 1 - ((platform_conc - 0.4) * 2)  # Penalty above 40%
            adjustment *= max(0.3, concentration_penalty)
        
        # Small spread penalty (less confidence)
        if opportunity['spread'] < 0.05:
            spread_penalty = opportunity['spread'] / 0.05  # Linear scaling below 5%
            adjustment *= spread_penalty
        
        return adjustment
    
    def _prioritize_trades(self, opportunities: List[Dict], portfolio: Dict) -> List[Dict]:
        """Prioritize and sequence trades for execution"""
        if not opportunities:
            return []
        
        # Calculate risk-adjusted expected return for each trade
        for opp in opportunities:
            risk_adj_return = (opp['expected_profit'] * opp['position_size'] * 
                             opp['win_probability'] * opp['risk_adjustment'])
            opp['risk_adj_return'] = risk_adj_return
            opp['return_per_dollar'] = risk_adj_return / opp['position_value']
        
        # Sort by risk-adjusted return per dollar invested
        sorted_ops = sorted(opportunities, key=lambda x: x['return_per_dollar'], reverse=True)
        
        # Apply capital constraints
        total_value = portfolio['total_portfolio_value']
        max_deploy = total_value * (1 - self.min_cash_reserve)  # Keep cash reserve
        
        selected_trades = []
        deployed_capital = 0
        
        for opp in sorted_ops:
            if deployed_capital + opp['position_value'] <= max_deploy:
                selected_trades.append(opp)
                deployed_capital += opp['position_value']
            else:
                # Try with smaller position size
                remaining_capital = max_deploy - deployed_capital
                if remaining_capital > opp['buy_price'] * 10:  # At least 10 shares
                    smaller_size = remaining_capital / opp['buy_price']
                    smaller_size = max(10, round(smaller_size))
                    
                    scaled_opp = opp.copy()
                    scaled_opp['position_size'] = smaller_size
                    scaled_opp['position_value'] = smaller_size * opp['buy_price']
                    selected_trades.append(scaled_opp)
                    break
        
        return selected_trades
    
    def _markets_related(self, market: Dict, position: Dict) -> bool:
        """Check if market and existing position are related"""
        market_theme = self._extract_market_theme(market['title'], "")
        position_theme = self._extract_market_theme(position['market'], "")
        return market_theme == position_theme and market_theme != 'misc'


class RiskManager:
    """Manages various types of trading risk"""
    
    def __init__(self):
        self.max_correlation = 0.7
        self.max_drawdown = 0.15
        
    def assess_portfolio_risk(self, portfolio: Dict, new_trades: List[Dict]) -> Dict:
        """Comprehensive portfolio risk assessment"""
        risk_metrics = {
            'correlation_risk': self._calculate_correlation_risk(portfolio, new_trades),
            'concentration_risk': self._calculate_concentration_risk(portfolio),
            'liquidity_risk': self._calculate_liquidity_risk(portfolio),
            'platform_risk': self._calculate_platform_risk(portfolio),
            'overall_risk_score': 0.0
        }
        
        # Calculate overall risk score (0-1, higher = riskier)
        weights = {'correlation_risk': 0.3, 'concentration_risk': 0.3, 
                  'liquidity_risk': 0.2, 'platform_risk': 0.2}
        
        risk_metrics['overall_risk_score'] = sum(
            risk_metrics[risk_type] * weight 
            for risk_type, weight in weights.items()
        )
        
        return risk_metrics
    
    def _calculate_correlation_risk(self, portfolio: Dict, new_trades: List[Dict]) -> float:
        """Calculate correlation risk between positions"""
        if not new_trades:
            return 0.0
        
        # Group all positions (existing + new) by themes
        theme_exposures = defaultdict(float)
        total_exposure = 0
        
        # Add existing positions
        for platform, data in portfolio.items():
            if platform == 'total_portfolio_value':
                continue
            for position in data.get('positions', []):
                theme = self._extract_theme_from_position(position['market'])
                theme_exposures[theme] += position['current_value']
                total_exposure += position['current_value']
        
        # Add new trades
        for trade in new_trades:
            theme = self._extract_theme_from_trade(trade)
            theme_exposures[theme] += trade['position_value']
            total_exposure += trade['position_value']
        
        if total_exposure == 0:
            return 0.0
        
        # Calculate concentration in each theme
        max_theme_concentration = max(exposure / total_exposure for exposure in theme_exposures.values())
        
        # Risk increases exponentially with concentration
        correlation_risk = min(1.0, (max_theme_concentration ** 2) * 2)
        return correlation_risk
    
    def _calculate_concentration_risk(self, portfolio: Dict) -> float:
        """Calculate position concentration risk"""
        total_value = portfolio.get('total_portfolio_value', 1)
        position_concentrations = []
        
        for platform, data in portfolio.items():
            if platform == 'total_portfolio_value':
                continue
            for position in data.get('positions', []):
                concentration = position['current_value'] / total_value
                position_concentrations.append(concentration)
        
        if not position_concentrations:
            return 0.0
        
        # Risk based on largest single position
        max_concentration = max(position_concentrations)
        return min(1.0, max_concentration * 5)  # Risk scales with max concentration
    
    def _calculate_liquidity_risk(self, portfolio: Dict) -> float:
        """Estimate liquidity risk of current positions"""
        # For now, assume all positions have similar liquidity
        # In real implementation, would check market volumes and bid-ask spreads
        total_positions = sum(len(data.get('positions', [])) 
                            for platform, data in portfolio.items() 
                            if platform != 'total_portfolio_value')
        
        # More positions = potentially harder to exit quickly
        return min(1.0, total_positions * 0.1)
    
    def _calculate_platform_risk(self, portfolio: Dict) -> float:
        """Calculate platform concentration risk"""
        total_value = portfolio.get('total_portfolio_value', 1)
        platform_concentrations = []
        
        for platform, data in portfolio.items():
            if platform == 'total_portfolio_value':
                continue
            concentration = data.get('total_value', 0) / total_value
            platform_concentrations.append(concentration)
        
        if not platform_concentrations:
            return 0.0
        
        # Risk increases with uneven distribution
        max_platform_conc = max(platform_concentrations)
        return min(1.0, max_platform_conc * 1.5)
    
    def _extract_theme_from_position(self, market_key: str) -> str:
        """Extract theme from position market key"""
        # Simplified theme extraction
        if 'trump' in market_key.lower():
            return 'trump'
        elif 'fed' in market_key.lower() or 'rate' in market_key.lower():
            return 'fed'
        elif any(tech in market_key.lower() for tech in ['apple', 'tesla', 'meta']):
            return 'tech'
        else:
            return 'misc'
    
    def _extract_theme_from_trade(self, trade: Dict) -> str:
        """Extract theme from trade opportunity"""
        combined_title = trade['buy_market']['title'] + ' ' + trade['sell_market']['title']
        return self._extract_theme_from_position(combined_title)