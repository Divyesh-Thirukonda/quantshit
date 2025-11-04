"""
Alerter service - sends notifications when important events occur.
Separate from monitoring so we can change notification method without touching tracking.
"""

from typing import Optional
from enum import Enum
from ...config import settings
from ...utils import get_logger

logger = get_logger(__name__)


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Alerter:
    """
    Send notifications for important events.
    """

    def __init__(self, enabled: bool = None):
        """
        Initialize alerter.

        Args:
            enabled: Enable/disable alerts (defaults to settings.ENABLE_ALERTS)
        """
        self.enabled = enabled if enabled is not None else settings.ENABLE_ALERTS
        self.telegram_token = settings.TELEGRAM_BOT_TOKEN
        self.telegram_chat_id = settings.TELEGRAM_CHAT_ID

        if self.enabled and not (self.telegram_token and self.telegram_chat_id):
            logger.warning("Alerts enabled but Telegram credentials not configured")
            self.enabled = False

        logger.info(f"Alerter initialized (enabled={self.enabled})")

    def send_alert(
        self,
        message: str,
        level: AlertLevel = AlertLevel.INFO,
        details: Optional[dict] = None
    ):
        """
        Send an alert notification.

        Args:
            message: Alert message
            level: Alert severity level
            details: Optional additional details
        """
        if not self.enabled:
            logger.debug(f"Alert disabled: [{level.value}] {message}")
            return

        # Format message
        formatted_message = self._format_message(message, level, details)

        # Log alert
        log_func = {
            AlertLevel.INFO: logger.info,
            AlertLevel.WARNING: logger.warning,
            AlertLevel.ERROR: logger.error,
            AlertLevel.CRITICAL: logger.critical
        }.get(level, logger.info)

        log_func(f"ALERT: {message}")

        # Send via configured channels
        self._send_telegram(formatted_message)

    def alert_opportunity_found(self, profit: float, profit_pct: float, market_title: str):
        """Alert when profitable opportunity found"""
        message = (
            f"💎 Opportunity Found!\n"
            f"Market: {market_title[:50]}...\n"
            f"Profit: ${profit:.2f} ({profit_pct:.2%})"
        )
        self.send_alert(message, AlertLevel.INFO)

    def alert_trade_executed(self, profit: float, market_title: str, success: bool):
        """Alert when trade is executed"""
        if success:
            message = (
                f"✅ Trade Executed!\n"
                f"Market: {market_title[:50]}...\n"
                f"Expected profit: ${profit:.2f}"
            )
            level = AlertLevel.INFO
        else:
            message = (
                f"❌ Trade Failed!\n"
                f"Market: {market_title[:50]}..."
            )
            level = AlertLevel.WARNING

        self.send_alert(message, level)

    def alert_position_pnl(self, position_id: str, pnl: float, pnl_pct: float):
        """Alert when position P&L crosses threshold"""
        emoji = "📈" if pnl > 0 else "📉"
        message = (
            f"{emoji} Position Update\n"
            f"Position: {position_id}\n"
            f"P&L: ${pnl:+.2f} ({pnl_pct:+.2f}%)"
        )

        level = AlertLevel.INFO if pnl > 0 else AlertLevel.WARNING
        self.send_alert(message, level)

    def alert_error(self, error_message: str, context: Optional[str] = None):
        """Alert on errors or failures"""
        message = f"⚠️ Error: {error_message}"
        if context:
            message += f"\nContext: {context}"

        self.send_alert(message, AlertLevel.ERROR)

    def _format_message(
        self,
        message: str,
        level: AlertLevel,
        details: Optional[dict]
    ) -> str:
        """Format alert message with level and details"""
        formatted = f"[{level.value.upper()}] {message}"

        if details:
            formatted += "\n\nDetails:\n"
            for key, value in details.items():
                formatted += f"  {key}: {value}\n"

        return formatted

    def _send_telegram(self, message: str):
        """Send message via Telegram"""
        if not (self.telegram_token and self.telegram_chat_id):
            return

        try:
            # TODO: Implement actual Telegram API call
            # import requests
            # url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            # requests.post(url, json={'chat_id': self.telegram_chat_id, 'text': message})

            logger.debug(f"Would send Telegram: {message}")
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
