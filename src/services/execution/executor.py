"""
Executor service - actually places orders on both exchanges.
Separate from validation so we can have multiple execution strategies.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from ...models import Opportunity, Order, Position
from ...types import Exchange, OrderSide, OrderStatus, Outcome
from ...config import settings
from ...utils import get_logger

logger = get_logger(__name__)


@dataclass
class ExecutionResult:
    """Result of executing a trade"""
    success: bool
    buy_order: Optional[Order] = None
    sell_order: Optional[Order] = None
    error_message: Optional[str] = None


class Executor:
    """
    Executes arbitrage trades on both exchanges.
    Currently supports paper trading mode.
    """

    def __init__(self, paper_trading: bool = True):
        """
        Initialize executor.

        Args:
            paper_trading: If True, simulate orders without hitting real APIs
        """
        self.paper_trading = paper_trading or settings.PAPER_TRADING
        logger.info(f"Executor initialized (paper_trading={self.paper_trading})")

    def execute(self, opportunity: Opportunity) -> ExecutionResult:
        """
        Execute both legs of an arbitrage trade.

        Args:
            opportunity: Validated opportunity to execute

        Returns:
            ExecutionResult with order details
        """
        logger.info(
            f"Executing arbitrage: {opportunity.outcome.value} on "
            f"{opportunity.market_kalshi.title[:50]}..."
        )

        try:
            # Step 1: Place buy order on cheaper exchange
            buy_order = self._place_buy_order(opportunity)
            if not buy_order:
                return ExecutionResult(
                    success=False,
                    error_message="Failed to place buy order"
                )

            logger.info(f"✓ Buy order placed: {buy_order.id} on {buy_order.exchange.value}")

            # Step 2: Place sell order on expensive exchange
            sell_order = self._place_sell_order(opportunity)
            if not sell_order:
                # Buy order succeeded but sell failed - in production, cancel buy order here
                logger.error("Sell order failed - in production would cancel buy order")
                return ExecutionResult(
                    success=False,
                    buy_order=buy_order,
                    error_message="Failed to place sell order (buy order may need cancellation)"
                )

            logger.info(f"✓ Sell order placed: {sell_order.id} on {sell_order.exchange.value}")

            # Both orders successful
            logger.info(
                f"✓✓ Arbitrage executed successfully! "
                f"Expected profit: ${opportunity.expected_profit:.2f}"
            )

            return ExecutionResult(
                success=True,
                buy_order=buy_order,
                sell_order=sell_order
            )

        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return ExecutionResult(
                success=False,
                error_message=str(e)
            )

    def _place_buy_order(self, opportunity: Opportunity) -> Optional[Order]:
        """Place buy order on the cheaper exchange"""
        # Determine which exchange to buy on
        buy_exchange = Exchange(opportunity.buy_exchange)
        market_id = (
            opportunity.market_kalshi.id
            if buy_exchange == Exchange.KALSHI
            else opportunity.market_polymarket.id
        )

        # Create order object
        order = Order(
            id=str(uuid.uuid4()),
            platform_order_id=None,  # Will be set by exchange
            exchange=buy_exchange,
            market_id=market_id,
            outcome=opportunity.outcome,
            side=OrderSide.BUY,
            quantity=opportunity.recommended_size,
            price=opportunity.buy_price or 0.5,
            filled_quantity=0,
            average_fill_price=0.0,
            status=OrderStatus.PENDING,
            timestamp=datetime.now()
        )

        if self.paper_trading:
            # Simulate order execution
            order.platform_order_id = f"paper_{uuid.uuid4().hex[:8]}"
            order.status = OrderStatus.FILLED
            order.filled_quantity = order.quantity
            order.average_fill_price = order.price
            order.filled_at = datetime.now()
            logger.debug(f"Paper trading: Buy order simulated")
        else:
            # TODO: Implement real API calls here
            # order = exchange_client.place_order(...)
            raise NotImplementedError("Real trading not yet implemented")

        return order

    def _place_sell_order(self, opportunity: Opportunity) -> Optional[Order]:
        """Place sell order on the more expensive exchange"""
        # Determine which exchange to sell on
        sell_exchange = Exchange(opportunity.sell_exchange)
        market_id = (
            opportunity.market_kalshi.id
            if sell_exchange == Exchange.KALSHI
            else opportunity.market_polymarket.id
        )

        # Create order object
        order = Order(
            id=str(uuid.uuid4()),
            platform_order_id=None,
            exchange=sell_exchange,
            market_id=market_id,
            outcome=opportunity.outcome,
            side=OrderSide.SELL,
            quantity=opportunity.recommended_size,
            price=opportunity.sell_price or 0.5,
            filled_quantity=0,
            average_fill_price=0.0,
            status=OrderStatus.PENDING,
            timestamp=datetime.now()
        )

        if self.paper_trading:
            # Simulate order execution
            order.platform_order_id = f"paper_{uuid.uuid4().hex[:8]}"
            order.status = OrderStatus.FILLED
            order.filled_quantity = order.quantity
            order.average_fill_price = order.price
            order.filled_at = datetime.now()
            logger.debug(f"Paper trading: Sell order simulated")
        else:
            # TODO: Implement real API calls here
            raise NotImplementedError("Real trading not yet implemented")

        return order
