"""
Scorer service - calculates profitability of matched market pairs.
Separate from matching so we can update scoring without touching match logic.
"""

import uuid
from typing import List, Tuple
from ...models import Market, Opportunity
from ...types import Outcome
from ...config import constants
from ...utils import get_logger, calculate_profit
from datetime import datetime

logger = get_logger(__name__)


class Scorer:
    """
    Calculate profitability of arbitrage opportunities.
    """

    def __init__(
        self,
        min_profit_threshold: float = constants.MIN_PROFIT_THRESHOLD,
        kalshi_fee: float = constants.FEE_KALSHI,
        polymarket_fee: float = constants.FEE_POLYMARKET,
        slippage: float = constants.SLIPPAGE_FACTOR
    ):
        """
        Initialize scorer with fee and threshold parameters.

        Args:
            min_profit_threshold: Minimum profit percentage to consider
            kalshi_fee: Kalshi fee percentage
            polymarket_fee: Polymarket fee percentage
            slippage: Slippage estimate percentage
        """
        self.min_profit_threshold = min_profit_threshold
        self.kalshi_fee = kalshi_fee
        self.polymarket_fee = polymarket_fee
        self.slippage = slippage

        logger.info(
            f"Scorer initialized - min_profit: {min_profit_threshold:.2%}, "
            f"Kalshi fee: {kalshi_fee:.2%}, Polymarket fee: {polymarket_fee:.2%}"
        )

    def score_opportunities(
        self,
        matched_pairs: List[Tuple[Market, Market, float]]
    ) -> List[Opportunity]:
        """
        Score all matched pairs and return profitable opportunities.

        Args:
            matched_pairs: List of (kalshi_market, polymarket_market, confidence)

        Returns:
            List of Opportunity objects, sorted by expected profit (highest first)
        """
        opportunities = []

        logger.info(f"Scoring {len(matched_pairs)} matched pairs")

        for kalshi_market, poly_market, confidence in matched_pairs:
            # Check both YES and NO outcomes for arbitrage
            yes_opp = self._calculate_opportunity(
                kalshi_market, poly_market, Outcome.YES, confidence
            )
            if yes_opp and yes_opp.is_profitable:
                opportunities.append(yes_opp)

            no_opp = self._calculate_opportunity(
                kalshi_market, poly_market, Outcome.NO, confidence
            )
            if no_opp and no_opp.is_profitable:
                opportunities.append(no_opp)

        # Sort by expected profit (descending)
        opportunities.sort(key=lambda opp: opp.expected_profit, reverse=True)

        logger.info(f"Found {len(opportunities)} profitable opportunities")
        return opportunities

    def _calculate_opportunity(
        self,
        kalshi_market: Market,
        poly_market: Market,
        outcome: Outcome,
        confidence: float
    ) -> Opportunity:
        """
        Calculate arbitrage opportunity for a specific outcome.

        Args:
            kalshi_market: Kalshi market
            poly_market: Polymarket market
            outcome: YES or NO
            confidence: Confidence score from matcher

        Returns:
            Opportunity object (may not be profitable - check is_profitable)
        """
        # Get prices for the outcome
        kalshi_price = kalshi_market.yes_price if outcome == Outcome.YES else kalshi_market.no_price
        poly_price = poly_market.yes_price if outcome == Outcome.YES else poly_market.no_price

        # Calculate spread (absolute difference)
        spread = abs(kalshi_price - poly_price)

        # Determine which exchange to buy/sell on
        if kalshi_price < poly_price:
            buy_price = kalshi_price
            sell_price = poly_price
            buy_fee = self.kalshi_fee
            sell_fee = self.polymarket_fee
        else:
            buy_price = poly_price
            sell_price = kalshi_price
            buy_fee = self.polymarket_fee
            sell_fee = self.kalshi_fee

        # Account for slippage
        buy_price_adjusted = buy_price * (1 + self.slippage)
        sell_price_adjusted = sell_price * (1 - self.slippage)

        # Calculate position size based on available liquidity
        max_size = int(min(kalshi_market.liquidity, poly_market.liquidity))
        recommended_size = min(max_size, constants.MAX_POSITION_SIZE)
        recommended_size = max(recommended_size, constants.MIN_POSITION_SIZE)

        # Calculate profit
        expected_profit = calculate_profit(
            buy_price=buy_price_adjusted,
            sell_price=sell_price_adjusted,
            quantity=recommended_size,
            buy_fee_pct=buy_fee,
            sell_fee_pct=sell_fee
        )

        # Calculate profit percentage
        capital_required = recommended_size * buy_price_adjusted * (1 + buy_fee)
        expected_profit_pct = (expected_profit / capital_required) if capital_required > 0 else 0.0

        # Determine expiry (use earliest of the two markets)
        expiry = None
        if kalshi_market.expiry and poly_market.expiry:
            expiry = min(kalshi_market.expiry, poly_market.expiry)
        elif kalshi_market.expiry:
            expiry = kalshi_market.expiry
        elif poly_market.expiry:
            expiry = poly_market.expiry

        # Create opportunity object
        opportunity = Opportunity(
            market_kalshi=kalshi_market,
            market_polymarket=poly_market,
            outcome=outcome,
            spread=spread,
            expected_profit=expected_profit,
            expected_profit_pct=expected_profit_pct,
            confidence_score=confidence,
            recommended_size=recommended_size,
            max_size=max_size,
            timestamp=datetime.now(),
            expiry=expiry
        )

        return opportunity
