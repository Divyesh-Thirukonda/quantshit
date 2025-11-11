"""
Tracker service - tracks all open positions and their P&L.
Runs continuously, separate from execution.
"""

from typing import List, Dict
from ...models import Position
from ...fin_types import Exchange
from ...config import constants
from ...utils import get_logger

logger = get_logger(__name__)


class Tracker:
    """
    Track all open positions and calculate P&L.
    """

    def __init__(self):
        """Initialize position tracker"""
        self.positions: List[Position] = []
        self.total_realized_pnl: float = 0.0
        logger.info("Position tracker initialized")

    def add_position(self, position: Position):
        """
        Add a new position to track.

        Args:
            position: Position object to track
        """
        self.positions.append(position)
        logger.info(
            f"New position tracked: {position.outcome.value} in {position.market_id} "
            f"({position.quantity} contracts @ ${position.avg_entry_price:.4f})"
        )

    def update_positions(self, market_prices: Dict[str, Dict[str, float]]):
        """
        Update all positions with current market prices.

        Args:
            market_prices: Dict mapping market_id -> {'yes_price': float, 'no_price': float}
        """
        logger.debug(f"Updating {len(self.positions)} positions with current prices")

        for position in self.positions:
            if position.market_id in market_prices:
                prices = market_prices[position.market_id]

                # Update current price based on outcome
                position.current_price = (
                    prices['yes_price'] if position.outcome.value == 'YES'
                    else prices['no_price']
                )

                logger.debug(
                    f"Position {position.position_id}: "
                    f"P&L ${position.unrealized_pnl:.2f} ({position.unrealized_pnl_pct:+.2f}%)"
                )

    def get_total_unrealized_pnl(self) -> float:
        """Calculate total unrealized P&L across all positions"""
        return sum(pos.unrealized_pnl for pos in self.positions)

    def get_total_portfolio_value(self) -> float:
        """Calculate total current value of all positions"""
        return sum(pos.market_value for pos in self.positions)

    def get_positions_by_exchange(self, exchange: Exchange) -> List[Position]:
        """Get all positions for a specific exchange"""
        return [pos for pos in self.positions if pos.exchange == exchange]

    def close_position(self, position_id: str, realized_pnl: float):
        """
        Close a position and record realized P&L.

        Args:
            position_id: ID of position to close
            realized_pnl: Actual P&L from closing the position
        """
        self.positions = [pos for pos in self.positions if pos.position_id != position_id]
        self.total_realized_pnl += realized_pnl

        logger.info(
            f"Position {position_id} closed. "
            f"Realized P&L: ${realized_pnl:+.2f}, "
            f"Total realized: ${self.total_realized_pnl:+.2f}"
        )

    def should_close_position(self, position: Position) -> bool:
        """
        Determine if a position should be closed based on P&L thresholds.

        Args:
            position: Position to evaluate

        Returns:
            True if position should be closed
        """
        # Check take profit
        if position.unrealized_pnl_pct >= constants.DEFAULT_TAKE_PROFIT_PCT * 100:
            logger.info(
                f"Take profit triggered for {position.position_id}: "
                f"{position.unrealized_pnl_pct:.2f}%"
            )
            return True

        # Check stop loss
        if position.unrealized_pnl_pct <= constants.DEFAULT_STOP_LOSS_PCT * 100:
            logger.warning(
                f"Stop loss triggered for {position.position_id}: "
                f"{position.unrealized_pnl_pct:.2f}%"
            )
            return True

        return False

    def get_summary(self) -> Dict:
        """Get summary of all positions and P&L"""
        return {
            'total_positions': len(self.positions),
            'total_market_value': self.get_total_portfolio_value(),
            'total_unrealized_pnl': self.get_total_unrealized_pnl(),
            'total_realized_pnl': self.total_realized_pnl,
            'total_pnl': self.get_total_unrealized_pnl() + self.total_realized_pnl,
            'positions': [
                {
                    'position_id': pos.position_id,
                    'market_id': pos.market_id,
                    'exchange': pos.exchange.value,
                    'outcome': pos.outcome.value,
                    'quantity': pos.quantity,
                    'entry_price': pos.avg_entry_price,
                    'current_price': pos.current_price,
                    'market_value': pos.market_value,
                    'unrealized_pnl': pos.unrealized_pnl,
                    'unrealized_pnl_pct': pos.unrealized_pnl_pct
                }
                for pos in self.positions
            ]
        }
