"""
Risk management system for monitoring and controlling trading risk.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from src.execution.engine import Order, OrderStatus
from src.strategies.base import TradingSignal, ArbitrageOpportunity
from src.core.logger import get_logger
from src.core.config import get_settings

logger = get_logger(__name__)


class RiskLevel(Enum):
    """Risk level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskMetrics:
    """Risk metrics snapshot."""
    timestamp: datetime
    total_exposure: float
    daily_pnl: float
    unrealized_pnl: float
    realized_pnl: float
    var_95: float  # Value at Risk 95%
    max_drawdown: float
    position_count: int
    platform_exposures: Dict[str, float]
    correlation_exposure: float
    largest_position: float
    risk_level: RiskLevel


@dataclass
class RiskAlert:
    """Risk alert."""
    alert_id: str
    alert_type: str
    severity: RiskLevel
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    resolved: bool = False


class RiskManager:
    """Risk management system."""
    
    def __init__(self):
        self.settings = get_settings()
        self.risk_limits = {
            "max_position_size": self.settings.max_position_size,
            "max_daily_loss": self.settings.max_daily_loss,
            "max_correlation_exposure": self.settings.max_correlation_exposure,
            "max_platform_exposure": self.settings.max_position_size * 5,  # 5x single position
            "max_total_exposure": self.settings.max_position_size * 10,  # 10x single position
            "max_drawdown": 0.15,  # 15%
            "var_95_limit": self.settings.max_daily_loss * 0.5
        }
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.pnl_history: List[Dict[str, Any]] = []
        self.risk_alerts: List[RiskAlert] = []
        self.alert_counter = 0
        self.emergency_stop = False
    
    def update_positions(self, orders: List[Order]) -> None:
        """Update position tracking from orders."""
        # Reset positions
        self.positions.clear()
        
        for order in orders:
            if order.status == OrderStatus.FILLED or order.status == OrderStatus.PARTIALLY_FILLED:
                position_key = f"{order.platform}_{order.market_id}_{order.outcome}"
                
                if position_key not in self.positions:
                    self.positions[position_key] = {
                        "platform": order.platform,
                        "market_id": order.market_id,
                        "outcome": order.outcome,
                        "quantity": 0.0,
                        "avg_price": 0.0,
                        "unrealized_pnl": 0.0,
                        "market_value": 0.0
                    }
                
                position = self.positions[position_key]
                
                # Update quantity and average price
                if order.side == "buy":
                    new_quantity = position["quantity"] + order.filled_quantity
                    if new_quantity > 0:
                        position["avg_price"] = (
                            (position["avg_price"] * position["quantity"]) + 
                            (order.avg_fill_price * order.filled_quantity)
                        ) / new_quantity
                    position["quantity"] = new_quantity
                else:  # sell
                    position["quantity"] -= order.filled_quantity
                
                # Update market value (would need current prices in real implementation)
                position["market_value"] = position["quantity"] * position["avg_price"]
    
    def calculate_risk_metrics(self, current_prices: Optional[Dict[str, float]] = None) -> RiskMetrics:
        """Calculate current risk metrics."""
        try:
            timestamp = datetime.utcnow()
            
            # Calculate exposures
            total_exposure = 0.0
            platform_exposures = {}
            correlation_exposure = 0.0
            largest_position = 0.0
            unrealized_pnl = 0.0
            
            for position in self.positions.values():
                platform = position["platform"]
                market_value = abs(position["market_value"])
                
                total_exposure += market_value
                
                if platform not in platform_exposures:
                    platform_exposures[platform] = 0.0
                platform_exposures[platform] += market_value
                
                largest_position = max(largest_position, market_value)
                
                # Calculate unrealized PnL (simplified)
                if current_prices and position["market_id"] in current_prices:
                    current_price = current_prices[position["market_id"]]
                    unrealized_pnl += position["quantity"] * (current_price - position["avg_price"])
            
            # Calculate daily PnL
            daily_pnl = self._calculate_daily_pnl()
            
            # Calculate VaR (simplified historical simulation)
            var_95 = self._calculate_var_95()
            
            # Calculate max drawdown
            max_drawdown = self._calculate_max_drawdown()
            
            # Determine risk level
            risk_level = self._assess_risk_level(total_exposure, daily_pnl, max_drawdown, var_95)
            
            return RiskMetrics(
                timestamp=timestamp,
                total_exposure=total_exposure,
                daily_pnl=daily_pnl,
                unrealized_pnl=unrealized_pnl,
                realized_pnl=self._calculate_realized_pnl(),
                var_95=var_95,
                max_drawdown=max_drawdown,
                position_count=len(self.positions),
                platform_exposures=platform_exposures,
                correlation_exposure=correlation_exposure,
                largest_position=largest_position,
                risk_level=risk_level
            )
        
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return RiskMetrics(
                timestamp=datetime.utcnow(),
                total_exposure=0.0,
                daily_pnl=0.0,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                var_95=0.0,
                max_drawdown=0.0,
                position_count=0,
                platform_exposures={},
                correlation_exposure=0.0,
                largest_position=0.0,
                risk_level=RiskLevel.LOW
            )
    
    def check_signal_risk(self, signal: TradingSignal) -> tuple[bool, Optional[str]]:
        """Check if a trading signal passes risk checks."""
        try:
            # Check position size limit
            if signal.suggested_size > self.risk_limits["max_position_size"]:
                return False, f"Position size {signal.suggested_size} exceeds limit {self.risk_limits['max_position_size']}"
            
            # Check if emergency stop is active
            if self.emergency_stop:
                return False, "Emergency stop is active"
            
            # Check platform exposure
            platform_exposure = sum(
                abs(pos["market_value"]) for pos in self.positions.values() 
                if pos["platform"] == signal.platform
            )
            
            if platform_exposure + signal.suggested_size > self.risk_limits["max_platform_exposure"]:
                return False, f"Platform exposure would exceed limit"
            
            # Check total exposure
            total_exposure = sum(abs(pos["market_value"]) for pos in self.positions.values())
            
            if total_exposure + signal.suggested_size > self.risk_limits["max_total_exposure"]:
                return False, f"Total exposure would exceed limit"
            
            # Check daily loss limit
            daily_pnl = self._calculate_daily_pnl()
            if daily_pnl < -self.risk_limits["max_daily_loss"]:
                return False, f"Daily loss limit reached: {daily_pnl}"
            
            return True, None
        
        except Exception as e:
            logger.error(f"Error checking signal risk: {e}")
            return False, f"Risk check error: {str(e)}"
    
    def check_opportunity_risk(self, opportunity: ArbitrageOpportunity) -> tuple[bool, Optional[str]]:
        """Check if an arbitrage opportunity passes risk checks."""
        try:
            # Check required capital
            if opportunity.required_capital > self.risk_limits["max_position_size"]:
                return False, f"Required capital {opportunity.required_capital} exceeds position limit"
            
            # Check if emergency stop is active
            if self.emergency_stop:
                return False, "Emergency stop is active"
            
            # Check confidence threshold
            if opportunity.confidence_score < 0.5:
                return False, f"Confidence score {opportunity.confidence_score} too low"
            
            # Check correlation exposure for correlation arbitrage
            if opportunity.opportunity_type == "correlation":
                correlation_exposure = sum(
                    abs(pos["market_value"]) for pos in self.positions.values()
                    if pos.get("strategy") == "correlation_arbitrage"
                )
                
                if correlation_exposure + opportunity.required_capital > self.risk_limits["max_correlation_exposure"]:
                    return False, "Correlation exposure limit would be exceeded"
            
            return True, None
        
        except Exception as e:
            logger.error(f"Error checking opportunity risk: {e}")
            return False, f"Risk check error: {str(e)}"
    
    def generate_risk_alerts(self, risk_metrics: RiskMetrics) -> List[RiskAlert]:
        """Generate risk alerts based on current metrics."""
        alerts = []
        
        try:
            # Check daily loss
            if risk_metrics.daily_pnl < -self.risk_limits["max_daily_loss"]:
                alerts.append(self._create_alert(
                    "daily_loss_limit",
                    RiskLevel.CRITICAL,
                    f"Daily loss {risk_metrics.daily_pnl} exceeds limit {-self.risk_limits['max_daily_loss']}",
                    {"daily_pnl": risk_metrics.daily_pnl, "limit": -self.risk_limits["max_daily_loss"]}
                ))
            
            # Check total exposure
            if risk_metrics.total_exposure > self.risk_limits["max_total_exposure"]:
                alerts.append(self._create_alert(
                    "total_exposure_limit",
                    RiskLevel.HIGH,
                    f"Total exposure {risk_metrics.total_exposure} exceeds limit {self.risk_limits['max_total_exposure']}",
                    {"exposure": risk_metrics.total_exposure, "limit": self.risk_limits["max_total_exposure"]}
                ))
            
            # Check max drawdown
            if risk_metrics.max_drawdown > self.risk_limits["max_drawdown"]:
                alerts.append(self._create_alert(
                    "max_drawdown",
                    RiskLevel.HIGH,
                    f"Max drawdown {risk_metrics.max_drawdown:.2%} exceeds limit {self.risk_limits['max_drawdown']:.2%}",
                    {"drawdown": risk_metrics.max_drawdown, "limit": self.risk_limits["max_drawdown"]}
                ))
            
            # Check VaR
            if risk_metrics.var_95 > self.risk_limits["var_95_limit"]:
                alerts.append(self._create_alert(
                    "var_95_limit",
                    RiskLevel.MEDIUM,
                    f"VaR 95% {risk_metrics.var_95} exceeds limit {self.risk_limits['var_95_limit']}",
                    {"var_95": risk_metrics.var_95, "limit": self.risk_limits["var_95_limit"]}
                ))
            
            # Check platform concentration
            for platform, exposure in risk_metrics.platform_exposures.items():
                if exposure > self.risk_limits["max_platform_exposure"]:
                    alerts.append(self._create_alert(
                        "platform_concentration",
                        RiskLevel.MEDIUM,
                        f"Platform {platform} exposure {exposure} exceeds limit {self.risk_limits['max_platform_exposure']}",
                        {"platform": platform, "exposure": exposure, "limit": self.risk_limits["max_platform_exposure"]}
                    ))
        
        except Exception as e:
            logger.error(f"Error generating risk alerts: {e}")
        
        # Add to alerts history
        self.risk_alerts.extend(alerts)
        
        return alerts
    
    def activate_emergency_stop(self, reason: str) -> None:
        """Activate emergency stop."""
        self.emergency_stop = True
        logger.critical(f"EMERGENCY STOP ACTIVATED: {reason}")
        
        alert = self._create_alert(
            "emergency_stop",
            RiskLevel.CRITICAL,
            f"Emergency stop activated: {reason}",
            {"reason": reason}
        )
        self.risk_alerts.append(alert)
    
    def deactivate_emergency_stop(self) -> None:
        """Deactivate emergency stop."""
        self.emergency_stop = False
        logger.info("Emergency stop deactivated")
    
    def _calculate_daily_pnl(self) -> float:
        """Calculate daily PnL."""
        # Simplified calculation - would use actual trade data in production
        today = datetime.utcnow().date()
        daily_pnl = 0.0
        
        for pnl_entry in self.pnl_history:
            if pnl_entry["date"] == today:
                daily_pnl += pnl_entry["pnl"]
        
        return daily_pnl
    
    def _calculate_realized_pnl(self) -> float:
        """Calculate total realized PnL."""
        return sum(entry["pnl"] for entry in self.pnl_history if entry["type"] == "realized")
    
    def _calculate_var_95(self) -> float:
        """Calculate Value at Risk 95%."""
        if len(self.pnl_history) < 30:
            return 0.0
        
        # Get last 30 days of PnL
        recent_pnl = [entry["pnl"] for entry in self.pnl_history[-30:]]
        
        # Calculate 5th percentile (95% VaR)
        return abs(np.percentile(recent_pnl, 5))
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown."""
        if len(self.pnl_history) < 2:
            return 0.0
        
        # Calculate cumulative PnL
        cumulative_pnl = []
        total = 0.0
        for entry in self.pnl_history:
            total += entry["pnl"]
            cumulative_pnl.append(total)
        
        # Calculate maximum drawdown
        max_dd = 0.0
        peak = cumulative_pnl[0]
        
        for value in cumulative_pnl:
            if value > peak:
                peak = value
            
            drawdown = (peak - value) / abs(peak) if peak != 0 else 0.0
            max_dd = max(max_dd, drawdown)
        
        return max_dd
    
    def _assess_risk_level(self, total_exposure: float, daily_pnl: float, max_drawdown: float, var_95: float) -> RiskLevel:
        """Assess overall risk level."""
        critical_count = 0
        high_count = 0
        medium_count = 0
        
        # Check each metric against thresholds
        if daily_pnl < -self.risk_limits["max_daily_loss"] * 0.8:
            critical_count += 1
        elif daily_pnl < -self.risk_limits["max_daily_loss"] * 0.6:
            high_count += 1
        elif daily_pnl < -self.risk_limits["max_daily_loss"] * 0.4:
            medium_count += 1
        
        if total_exposure > self.risk_limits["max_total_exposure"] * 0.8:
            high_count += 1
        elif total_exposure > self.risk_limits["max_total_exposure"] * 0.6:
            medium_count += 1
        
        if max_drawdown > self.risk_limits["max_drawdown"] * 0.8:
            critical_count += 1
        elif max_drawdown > self.risk_limits["max_drawdown"] * 0.6:
            high_count += 1
        
        if var_95 > self.risk_limits["var_95_limit"] * 0.8:
            high_count += 1
        elif var_95 > self.risk_limits["var_95_limit"] * 0.6:
            medium_count += 1
        
        # Determine overall risk level
        if critical_count > 0 or self.emergency_stop:
            return RiskLevel.CRITICAL
        elif high_count >= 2:
            return RiskLevel.HIGH
        elif high_count >= 1 or medium_count >= 2:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _create_alert(self, alert_type: str, severity: RiskLevel, message: str, details: Dict[str, Any]) -> RiskAlert:
        """Create a new risk alert."""
        self.alert_counter += 1
        return RiskAlert(
            alert_id=f"ALERT_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{self.alert_counter:04d}",
            alert_type=alert_type,
            severity=severity,
            message=message,
            details=details,
            timestamp=datetime.utcnow()
        )
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get risk management summary."""
        risk_metrics = self.calculate_risk_metrics()
        active_alerts = [alert for alert in self.risk_alerts if not alert.resolved]
        
        return {
            "risk_metrics": risk_metrics,
            "active_alerts": active_alerts,
            "emergency_stop": self.emergency_stop,
            "risk_limits": self.risk_limits,
            "position_count": len(self.positions),
            "alert_count": len(active_alerts)
        }