#!/usr/bin/env python3
"""
Generate realistic demo market data with historical prices.
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List
import numpy as np


class DemoDataGenerator:
    """Generate realistic prediction market data for demo purposes"""

    # Market templates with realistic topics
    MARKET_TEMPLATES = [
        # Politics
        ("Trump wins 2024 Presidential Election", "politics", 12000000),
        ("Biden approval rating above 45% in November", "politics", 3500000),
        ("Democrats control House after 2024 election", "politics", 8500000),
        ("Republicans win Senate majority 2024", "politics", 7200000),
        ("VP Harris approval above 50% by year end", "politics", 2800000),

        # Economics
        ("Fed cuts rates in Q4 2024", "economics", 4500000),
        ("US GDP growth exceeds 2.5% in 2024", "economics", 3200000),
        ("Inflation below 3% by end of 2024", "economics", 5600000),
        ("Unemployment stays below 4% in 2024", "economics", 2100000),
        ("S&P 500 above 6000 by end of 2024", "economics", 9800000),
        ("Dow Jones above 45000 by year end", "economics", 6500000),
        ("10-year Treasury yield below 4% in December", "economics", 3800000),

        # Technology & Crypto
        ("Bitcoin reaches $100,000 by end of 2024", "crypto", 15000000),
        ("Ethereum above $5,000 by year end", "crypto", 8200000),
        ("Tesla stock hits $300 before end of 2024", "tech", 7400000),
        ("Apple stock reaches $250 by year end", "tech", 6800000),
        ("Nvidia stock above $600 by December 2024", "tech", 8900000),
        ("Meta releases new VR headset in 2024", "tech", 2400000),
        ("ChatGPT reaches 500M users by end of 2024", "tech", 4200000),

        # Markets & Finance
        ("US stock market positive returns in 2024", "finance", 5500000),
        ("Gold price above $2,500 by year end", "finance", 4300000),
        ("Oil prices stay below $100 in 2024", "finance", 3700000),
        ("Dollar Index below 100 by December", "finance", 2900000),

        # Sports & Entertainment
        ("Lakers make NBA playoffs 2024-25", "sports", 4600000),
        ("Chiefs win Super Bowl 2025", "sports", 12000000),
        ("Messi wins another Ballon d'Or 2024", "sports", 3200000),

        # Science & Weather
        ("Hurricane season 2024 above average activity", "weather", 1800000),
        ("Record high temperatures globally in 2024", "climate", 2500000),
        ("Major AI breakthrough announced in 2024", "tech", 3900000),
    ]

    def __init__(self, seed: int = 42):
        """Initialize generator with random seed for reproducibility"""
        random.seed(seed)
        np.random.seed(seed)

    def _generate_price_history(
        self,
        start_price: float,
        days: int = 30,
        volatility: float = 0.15
    ) -> List[float]:
        """Generate realistic price history using geometric Brownian motion"""
        prices = [start_price]

        for _ in range(days - 1):
            # Geometric Brownian motion
            daily_return = np.random.normal(0, volatility / np.sqrt(252))
            new_price = prices[-1] * (1 + daily_return)

            # Constrain prices between 0.01 and 0.99
            new_price = max(0.01, min(0.99, new_price))

            # Ensure yes + no = 1
            prices.append(new_price)

        return prices

    def _generate_volume_history(
        self,
        base_volume: float,
        days: int = 30
    ) -> List[float]:
        """Generate realistic volume history with random spikes"""
        volumes = []

        for i in range(days):
            # Base volume with random variation
            daily_variation = np.random.uniform(0.7, 1.3)
            volume = base_volume * daily_variation

            # Occasional volume spikes (10% chance)
            if random.random() < 0.1:
                volume *= random.uniform(1.5, 3.0)

            # Volume tends to increase over time as market approaches end
            time_factor = 1 + (i / days) * 0.5
            volume *= time_factor

            volumes.append(volume)

        return volumes

    def generate_market_with_history(
        self,
        market_id: str,
        title: str,
        platform: str,
        base_volume: float,
        category: str,
        days_history: int = 30
    ) -> Dict:
        """Generate a single market with historical data"""

        # Generate realistic starting prices based on category
        if category == "politics":
            yes_price = random.uniform(0.35, 0.65)
        elif category == "crypto":
            yes_price = random.uniform(0.20, 0.50)
        elif category == "tech":
            yes_price = random.uniform(0.30, 0.60)
        elif category == "economics":
            yes_price = random.uniform(0.40, 0.75)
        else:
            yes_price = random.uniform(0.25, 0.75)

        # Generate price history
        volatility = random.uniform(0.10, 0.25)
        yes_prices = self._generate_price_history(yes_price, days_history, volatility)

        # Generate volume history
        volumes = self._generate_volume_history(base_volume, days_history)

        # Create historical data points
        end_date = datetime.now()
        history = []

        for i in range(days_history):
            date = end_date - timedelta(days=days_history - i - 1)
            yes_price_hist = yes_prices[i]
            no_price_hist = 1 - yes_price_hist

            history.append({
                "date": date.strftime("%Y-%m-%d"),
                "yes_price": round(yes_price_hist, 4),
                "no_price": round(no_price_hist, 4),
                "volume": round(volumes[i], 2),
                "liquidity": round(volumes[i] * random.uniform(0.3, 0.5), 2)
            })

        # Current market state (most recent history)
        current = history[-1]

        return {
            "id": market_id,
            "title": title,
            "platform": platform,
            "category": category,
            "volume": current["volume"],
            "yes_price": current["yes_price"],
            "no_price": current["no_price"],
            "liquidity": current["liquidity"],
            "end_date": (end_date + timedelta(days=random.randint(30, 90))).strftime("%Y-%m-%dT23:59:59Z"),
            "history": history
        }

    def generate_platform_markets(
        self,
        platform: str,
        num_markets: int = 25,
        days_history: int = 30
    ) -> List[Dict]:
        """Generate multiple markets for a platform"""
        markets = []

        # Randomly select markets from templates
        selected = random.sample(self.MARKET_TEMPLATES, min(num_markets, len(self.MARKET_TEMPLATES)))

        for i, (title, category, base_volume) in enumerate(selected):
            # Add platform-specific variation to titles
            if platform == "kalshi":
                # Kalshi uses more formal language
                if "wins" in title.lower():
                    title = title.replace("wins", "to win")
                if "reaches" in title.lower():
                    title = title.replace("reaches", "to reach")

            # Add some volume variation by platform
            if platform == "polymarket":
                volume_mult = random.uniform(0.9, 1.2)
            elif platform == "kalshi":
                volume_mult = random.uniform(0.7, 1.1)
            else:
                volume_mult = 1.0

            market = self.generate_market_with_history(
                market_id=f"{platform}_market_{i+1}",
                title=title,
                platform=platform,
                base_volume=base_volume * volume_mult,
                category=category,
                days_history=days_history
            )
            markets.append(market)

        return markets

    def generate_all_markets(
        self,
        days_history: int = 30
    ) -> Dict[str, List[Dict]]:
        """Generate markets for all platforms"""
        return {
            "polymarket": self.generate_platform_markets("polymarket", 25, days_history),
            "kalshi": self.generate_platform_markets("kalshi", 25, days_history)
        }

    def save_to_files(self, output_dir: str = "demo"):
        """Generate and save market data to JSON files"""
        markets = self.generate_all_markets(days_history=30)

        # Save polymarket data
        with open(f"{output_dir}/polymarket_markets.json", "w") as f:
            json.dump(markets["polymarket"], f, indent=2)

        # Save kalshi data
        with open(f"{output_dir}/kalshi_markets.json", "w") as f:
            json.dump(markets["kalshi"], f, indent=2)

        print(f"Generated {len(markets['polymarket'])} Polymarket markets")
        print(f"Generated {len(markets['kalshi'])} Kalshi markets")
        print(f"Saved to {output_dir}/ directory")


if __name__ == "__main__":
    generator = DemoDataGenerator(seed=42)
    generator.save_to_files()
