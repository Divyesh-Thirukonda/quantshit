"""
Repository - data access layer for all database operations.
Dependency Inversion - services don't know if we use Postgres, SQLite, or in-memory.
Just call repository methods.
"""

from typing import List, Optional, Dict
from datetime import datetime
from ..models import Opportunity, Order, Position
from ..utils import get_logger

logger = get_logger(__name__)


class Repository:
    """
    Data access layer - all database operations go through here.
    Currently implements in-memory storage (can be replaced with SQL later).
    """

    def __init__(self):
        """Initialize repository with in-memory storage"""
        # In-memory storage (replace with real DB later)
        self.opportunities: Dict[str, Opportunity] = {}
        self.orders: Dict[str, Order] = {}
        self.positions: Dict[str, Position] = {}

        logger.info("Repository initialized (in-memory mode)")

    # Opportunity operations
    def save_opportunity(self, opportunity: Opportunity) -> bool:
        """
        Save an opportunity to the database.

        Args:
            opportunity: Opportunity object to save

        Returns:
            True if successful
        """
        try:
            # Generate ID if not set
            opp_id = f"opp_{opportunity.timestamp.timestamp()}"
            self.opportunities[opp_id] = opportunity

            logger.debug(f"Saved opportunity: {opp_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save opportunity: {e}")
            return False

    def get_opportunities(
        self,
        limit: int = 100,
        min_profit: Optional[float] = None
    ) -> List[Opportunity]:
        """
        Get opportunities from database.

        Args:
            limit: Maximum number to return
            min_profit: Optional minimum profit filter

        Returns:
            List of opportunities
        """
        opps = list(self.opportunities.values())

        # Apply filters
        if min_profit is not None:
            opps = [opp for opp in opps if opp.expected_profit >= min_profit]

        # Sort by timestamp (newest first)
        opps.sort(key=lambda x: x.timestamp, reverse=True)

        return opps[:limit]

    # Order operations
    def save_order(self, order: Order) -> bool:
        """
        Save an order to the database.

        Args:
            order: Order object to save

        Returns:
            True if successful
        """
        try:
            self.orders[order.id] = order
            logger.debug(f"Saved order: {order.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save order: {e}")
            return False

    def get_order(self, order_id: str) -> Optional[Order]:
        """Get an order by ID"""
        return self.orders.get(order_id)

    def get_orders(
        self,
        exchange: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Order]:
        """
        Get orders from database with optional filters.

        Args:
            exchange: Filter by exchange
            status: Filter by status
            limit: Maximum number to return

        Returns:
            List of orders
        """
        orders = list(self.orders.values())

        # Apply filters
        if exchange:
            orders = [o for o in orders if o.exchange.value == exchange]
        if status:
            orders = [o for o in orders if o.status.value == status]

        # Sort by timestamp (newest first)
        orders.sort(key=lambda x: x.timestamp, reverse=True)

        return orders[:limit]

    def update_order(self, order: Order) -> bool:
        """Update an existing order"""
        if order.id in self.orders:
            self.orders[order.id] = order
            logger.debug(f"Updated order: {order.id}")
            return True
        return False

    # Position operations
    def save_position(self, position: Position) -> bool:
        """
        Save a position to the database.

        Args:
            position: Position object to save

        Returns:
            True if successful
        """
        try:
            self.positions[position.position_id] = position
            logger.debug(f"Saved position: {position.position_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save position: {e}")
            return False

    def get_position(self, position_id: str) -> Optional[Position]:
        """Get a position by ID"""
        return self.positions.get(position_id)

    def get_positions(
        self,
        exchange: Optional[str] = None,
        market_id: Optional[str] = None
    ) -> List[Position]:
        """
        Get all positions with optional filters.

        Args:
            exchange: Filter by exchange
            market_id: Filter by market

        Returns:
            List of positions
        """
        positions = list(self.positions.values())

        # Apply filters
        if exchange:
            positions = [p for p in positions if p.exchange.value == exchange]
        if market_id:
            positions = [p for p in positions if p.market_id == market_id]

        return positions

    def update_position(self, position: Position) -> bool:
        """Update an existing position"""
        if position.position_id in self.positions:
            self.positions[position.position_id] = position
            logger.debug(f"Updated position: {position.position_id}")
            return True
        return False

    def delete_position(self, position_id: str) -> bool:
        """Delete a position (when closed)"""
        if position_id in self.positions:
            del self.positions[position_id]
            logger.debug(f"Deleted position: {position_id}")
            return True
        return False

    # Trade history
    def get_historical_trades(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Order]:
        """
        Get historical filled orders (trades).

        Args:
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number to return

        Returns:
            List of filled orders
        """
        # Get only filled orders
        trades = [o for o in self.orders.values() if o.is_filled]

        # Apply date filters
        if start_date:
            trades = [t for t in trades if t.timestamp >= start_date]
        if end_date:
            trades = [t for t in trades if t.timestamp <= end_date]

        # Sort by timestamp (newest first)
        trades.sort(key=lambda x: x.timestamp, reverse=True)

        return trades[:limit]

    # Statistics
    def get_stats(self) -> Dict:
        """Get repository statistics"""
        return {
            'total_opportunities': len(self.opportunities),
            'total_orders': len(self.orders),
            'total_positions': len(self.positions),
            'filled_orders': len([o for o in self.orders.values() if o.is_filled])
        }

    def clear_all(self):
        """Clear all data (for testing)"""
        self.opportunities.clear()
        self.orders.clear()
        self.positions.clear()
        logger.warning("Repository cleared - all data deleted")
