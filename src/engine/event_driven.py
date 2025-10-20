"""
Event-Driven Arbitrage Engine

Captures arbitrage opportunities immediately when new markets are created
by listening to platform webhooks/streams and finding cross-platform matches.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from .bot import ArbitrageBot
from ..platforms import get_market_api

@dataclass
class MarketEvent:
    """Represents a new market creation event"""
    platform: str
    event_id: str
    title: str
    yes_price: float
    no_price: float
    volume: float
    liquidity: float
    created_at: datetime
    tags: List[str] = None

class EventDrivenArbitrage:
    """Real-time arbitrage engine that responds to market creation events"""
    
    def __init__(self, min_edge_bps: int = 100, max_trade_size: float = 100):
        self.bot = ArbitrageBot()
        self.min_edge_bps = min_edge_bps  # Minimum 1% edge
        self.max_trade_size = max_trade_size
        self.active_listeners = {}
        self.recent_markets = {}  # Cache of recent markets by platform
        self.executed_pairs = set()  # Track executed arbitrage pairs
        
        # Callbacks for different events
        self.on_opportunity_found: Optional[Callable] = None
        self.on_trade_executed: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
        print("🎯 Event-Driven Arbitrage Engine initialized")
        print(f"   Min edge: {min_edge_bps} bps ({min_edge_bps/100}%)")
        print(f"   Max trade size: ${max_trade_size}")
    
    async def start_real_time_monitoring(self):
        """Start monitoring all platforms for new market events"""
        print("\n🔴 Starting real-time market monitoring...")
        
        # Start listeners for each platform
        tasks = []
        for platform in self.bot.api_keys.keys():
            task = asyncio.create_task(self._monitor_platform(platform))
            tasks.append(task)
            self.active_listeners[platform] = task
        
        # Start cross-platform matching engine
        matching_task = asyncio.create_task(self._cross_platform_matcher())
        tasks.append(matching_task)
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            print("\n🛑 Stopping real-time monitoring...")
            await self._stop_all_listeners()
    
    async def _monitor_platform(self, platform: str):
        """Monitor a specific platform for new market events"""
        print(f"📡 Starting {platform} event listener...")
        
        while True:
            try:
                # In real implementation, this would be a WebSocket or webhook listener
                # For demo, we'll simulate by polling with change detection
                new_markets = await self._get_new_markets(platform)
                
                for market in new_markets:
                    await self._handle_new_market_event(market)
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"❌ Error monitoring {platform}: {e}")
                if self.on_error:
                    await self.on_error(platform, str(e))
                await asyncio.sleep(30)  # Wait longer on error
    
    async def _get_new_markets(self, platform: str) -> List[MarketEvent]:
        """Get new markets from a platform (simulate real-time data)"""
        try:
            api = get_market_api(platform, self.bot.api_keys[platform])
            current_markets = api.get_recent_markets(min_volume=0)
            
            # Track what we've seen before
            if platform not in self.recent_markets:
                self.recent_markets[platform] = set()
            
            new_markets = []
            for market in current_markets:
                market_id = market['id']
                if market_id not in self.recent_markets[platform]:
                    # New market detected!
                    event = MarketEvent(
                        platform=platform,
                        event_id=market_id,
                        title=market['title'],
                        yes_price=market['yes_price'],
                        no_price=market['no_price'],
                        volume=market['volume'],
                        liquidity=market['liquidity'],
                        created_at=datetime.now(),
                        tags=self._extract_tags(market['title'])
                    )
                    new_markets.append(event)
                    self.recent_markets[platform].add(market_id)
            
            return new_markets
            
        except Exception as e:
            print(f"Error fetching markets from {platform}: {e}")
            return []
    
    def _extract_tags(self, title: str) -> List[str]:
        """Extract relevant tags from market title for matching"""
        tags = []
        title_lower = title.lower()
        
        # Entity tags
        entities = {
            'trump': ['trump', 'donald', 'djt'],
            'biden': ['biden', 'joe'],
            'fed': ['fed', 'federal reserve', 'jerome powell', 'rate'],
            'apple': ['apple', 'aapl'],
            'tesla': ['tesla', 'tsla', 'musk'],
            'election': ['election', 'president', 'electoral'],
            'earnings': ['earnings', 'revenue', 'beats', 'exceeds'],
            'stock': ['stock', 'share', 'market cap'],
        }
        
        for tag, keywords in entities.items():
            if any(keyword in title_lower for keyword in keywords):
                tags.append(tag)
        
        return tags
    
    async def _handle_new_market_event(self, event: MarketEvent):
        """Handle a new market creation event"""
        print(f"\n🆕 NEW MARKET: [{event.platform}] {event.title}")
        print(f"    ID: {event.event_id}")
        print(f"    Prices: YES ${event.yes_price:.3f}, NO ${event.no_price:.3f}")
        print(f"    Tags: {event.tags}")
        
        # Immediately search for arbitrage opportunities
        opportunities = await self._find_immediate_arbitrage(event)
        
        for opp in opportunities:
            if opp['edge_bps'] >= self.min_edge_bps:
                await self._execute_arbitrage_opportunity(opp)
    
    async def _find_immediate_arbitrage(self, new_event: MarketEvent) -> List[Dict]:
        """Find arbitrage opportunities for a newly created market"""
        opportunities = []
        
        # Search other platforms for matching events
        for platform in self.bot.api_keys.keys():
            if platform == new_event.platform:
                continue
                
            try:
                # Search by tags first (most accurate)
                matches = await self._find_matching_markets(new_event, platform)
                
                for match in matches:
                    arb_opportunities = self._calculate_immediate_arbitrage(new_event, match)
                    opportunities.extend(arb_opportunities)
                    
            except Exception as e:
                print(f"Error searching {platform}: {e}")
        
        return opportunities
    
    async def _find_matching_markets(self, event: MarketEvent, target_platform: str) -> List[Dict]:
        """Find markets on target platform that match the new event"""
        try:
            api = get_market_api(target_platform, self.bot.api_keys[target_platform])
            
            # Strategy 1: Search by extracted tags
            matches = []
            for tag in event.tags:
                tag_matches = api.find_event(tag, limit=3)
                matches.extend(tag_matches)
            
            # Strategy 2: Search by key terms from title
            key_terms = self._extract_key_terms(event.title)
            for term in key_terms:
                term_matches = api.find_event(term, limit=2)
                matches.extend(term_matches)
            
            # Remove duplicates and filter by similarity
            unique_matches = []
            seen_ids = set()
            
            for match in matches:
                if match['id'] not in seen_ids:
                    # Additional similarity check
                    if self._is_similar_event(event.title, match['title']):
                        unique_matches.append(match)
                        seen_ids.add(match['id'])
            
            return unique_matches
            
        except Exception as e:
            print(f"Error finding matches on {target_platform}: {e}")
            return []
    
    def _extract_key_terms(self, title: str) -> List[str]:
        """Extract key search terms from title"""
        import re
        
        # Remove common words
        stop_words = {'will', 'be', 'by', 'before', 'after', 'on', 'the', 'a', 'an', 'and', 'or', 'in', 'to'}
        
        # Extract meaningful words (3+ characters)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', title.lower())
        key_terms = [word for word in words if word not in stop_words]
        
        # Return top 3 most important terms
        return key_terms[:3]
    
    def _is_similar_event(self, title1: str, title2: str, threshold: float = 0.4) -> bool:
        """Check if two titles represent similar events"""
        # Simple word overlap similarity
        words1 = set(title1.lower().split())
        words2 = set(title2.lower().split())
        
        if not words1 or not words2:
            return False
        
        overlap = len(words1.intersection(words2))
        total = len(words1.union(words2))
        
        return (overlap / total) >= threshold
    
    def _calculate_immediate_arbitrage(self, event1: MarketEvent, market2: Dict) -> List[Dict]:
        """Calculate arbitrage between new event and existing market"""
        opportunities = []
        
        # Convert MarketEvent to dict format for consistency
        market1 = {
            'id': event1.event_id,
            'platform': event1.platform,
            'title': event1.title,
            'yes_price': event1.yes_price,
            'no_price': event1.no_price,
            'volume': event1.volume,
            'liquidity': event1.liquidity
        }
        
        # Calculate YES arbitrage
        yes_spread = abs(market1['yes_price'] - market2['yes_price'])
        if yes_spread > 0.01:  # Minimum 1 cent spread
            if market1['yes_price'] < market2['yes_price']:
                buy_market, sell_market = market1, market2
                profit = market2['yes_price'] - market1['yes_price']
            else:
                buy_market, sell_market = market2, market1
                profit = market1['yes_price'] - market2['yes_price']
            
            edge_bps = int(profit * 10000)  # Convert to basis points
            
            if edge_bps > 0:
                opportunities.append({
                    'type': 'immediate_arbitrage',
                    'outcome': 'YES',
                    'buy_market': buy_market,
                    'sell_market': sell_market,
                    'buy_price': buy_market['yes_price'],
                    'sell_price': sell_market['yes_price'],
                    'spread': yes_spread,
                    'expected_profit': profit,
                    'edge_bps': edge_bps,
                    'trade_amount': min(self.max_trade_size, buy_market['liquidity'] / 10),
                    'detected_at': datetime.now(),
                    'new_market_id': event1.event_id
                })
        
        # Calculate NO arbitrage
        no_spread = abs(market1['no_price'] - market2['no_price'])
        if no_spread > 0.01:
            if market1['no_price'] < market2['no_price']:
                buy_market, sell_market = market1, market2
                profit = market2['no_price'] - market1['no_price']
            else:
                buy_market, sell_market = market2, market1
                profit = market1['no_price'] - market2['no_price']
            
            edge_bps = int(profit * 10000)
            
            if edge_bps > 0:
                opportunities.append({
                    'type': 'immediate_arbitrage',
                    'outcome': 'NO',
                    'buy_market': buy_market,
                    'sell_market': sell_market,
                    'buy_price': buy_market['no_price'],
                    'sell_price': sell_market['no_price'],
                    'spread': no_spread,
                    'expected_profit': profit,
                    'edge_bps': edge_bps,
                    'trade_amount': min(self.max_trade_size, buy_market['liquidity'] / 10),
                    'detected_at': datetime.now(),
                    'new_market_id': event1.event_id
                })
        
        return opportunities
    
    async def _execute_arbitrage_opportunity(self, opportunity: Dict):
        """Execute an arbitrage opportunity immediately"""
        pair_key = f"{opportunity['buy_market']['id']}-{opportunity['sell_market']['id']}-{opportunity['outcome']}"
        
        # Avoid duplicate executions
        if pair_key in self.executed_pairs:
            return
        
        print(f"\n💰 ARBITRAGE OPPORTUNITY DETECTED!")
        print(f"    Edge: {opportunity['edge_bps']} bps ({opportunity['edge_bps']/100:.2f}%)")
        print(f"    Profit: ${opportunity['expected_profit']:.4f}")
        print(f"    Buy: [{opportunity['buy_market']['platform']}] {opportunity['outcome']} @ ${opportunity['buy_price']:.3f}")
        print(f"    Sell: [{opportunity['sell_market']['platform']}] {opportunity['outcome']} @ ${opportunity['sell_price']:.3f}")
        
        if self.on_opportunity_found:
            await self.on_opportunity_found(opportunity)
        
        # Execute the arbitrage
        try:
            result = await self._execute_trades(opportunity)
            self.executed_pairs.add(pair_key)
            
            if result['success']:
                print(f"    ✅ ARBITRAGE EXECUTED SUCCESSFULLY!")
                if self.on_trade_executed:
                    await self.on_trade_executed(opportunity, result)
            else:
                print(f"    ❌ EXECUTION FAILED: {result.get('error')}")
        
        except Exception as e:
            print(f"    ❌ EXECUTION ERROR: {e}")
            if self.on_error:
                await self.on_error('execution', str(e))
    
    async def _execute_trades(self, opportunity: Dict) -> Dict:
        """Execute both legs of the arbitrage trade"""
        try:
            buy_result = self.bot.execute_trade(
                platform=opportunity['buy_market']['platform'],
                event_id=opportunity['buy_market']['id'],
                outcome=opportunity['outcome'],
                action='BUY',
                amount=opportunity['trade_amount'],
                price=opportunity['buy_price']
            )
            
            if not buy_result.get('success'):
                return {'success': False, 'error': f"Buy failed: {buy_result.get('error')}"}
            
            # Small delay between trades
            await asyncio.sleep(0.5)
            
            sell_result = self.bot.execute_trade(
                platform=opportunity['sell_market']['platform'],
                event_id=opportunity['sell_market']['id'],
                outcome=opportunity['outcome'],
                action='SELL',
                amount=opportunity['trade_amount'],
                price=opportunity['sell_price']
            )
            
            if not sell_result.get('success'):
                return {'success': False, 'error': f"Sell failed: {sell_result.get('error')}"}
            
            return {
                'success': True,
                'buy_result': buy_result,
                'sell_result': sell_result,
                'profit': opportunity['expected_profit'] * opportunity['trade_amount']
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _cross_platform_matcher(self):
        """Continuously check for arbitrage opportunities between existing markets"""
        print("🔄 Starting cross-platform matching engine...")
        
        while True:
            try:
                # Run traditional arbitrage scan every 30 seconds
                opportunities = self.bot.strategy.find_opportunities(self.bot.collect_market_data())
                
                for opp in opportunities:
                    opp['edge_bps'] = int(opp['expected_profit'] * 10000)
                    if opp['edge_bps'] >= self.min_edge_bps:
                        await self._execute_arbitrage_opportunity(opp)
                
                await asyncio.sleep(30)
                
            except Exception as e:
                print(f"❌ Cross-platform matching error: {e}")
                await asyncio.sleep(60)
    
    async def _stop_all_listeners(self):
        """Stop all platform listeners"""
        for platform, task in self.active_listeners.items():
            task.cancel()
            print(f"🛑 Stopped {platform} listener")
    
    def set_callbacks(self, 
                     on_opportunity: Callable = None,
                     on_execution: Callable = None,
                     on_error: Callable = None):
        """Set callback functions for events"""
        self.on_opportunity_found = on_opportunity
        self.on_trade_executed = on_execution  
        self.on_error = on_error


# Usage example
async def main():
    """Example usage of event-driven arbitrage"""
    
    # Initialize with custom parameters
    arbitrage = EventDrivenArbitrage(
        min_edge_bps=150,  # 1.5% minimum edge
        max_trade_size=50  # $50 max per trade
    )
    
    # Set up callbacks for monitoring
    async def on_opportunity_found(opp):
        print(f"📧 ALERT: {opp['edge_bps']} bps opportunity found!")
        # Could send Discord/Telegram notification here
    
    async def on_trade_executed(opp, result):
        profit = result.get('profit', 0)
        print(f"💰 PROFIT: ${profit:.2f} from arbitrage")
        # Could log to database here
    
    async def on_error(source, error):
        print(f"🚨 ERROR in {source}: {error}")
        # Could send error alerts here
    
    arbitrage.set_callbacks(on_opportunity_found, on_trade_executed, on_error)
    
    # Start real-time monitoring
    await arbitrage.start_real_time_monitoring()

if __name__ == "__main__":
    asyncio.run(main())