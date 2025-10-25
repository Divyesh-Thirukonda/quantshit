"""
Adapters for converting between legacy dict formats and new typed structures
Provides backwards compatibility while enabling gradual migration to typed system
"""

from typing import Dict, List, Optional
from datetime import datetime
from .types import (
    Market, Quote, Platform, Outcome, ArbitrageOpportunity, 
    Order, OrderType, OrderStatus, Position, RiskLevel,
    ensure_platform, ensure_outcome
)


class MarketAdapter:
    """Converts between legacy market dicts and Market objects"""
    
    @staticmethod
    def from_dict(data: Dict) -> Market:
        """Convert legacy market dict to Market object"""
        platform = ensure_platform(data['platform'])
        
        # Create quotes from price data
        yes_quote = Quote(
            price=data['yes_price'],
            volume=data.get('volume', 0) * 0.6,  # Estimate YES volume as 60%
            liquidity=data.get('liquidity', 0) * 0.6
        )
        
        no_quote = Quote(
            price=data['no_price'],
            volume=data.get('volume', 0) * 0.4,  # Estimate NO volume as 40%
            liquidity=data.get('liquidity', 0) * 0.4
        )
        
        return Market(
            id=data['id'],
            platform=platform,
            title=data['title'],
            yes_quote=yes_quote,
            no_quote=no_quote,
            total_volume=data.get('volume', 0),
            total_liquidity=data.get('liquidity', 0),
            category=data.get('category'),
            tags=data.get('tags', [])
        )
    
    @staticmethod
    def to_dict(market: Market) -> Dict:
        """Convert Market object to legacy dict format"""
        return market.to_dict()
    
    @staticmethod
    def from_dict_list(data_list: List[Dict]) -> List[Market]:
        """Convert list of legacy dicts to list of Market objects"""
        return [MarketAdapter.from_dict(data) for data in data_list]
    
    @staticmethod
    def to_dict_list(markets: List[Market]) -> List[Dict]:
        """Convert list of Market objects to legacy dict format"""
        return [market.to_dict() for market in markets]


class OpportunityAdapter:
    """Converts between legacy opportunity dicts and ArbitrageOpportunity objects"""
    
    @staticmethod
    def from_dict(data: Dict) -> ArbitrageOpportunity:
        """Convert legacy opportunity dict to ArbitrageOpportunity object"""
        # Convert market dicts to Market objects
        buy_market = MarketAdapter.from_dict(data['buy_market'])
        sell_market = MarketAdapter.from_dict(data['sell_market'])
        
        outcome = ensure_outcome(data['outcome'])
        
        # Calculate confidence score based on spread
        spread = data.get('spread', 0)
        confidence_score = min(1.0, spread * 10)  # Higher spread = higher confidence
        
        # Determine risk level
        if spread >= 0.1:
            risk_level = RiskLevel.LOW
        elif spread >= 0.05:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.HIGH
        
        return ArbitrageOpportunity(
            id=f"{buy_market.id}_{sell_market.id}_{outcome.value}_{int(datetime.now().timestamp())}",
            buy_market=buy_market,
            sell_market=sell_market,
            outcome=outcome,
            buy_price=data['buy_price'],
            sell_price=data['sell_price'],
            spread=spread,
            expected_profit_per_share=data.get('expected_profit', 0),
            confidence_score=confidence_score,
            risk_level=risk_level,
            max_quantity=data.get('trade_amount', 100),
            recommended_quantity=data.get('position_size'),
            kelly_fraction=data.get('kelly_fraction'),
            risk_adjustment=data.get('risk_adjustment'),
            win_probability=data.get('win_probability')
        )
    
    @staticmethod
    def to_dict(opportunity: ArbitrageOpportunity) -> Dict:
        """Convert ArbitrageOpportunity object to legacy dict format"""
        return opportunity.to_legacy_dict()
    
    @staticmethod
    def from_dict_list(data_list: List[Dict]) -> List[ArbitrageOpportunity]:
        """Convert list of legacy dicts to list of ArbitrageOpportunity objects"""
        return [OpportunityAdapter.from_dict(data) for data in data_list]
    
    @staticmethod
    def to_dict_list(opportunities: List[ArbitrageOpportunity]) -> List[Dict]:
        """Convert list of ArbitrageOpportunity objects to legacy dict format"""
        return [opp.to_legacy_dict() for opp in opportunities]


class OrderAdapter:
    """Converts between order representations and Order objects"""
    
    @staticmethod
    def create_from_opportunity(opportunity: ArbitrageOpportunity, order_type: OrderType) -> Order:
        """Create Order from ArbitrageOpportunity"""
        if order_type == OrderType.BUY:
            platform = opportunity.buy_market.platform
            market_id = opportunity.buy_market.id
            price = opportunity.buy_price
        else:  # SELL
            platform = opportunity.sell_market.platform
            market_id = opportunity.sell_market.id
            price = opportunity.sell_price
        
        quantity = opportunity.recommended_quantity or opportunity.max_quantity
        
        return Order(
            market_id=market_id,
            platform=platform,
            outcome=opportunity.outcome,
            order_type=order_type,
            quantity=quantity,
            price=price
        )
    
    @staticmethod
    def from_execution_result(result: Dict, original_order: Order) -> Order:
        """Update Order object with execution results"""
        updated_order = original_order
        
        if result.get('success', False):
            updated_order.status = OrderStatus.FILLED
            updated_order.filled_quantity = original_order.quantity
            updated_order.average_fill_price = original_order.price
            updated_order.order_id = result.get('order_id')
        else:
            updated_order.status = OrderStatus.FAILED
        
        return updated_order


class PositionAdapter:
    """Converts between position representations and Position objects"""
    
    @staticmethod
    def from_portfolio_position(position_data: Dict, platform: Platform) -> Position:
        """Convert portfolio position dict to Position object"""
        # Parse market key to extract market_id and outcome
        market_key = position_data['market']
        parts = market_key.split('_')
        
        if len(parts) >= 3:
            market_id = f"{parts[0]}_{parts[1]}"
            outcome_str = parts[2]
        else:
            market_id = market_key
            outcome_str = "YES"  # Default
        
        outcome = ensure_outcome(outcome_str)
        
        return Position(
            market_id=market_id,
            platform=platform,
            outcome=outcome,
            quantity=int(position_data['shares']),
            average_price=position_data['avg_price'],
            current_price=position_data['avg_price'],  # Use avg_price as current for now
            total_cost=position_data.get('total_cost', position_data['shares'] * position_data['avg_price'])
        )
    
    @staticmethod
    def to_portfolio_dict(position: Position) -> Dict:
        """Convert Position object to portfolio dict format"""
        market_key = f"{position.market_id}_{position.outcome.value}"
        
        return {
            'market': market_key,
            'shares': position.quantity,
            'avg_price': position.average_price,
            'current_value': position.market_value,
            'unrealized_pnl': position.unrealized_pnl
        }


class PortfolioAdapter:
    """Converts between portfolio representations"""
    
    @staticmethod
    def extract_positions_from_summary(portfolio_summary: Dict) -> List[Position]:
        """Extract all positions from portfolio summary"""
        positions = []
        
        for platform_name, platform_data in portfolio_summary.items():
            if platform_name == 'total_portfolio_value':
                continue
            
            platform = ensure_platform(platform_name)
            platform_positions = platform_data.get('positions', [])
            
            for pos_data in platform_positions:
                position = PositionAdapter.from_portfolio_position(pos_data, platform)
                positions.append(position)
        
        return positions
    
    @staticmethod
    def get_platform_cash_balances(portfolio_summary: Dict) -> Dict[Platform, float]:
        """Extract cash balances by platform"""
        balances = {}
        
        for platform_name, platform_data in portfolio_summary.items():
            if platform_name == 'total_portfolio_value':
                continue
            
            platform = ensure_platform(platform_name)
            cash = platform_data.get('cash', 0.0)
            balances[platform] = cash
        
        return balances


# Backwards compatibility layer
class LegacyCompat:
    """Provides backwards compatibility for existing code"""
    
    @staticmethod
    def ensure_dict_format(opportunities: List) -> List[Dict]:
        """Ensure opportunities are in dict format for legacy code"""
        result = []
        
        for opp in opportunities:
            if isinstance(opp, ArbitrageOpportunity):
                result.append(opp.to_legacy_dict())
            elif isinstance(opp, dict):
                result.append(opp)
            else:
                raise ValueError(f"Unknown opportunity type: {type(opp)}")
        
        return result
    
    @staticmethod
    def ensure_typed_format(opportunities: List) -> List[ArbitrageOpportunity]:
        """Ensure opportunities are in typed format"""
        result = []
        
        for opp in opportunities:
            if isinstance(opp, dict):
                result.append(OpportunityAdapter.from_dict(opp))
            elif isinstance(opp, ArbitrageOpportunity):
                result.append(opp)
            else:
                raise ValueError(f"Unknown opportunity type: {type(opp)}")
        
        return result