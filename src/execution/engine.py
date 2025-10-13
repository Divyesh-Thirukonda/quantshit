"""
Order execution engine for managing trades across platforms.
"""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from src.strategies.base import TradingSignal, ArbitrageOpportunity
from src.core.logger import get_logger
from src.core.config import get_settings

logger = get_logger(__name__)


class OrderStatus(Enum):
    """Order status enumeration."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderType(Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


@dataclass
class Order:
    """Order representation."""
    order_id: str
    platform: str
    market_id: str
    side: str  # "buy" or "sell"
    outcome: str  # "yes" or "no"
    quantity: float
    order_type: OrderType
    price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    avg_fill_price: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @property
    def is_active(self) -> bool:
        """Check if order is still active."""
        return self.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED]
    
    @property
    def remaining_quantity(self) -> float:
        """Get remaining quantity to fill."""
        return self.quantity - self.filled_quantity
    
    @property
    def fill_percentage(self) -> float:
        """Get fill percentage."""
        return (self.filled_quantity / self.quantity) * 100 if self.quantity > 0 else 0.0


@dataclass
class ExecutionResult:
    """Result of order execution."""
    success: bool
    order: Optional[Order] = None
    error_message: Optional[str] = None
    platform_order_id: Optional[str] = None


class BaseTradingClient:
    """Base class for platform trading clients."""
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self._is_connected = False
    
    async def connect(self) -> bool:
        """Connect to trading platform."""
        raise NotImplementedError
    
    async def disconnect(self) -> None:
        """Disconnect from trading platform."""
        raise NotImplementedError
    
    async def place_order(self, order: Order) -> ExecutionResult:
        """Place an order."""
        raise NotImplementedError
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        raise NotImplementedError
    
    async def get_order_status(self, order_id: str) -> Optional[Order]:
        """Get order status."""
        raise NotImplementedError
    
    async def get_portfolio(self) -> Dict[str, Any]:
        """Get portfolio positions."""
        raise NotImplementedError
    
    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance."""
        raise NotImplementedError


class OrderManager:
    """Manages orders across multiple platforms."""
    
    def __init__(self):
        self.trading_clients: Dict[str, BaseTradingClient] = {}
        self.active_orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []
        self.settings = get_settings()
        self.order_counter = 0
    
    def add_trading_client(self, client: BaseTradingClient) -> None:
        """Add a trading client."""
        self.trading_clients[client.platform_name] = client
    
    def remove_trading_client(self, platform_name: str) -> None:
        """Remove a trading client."""
        if platform_name in self.trading_clients:
            del self.trading_clients[platform_name]
    
    async def connect_all_clients(self) -> Dict[str, bool]:
        """Connect to all trading clients."""
        results = {}
        for platform, client in self.trading_clients.items():
            try:
                results[platform] = await client.connect()
                logger.info(f"Connected to {platform} trading client: {results[platform]}")
            except Exception as e:
                logger.error(f"Failed to connect to {platform}: {e}")
                results[platform] = False
        return results
    
    async def disconnect_all_clients(self) -> None:
        """Disconnect from all trading clients."""
        for platform, client in self.trading_clients.items():
            try:
                await client.disconnect()
                logger.info(f"Disconnected from {platform}")
            except Exception as e:
                logger.error(f"Error disconnecting from {platform}: {e}")
    
    def generate_order_id(self) -> str:
        """Generate unique order ID."""
        self.order_counter += 1
        return f"ORD_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{self.order_counter:04d}"
    
    async def execute_signal(self, signal: TradingSignal) -> ExecutionResult:
        """Execute a trading signal."""
        try:
            # Get trading client for the platform
            client = self.trading_clients.get(signal.platform)
            if not client:
                return ExecutionResult(
                    success=False,
                    error_message=f"No trading client for platform {signal.platform}"
                )
            
            # Create order from signal
            order = self._create_order_from_signal(signal)
            
            # Execute order
            result = await client.place_order(order)
            
            if result.success and result.order:
                # Store order
                self.active_orders[result.order.order_id] = result.order
                logger.info(f"Order executed successfully: {result.order.order_id}")
                
                # Start monitoring order
                asyncio.create_task(self._monitor_order(result.order.order_id))
            
            return result
        
        except Exception as e:
            logger.error(f"Error executing signal: {e}")
            return ExecutionResult(
                success=False,
                error_message=str(e)
            )
    
    async def execute_arbitrage_opportunity(self, opportunity: ArbitrageOpportunity) -> List[ExecutionResult]:
        """Execute an arbitrage opportunity (multiple orders)."""
        results = []
        
        try:
            # For cross-platform arbitrage, we need to place orders on multiple platforms
            if opportunity.opportunity_type == "cross_platform":
                results = await self._execute_cross_platform_arbitrage(opportunity)
            elif opportunity.opportunity_type == "correlation":
                results = await self._execute_correlation_arbitrage(opportunity)
            else:
                logger.warning(f"Unknown opportunity type: {opportunity.opportunity_type}")
        
        except Exception as e:
            logger.error(f"Error executing arbitrage opportunity: {e}")
            results.append(ExecutionResult(
                success=False,
                error_message=str(e)
            ))
        
        return results
    
    def _create_order_from_signal(self, signal: TradingSignal) -> Order:
        """Create an order from a trading signal."""
        order_id = self.generate_order_id()
        
        # Determine order type and price
        order_type = OrderType.LIMIT if signal.price_target else OrderType.MARKET
        price = signal.price_target if order_type == OrderType.LIMIT else None
        
        # Set expiration (default 30 minutes for limit orders)
        expires_at = None
        if order_type == OrderType.LIMIT:
            expires_at = datetime.utcnow() + timedelta(seconds=self.settings.order_timeout)
        
        return Order(
            order_id=order_id,
            platform=signal.platform,
            market_id=signal.market_id,
            side=signal.signal_type.value,
            outcome=signal.outcome,
            quantity=signal.suggested_size,
            order_type=order_type,
            price=price,
            expires_at=expires_at,
            metadata={
                "strategy": signal.strategy_name,
                "confidence": signal.confidence,
                "signal_metadata": signal.metadata
            }
        )
    
    async def _execute_cross_platform_arbitrage(self, opportunity: ArbitrageOpportunity) -> List[ExecutionResult]:
        """Execute cross-platform arbitrage opportunity."""
        results = []
        
        if len(opportunity.markets) < 2:
            return [ExecutionResult(success=False, error_message="Need at least 2 markets for cross-platform arbitrage")]
        
        market1 = opportunity.markets[0]
        market2 = opportunity.markets[1]
        
        # Determine which market to buy and which to sell
        if market1["yes_price"] < market2["yes_price"]:
            # Buy on market1, sell on market2
            buy_market = market1
            sell_market = market2
        else:
            # Buy on market2, sell on market1
            buy_market = market2
            sell_market = market1
        
        # Calculate position size
        position_size = min(100.0, opportunity.required_capital / max(buy_market["yes_price"], sell_market["yes_price"]))
        
        # Create and execute buy order
        buy_order = Order(
            order_id=self.generate_order_id(),
            platform=buy_market["platform"],
            market_id=buy_market["market_id"],
            side="buy",
            outcome="yes",
            quantity=position_size,
            order_type=OrderType.LIMIT,
            price=buy_market["yes_price"],
            expires_at=datetime.utcnow() + timedelta(minutes=5),
            metadata={"opportunity_id": opportunity.opportunity_id, "leg": "buy"}
        )
        
        # Create and execute sell order
        sell_order = Order(
            order_id=self.generate_order_id(),
            platform=sell_market["platform"],
            market_id=sell_market["market_id"],
            side="sell",
            outcome="yes",
            quantity=position_size,
            order_type=OrderType.LIMIT,
            price=sell_market["yes_price"],
            expires_at=datetime.utcnow() + timedelta(minutes=5),
            metadata={"opportunity_id": opportunity.opportunity_id, "leg": "sell"}
        )
        
        # Execute orders simultaneously
        buy_client = self.trading_clients.get(buy_market["platform"])
        sell_client = self.trading_clients.get(sell_market["platform"])
        
        if buy_client and sell_client:
            buy_task = buy_client.place_order(buy_order)
            sell_task = sell_client.place_order(sell_order)
            
            buy_result, sell_result = await asyncio.gather(buy_task, sell_task, return_exceptions=True)
            
            if isinstance(buy_result, Exception):
                buy_result = ExecutionResult(success=False, error_message=str(buy_result))
            if isinstance(sell_result, Exception):
                sell_result = ExecutionResult(success=False, error_message=str(sell_result))
            
            results = [buy_result, sell_result]
            
            # Store successful orders
            for result in results:
                if result.success and result.order:
                    self.active_orders[result.order.order_id] = result.order
                    asyncio.create_task(self._monitor_order(result.order.order_id))
        
        return results
    
    async def _execute_correlation_arbitrage(self, opportunity: ArbitrageOpportunity) -> List[ExecutionResult]:
        """Execute correlation arbitrage opportunity."""
        results = []
        
        if len(opportunity.markets) < 2:
            return [ExecutionResult(success=False, error_message="Need at least 2 markets for correlation arbitrage")]
        
        market1 = opportunity.markets[0]
        market2 = opportunity.markets[1]
        
        # Determine position sizes and directions based on price deviations
        # This is simplified - in practice would be more sophisticated
        position_size = 100.0  # Base position size
        
        platform = market1["platform"]  # Same platform for correlation arbitrage
        client = self.trading_clients.get(platform)
        
        if not client:
            return [ExecutionResult(success=False, error_message=f"No client for platform {platform}")]
        
        # Create orders (this is simplified logic)
        orders = []
        
        # If market2 has expected_price, trade based on deviation
        if "expected_price" in market2:
            expected_price = market2["expected_price"]
            actual_price = market2["yes_price"]
            
            if actual_price > expected_price:
                # Sell overpriced market
                orders.append(Order(
                    order_id=self.generate_order_id(),
                    platform=platform,
                    market_id=market2["market_id"],
                    side="sell",
                    outcome="yes",
                    quantity=position_size,
                    order_type=OrderType.LIMIT,
                    price=actual_price,
                    expires_at=datetime.utcnow() + timedelta(minutes=10),
                    metadata={"opportunity_id": opportunity.opportunity_id, "leg": "main"}
                ))
            else:
                # Buy underpriced market
                orders.append(Order(
                    order_id=self.generate_order_id(),
                    platform=platform,
                    market_id=market2["market_id"],
                    side="buy",
                    outcome="yes",
                    quantity=position_size,
                    order_type=OrderType.LIMIT,
                    price=actual_price,
                    expires_at=datetime.utcnow() + timedelta(minutes=10),
                    metadata={"opportunity_id": opportunity.opportunity_id, "leg": "main"}
                ))
        
        # Execute orders
        for order in orders:
            try:
                result = await client.place_order(order)
                results.append(result)
                
                if result.success and result.order:
                    self.active_orders[result.order.order_id] = result.order
                    asyncio.create_task(self._monitor_order(result.order.order_id))
            
            except Exception as e:
                results.append(ExecutionResult(success=False, error_message=str(e)))
        
        return results
    
    async def _monitor_order(self, order_id: str) -> None:
        """Monitor an order for updates."""
        try:
            order = self.active_orders.get(order_id)
            if not order:
                return
            
            client = self.trading_clients.get(order.platform)
            if not client:
                return
            
            # Monitor order for updates
            while order.is_active and order_id in self.active_orders:
                try:
                    updated_order = await client.get_order_status(order_id)
                    if updated_order:
                        # Update order status
                        self.active_orders[order_id] = updated_order
                        
                        # If order is no longer active, move to history
                        if not updated_order.is_active:
                            self.order_history.append(updated_order)
                            del self.active_orders[order_id]
                            logger.info(f"Order {order_id} completed with status: {updated_order.status}")
                            break
                    
                    await asyncio.sleep(5)  # Check every 5 seconds
                
                except Exception as e:
                    logger.error(f"Error monitoring order {order_id}: {e}")
                    await asyncio.sleep(10)
        
        except Exception as e:
            logger.error(f"Error in order monitoring: {e}")
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an active order."""
        try:
            order = self.active_orders.get(order_id)
            if not order:
                logger.warning(f"Order {order_id} not found in active orders")
                return False
            
            client = self.trading_clients.get(order.platform)
            if not client:
                logger.error(f"No client for platform {order.platform}")
                return False
            
            success = await client.cancel_order(order_id)
            
            if success:
                # Update order status
                order.status = OrderStatus.CANCELLED
                self.order_history.append(order)
                del self.active_orders[order_id]
                logger.info(f"Order {order_id} cancelled successfully")
            
            return success
        
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    async def cancel_all_orders(self) -> Dict[str, bool]:
        """Cancel all active orders."""
        results = {}
        
        for order_id in list(self.active_orders.keys()):
            results[order_id] = await self.cancel_order(order_id)
        
        return results
    
    def get_active_orders(self) -> Dict[str, Order]:
        """Get all active orders."""
        return self.active_orders.copy()
    
    def get_order_history(self) -> List[Order]:
        """Get order history."""
        return self.order_history.copy()
    
    def get_platform_orders(self, platform: str) -> List[Order]:
        """Get orders for a specific platform."""
        platform_orders = []
        
        # Active orders
        for order in self.active_orders.values():
            if order.platform == platform:
                platform_orders.append(order)
        
        # Historical orders
        for order in self.order_history:
            if order.platform == platform:
                platform_orders.append(order)
        
        return platform_orders