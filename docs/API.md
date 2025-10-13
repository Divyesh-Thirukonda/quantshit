# API Documentation

## Overview

The Arbitrage Trading System provides a comprehensive REST API for monitoring and controlling the trading system.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All API endpoints require authentication via API key in the header:

```
Authorization: Bearer YOUR_API_KEY
```

## Endpoints

### System Status

#### GET /status
Get overall system status.

**Response:**
```json
{
  "status": "running",
  "uptime": 3600,
  "data_providers": 1,
  "active_strategies": 2,
  "active_orders": 5,
  "risk_level": "low"
}
```

### Markets

#### GET /markets
Get current market data from all platforms.

**Parameters:**
- `platform` (optional): Filter by platform
- `category` (optional): Filter by category

**Response:**
```json
{
  "markets": [
    {
      "platform": "kalshi",
      "market_id": "KALSHI_ELECTION_001",
      "title": "Will Biden win 2024 election?",
      "yes_price": 0.65,
      "no_price": 0.35,
      "volume": 1000.0,
      "last_updated": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Opportunities

#### GET /opportunities
Get current arbitrage opportunities.

**Parameters:**
- `type` (optional): Filter by opportunity type
- `min_profit` (optional): Minimum profit threshold

**Response:**
```json
{
  "opportunities": [
    {
      "opportunity_id": "cross_kalshi_001_polymarket_001",
      "type": "cross_platform",
      "expected_profit": 0.035,
      "confidence_score": 0.85,
      "markets": [
        {
          "platform": "kalshi",
          "market_id": "KALSHI_ELECTION_001",
          "yes_price": 0.65
        },
        {
          "platform": "polymarket", 
          "market_id": "POLY_ELECTION_001",
          "yes_price": 0.68
        }
      ]
    }
  ]
}
```

### Orders

#### GET /orders
Get order status and history.

**Parameters:**
- `status` (optional): Filter by order status
- `platform` (optional): Filter by platform

**Response:**
```json
{
  "orders": [
    {
      "order_id": "ORD_20240115103000_0001",
      "platform": "kalshi",
      "market_id": "KALSHI_ELECTION_001",
      "side": "buy",
      "outcome": "yes",
      "quantity": 100,
      "price": 0.65,
      "status": "filled",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### POST /orders
Place a new order.

**Request:**
```json
{
  "platform": "kalshi",
  "market_id": "KALSHI_ELECTION_001",
  "side": "buy",
  "outcome": "yes",
  "quantity": 100,
  "order_type": "limit",
  "price": 0.65
}
```

**Response:**
```json
{
  "success": true,
  "order_id": "ORD_20240115103000_0001",
  "message": "Order placed successfully"
}
```

#### DELETE /orders/{order_id}
Cancel an order.

**Response:**
```json
{
  "success": true,
  "message": "Order cancelled successfully"
}
```

### Risk Management

#### GET /risk/metrics
Get current risk metrics.

**Response:**
```json
{
  "total_exposure": 15420.0,
  "daily_pnl": 123.45,
  "var_95": 450.0,
  "max_drawdown": 0.032,
  "risk_level": "low",
  "position_count": 12,
  "platform_exposures": {
    "kalshi": 15420.0
  }
}
```

#### GET /risk/alerts
Get active risk alerts.

**Response:**
```json
{
  "alerts": [
    {
      "alert_id": "ALERT_20240115103000_0001",
      "type": "exposure_warning",
      "severity": "medium",
      "message": "Platform exposure at 62%",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### POST /risk/emergency-stop
Activate emergency stop.

**Request:**
```json
{
  "reason": "Manual intervention required"
}
```

### Strategies

#### GET /strategies
Get strategy status and performance.

**Response:**
```json
{
  "strategies": [
    {
      "name": "cross_platform_arbitrage",
      "status": "active",
      "position_size": 1500.0,
      "performance": {
        "total_return": 0.15,
        "win_rate": 0.735,
        "sharpe_ratio": 1.85
      }
    }
  ]
}
```

#### POST /strategies/{strategy_name}/pause
Pause a strategy.

#### POST /strategies/{strategy_name}/resume
Resume a strategy.

### Backtesting

#### POST /backtest
Run a backtest.

**Request:**
```json
{
  "strategy": "cross_platform_arbitrage",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "initial_capital": 100000.0,
  "config": {
    "min_spread": 0.03
  }
}
```

**Response:**
```json
{
  "backtest_id": "bt_20240115103000",
  "status": "running",
  "message": "Backtest started"
}
```

#### GET /backtest/{backtest_id}
Get backtest results.

**Response:**
```json
{
  "backtest_id": "bt_20240115103000",
  "status": "completed",
  "results": {
    "total_return": 0.154,
    "sharpe_ratio": 1.85,
    "max_drawdown": 0.032,
    "total_trades": 45,
    "win_rate": 0.735
  }
}
```

## Error Responses

All endpoints return standard HTTP status codes. Error responses include:

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Invalid market ID provided",
    "details": {}
  }
}
```

## Rate Limiting

API requests are limited to:
- 100 requests per minute for general endpoints
- 10 requests per minute for order placement
- 5 requests per minute for backtesting

## Webhooks

The system supports webhooks for real-time notifications:

### Order Updates
```json
{
  "event": "order.filled",
  "order_id": "ORD_20240115103000_0001",
  "data": {
    "platform": "kalshi",
    "market_id": "KALSHI_ELECTION_001",
    "filled_quantity": 100,
    "avg_fill_price": 0.65
  }
}
```

### Risk Alerts
```json
{
  "event": "risk.alert",
  "alert_id": "ALERT_20240115103000_0001",
  "data": {
    "type": "exposure_warning",
    "severity": "medium",
    "message": "Platform exposure at 62%"
  }
}
```

### Opportunities
```json
{
  "event": "opportunity.detected",
  "opportunity_id": "cross_kalshi_001_polymarket_001",
  "data": {
    "type": "cross_platform",
    "expected_profit": 0.035,
    "confidence_score": 0.85
  }
}
```