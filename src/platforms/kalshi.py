"""
Kalshi platform implementation for data and trading.
"""
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import json
from src.data.providers import BaseDataProvider, MarketData, OrderBook, OrderBookEntry, MarketStatus
from src.core.config import get_settings
from src.core.logger import get_logger

logger = get_logger(__name__)


class KalshiDataProvider(BaseDataProvider):
    """Kalshi data provider implementation."""
    
    def __init__(self):
        super().__init__("kalshi")
        self.settings = get_settings()
        self.base_url = self.settings.kalshi_api_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.auth_token: Optional[str] = None
        self.subscriptions: Dict[str, Any] = {}
    
    async def connect(self) -> bool:
        """Connect to Kalshi API."""
        try:
            self.session = aiohttp.ClientSession()
            
            # Authenticate if credentials are provided
            if self.settings.kalshi_email and self.settings.kalshi_password:
                await self._authenticate()
            
            self._is_connected = True
            logger.info("Connected to Kalshi API")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Kalshi: {e}")
            self._is_connected = False
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Kalshi API."""
        if self.session:
            await self.session.close()
        self._is_connected = False
        logger.info("Disconnected from Kalshi API")
    
    async def _authenticate(self) -> None:
        """Authenticate with Kalshi API."""
        auth_data = {
            "email": self.settings.kalshi_email,
            "password": self.settings.kalshi_password
        }
        
        async with self.session.post(f"{self.base_url}/login", json=auth_data) as response:
            if response.status == 200:
                data = await response.json()
                self.auth_token = data.get("token")
                logger.info("Successfully authenticated with Kalshi")
            else:
                logger.error(f"Authentication failed: {response.status}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers
    
    async def get_markets(self, category: Optional[str] = None) -> List[MarketData]:
        """Get all available markets from Kalshi."""
        if not self.session:
            return []
        
        try:
            params = {}
            if category:
                params["category"] = category
            
            async with self.session.get(
                f"{self.base_url}/markets",
                params=params,
                headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    markets = []
                    
                    for market_data in data.get("markets", []):
                        market = self._parse_market_data(market_data)
                        if market:
                            markets.append(market)
                    
                    logger.info(f"Retrieved {len(markets)} markets from Kalshi")
                    return markets
                else:
                    logger.error(f"Failed to get markets: {response.status}")
                    return []
        
        except Exception as e:
            logger.error(f"Error getting markets: {e}")
            return []
    
    async def get_market_data(self, market_id: str) -> Optional[MarketData]:
        """Get data for a specific market."""
        if not self.session:
            return None
        
        try:
            async with self.session.get(
                f"{self.base_url}/markets/{market_id}",
                headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_market_data(data.get("market", {}))
                else:
                    logger.error(f"Failed to get market {market_id}: {response.status}")
                    return None
        
        except Exception as e:
            logger.error(f"Error getting market {market_id}: {e}")
            return None
    
    async def get_order_book(self, market_id: str) -> Optional[OrderBook]:
        """Get order book for a market."""
        if not self.session:
            return None
        
        try:
            async with self.session.get(
                f"{self.base_url}/markets/{market_id}/orderbook",
                headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_order_book(market_id, data)
                else:
                    logger.error(f"Failed to get order book for {market_id}: {response.status}")
                    return None
        
        except Exception as e:
            logger.error(f"Error getting order book for {market_id}: {e}")
            return None
    
    async def subscribe_to_market(self, market_id: str, callback) -> bool:
        """Subscribe to real-time market updates."""
        # Kalshi doesn't have websockets in their public API
        # We'll implement polling for now
        logger.info(f"Setting up polling subscription for market {market_id}")
        
        async def poll_market():
            while market_id in self.subscriptions:
                try:
                    market_data = await self.get_market_data(market_id)
                    if market_data:
                        await callback(market_data)
                    await asyncio.sleep(5)  # Poll every 5 seconds
                except Exception as e:
                    logger.error(f"Error in market polling: {e}")
                    await asyncio.sleep(10)
        
        self.subscriptions[market_id] = asyncio.create_task(poll_market())
        return True
    
    async def unsubscribe_from_market(self, market_id: str) -> bool:
        """Unsubscribe from market updates."""
        if market_id in self.subscriptions:
            self.subscriptions[market_id].cancel()
            del self.subscriptions[market_id]
            logger.info(f"Unsubscribed from market {market_id}")
            return True
        return False
    
    def _parse_market_data(self, market_data: Dict[str, Any]) -> Optional[MarketData]:
        """Parse Kalshi market data into MarketData object."""
        try:
            # Parse close date
            close_date = None
            if market_data.get("close_ts"):
                close_date = datetime.fromtimestamp(market_data["close_ts"], tz=timezone.utc)
            
            # Map Kalshi status to our enum
            status_map = {
                "open": MarketStatus.ACTIVE,
                "closed": MarketStatus.CLOSED,
                "settled": MarketStatus.SETTLED,
                "halted": MarketStatus.SUSPENDED
            }
            status = status_map.get(market_data.get("status", "open"), MarketStatus.ACTIVE)
            
            return MarketData(
                platform="kalshi",
                market_id=market_data.get("ticker", ""),
                title=market_data.get("title", ""),
                category=market_data.get("category", ""),
                description=market_data.get("subtitle", ""),
                yes_price=market_data.get("yes_bid", None),
                no_price=market_data.get("no_bid", None),
                volume=market_data.get("volume", 0.0),
                open_interest=market_data.get("open_interest", 0.0),
                close_date=close_date,
                status=status,
                last_updated=datetime.utcnow()
            )
        
        except Exception as e:
            logger.error(f"Error parsing market data: {e}")
            return None
    
    def _parse_order_book(self, market_id: str, orderbook_data: Dict[str, Any]) -> Optional[OrderBook]:
        """Parse Kalshi order book data."""
        try:
            bids = []
            asks = []
            
            # Parse yes bids (equivalent to buying yes)
            for bid_data in orderbook_data.get("yes", {}).get("bids", []):
                bids.append(OrderBookEntry(
                    price=bid_data["price"],
                    quantity=bid_data["quantity"],
                    side="bid"
                ))
            
            # Parse yes asks (equivalent to selling yes)
            for ask_data in orderbook_data.get("yes", {}).get("asks", []):
                asks.append(OrderBookEntry(
                    price=ask_data["price"],
                    quantity=ask_data["quantity"],
                    side="ask"
                ))
            
            return OrderBook(
                market_id=market_id,
                platform="kalshi",
                bids=bids,
                asks=asks,
                timestamp=datetime.utcnow()
            )
        
        except Exception as e:
            logger.error(f"Error parsing order book: {e}")
            return None


class KalshiTradingClient:
    """Kalshi trading client for order execution."""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.kalshi_api_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.auth_token: Optional[str] = None
        self.logger = get_logger(__name__)
    
    async def connect(self) -> bool:
        """Connect and authenticate."""
        try:
            self.session = aiohttp.ClientSession()
            await self._authenticate()
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect trading client: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect."""
        if self.session:
            await self.session.close()
    
    async def _authenticate(self) -> None:
        """Authenticate with Kalshi API."""
        auth_data = {
            "email": self.settings.kalshi_email,
            "password": self.settings.kalshi_password
        }
        
        async with self.session.post(f"{self.base_url}/login", json=auth_data) as response:
            if response.status == 200:
                data = await response.json()
                self.auth_token = data.get("token")
                self.logger.info("Trading client authenticated with Kalshi")
            else:
                raise Exception(f"Authentication failed: {response.status}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers
    
    async def place_order(
        self,
        market_id: str,
        side: str,  # "buy" or "sell"
        outcome: str,  # "yes" or "no"
        quantity: int,
        price: Optional[float] = None,
        order_type: str = "market"
    ) -> Dict[str, Any]:
        """Place an order on Kalshi."""
        if not self.session:
            raise Exception("Not connected")
        
        order_data = {
            "ticker": market_id,
            "type": order_type,
            "side": side,
            "action": outcome,
            "count": quantity
        }
        
        if price and order_type == "limit":
            order_data["yes_price"] = price if outcome == "yes" else None
            order_data["no_price"] = price if outcome == "no" else None
        
        try:
            async with self.session.post(
                f"{self.base_url}/portfolio/orders",
                json=order_data,
                headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.info(f"Order placed successfully: {result}")
                    return result
                else:
                    error_text = await response.text()
                    self.logger.error(f"Failed to place order: {response.status} - {error_text}")
                    raise Exception(f"Order failed: {response.status}")
        
        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            raise
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        if not self.session:
            return False
        
        try:
            async with self.session.delete(
                f"{self.base_url}/portfolio/orders/{order_id}",
                headers=self._get_headers()
            ) as response:
                success = response.status == 200
                if success:
                    self.logger.info(f"Order {order_id} cancelled successfully")
                else:
                    self.logger.error(f"Failed to cancel order {order_id}: {response.status}")
                return success
        
        except Exception as e:
            self.logger.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    async def get_portfolio(self) -> Dict[str, Any]:
        """Get current portfolio positions."""
        if not self.session:
            return {}
        
        try:
            async with self.session.get(
                f"{self.base_url}/portfolio/positions",
                headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.error(f"Failed to get portfolio: {response.status}")
                    return {}
        
        except Exception as e:
            self.logger.error(f"Error getting portfolio: {e}")
            return {}
    
    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance."""
        if not self.session:
            return {}
        
        try:
            async with self.session.get(
                f"{self.base_url}/portfolio/balance",
                headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.error(f"Failed to get balance: {response.status}")
                    return {}
        
        except Exception as e:
            self.logger.error(f"Error getting balance: {e}")
            return {}