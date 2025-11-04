-- Supabase Database Schema for Quantshit Arbitrage System
-- Run this in your Supabase SQL editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Markets table - stores all markets from different platforms
CREATE TABLE IF NOT EXISTS markets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id TEXT NOT NULL, -- Platform-specific market ID
    platform TEXT NOT NULL CHECK (platform IN ('kalshi', 'polymarket')),
    title TEXT NOT NULL,
    description TEXT,
    question TEXT,
    category TEXT,
    end_date TIMESTAMP,
    status TEXT CHECK (status IN ('active', 'closed', 'resolved', 'suspended')),
    volume DECIMAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Additional platform-specific data stored as JSON
    metadata JSONB DEFAULT '{}',
    
    -- Unique constraint per platform
    UNIQUE(platform, external_id)
);

-- Market matches - stores matched markets between platforms
CREATE TABLE IF NOT EXISTS market_matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    kalshi_market_id UUID REFERENCES markets(id),
    polymarket_market_id UUID REFERENCES markets(id),
    similarity_score DECIMAL NOT NULL,
    match_type TEXT CHECK (match_type IN ('exact', 'high', 'medium', 'low')),
    confidence DECIMAL DEFAULT 0,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'expired')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Ensure unique market pairs
    UNIQUE(kalshi_market_id, polymarket_market_id)
);

-- Market quotes/prices - real-time price data
CREATE TABLE IF NOT EXISTS market_quotes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    market_id UUID REFERENCES markets(id),
    outcome TEXT NOT NULL CHECK (outcome IN ('yes', 'no')),
    bid_price DECIMAL,
    ask_price DECIMAL,
    last_price DECIMAL,
    volume DECIMAL DEFAULT 0,
    timestamp TIMESTAMP DEFAULT NOW(),
    
    -- Index for fast lookups
    INDEX idx_quotes_market_time (market_id, timestamp DESC)
);

-- Arbitrage opportunities - detected opportunities
CREATE TABLE IF NOT EXISTS arbitrage_opportunities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id UUID REFERENCES market_matches(id),
    outcome TEXT NOT NULL CHECK (outcome IN ('yes', 'no')),
    
    -- Buy side (lower price)
    buy_platform TEXT NOT NULL,
    buy_market_id UUID REFERENCES markets(id),
    buy_price DECIMAL NOT NULL,
    
    -- Sell side (higher price)
    sell_platform TEXT NOT NULL,
    sell_market_id UUID REFERENCES markets(id),
    sell_price DECIMAL NOT NULL,
    
    -- Opportunity metrics
    spread DECIMAL NOT NULL, -- Absolute spread
    spread_percentage DECIMAL NOT NULL, -- Percentage spread
    expected_profit DECIMAL,
    max_position_size DECIMAL,
    confidence_score DECIMAL DEFAULT 0,
    risk_level TEXT CHECK (risk_level IN ('low', 'medium', 'high')),
    
    -- Status and timing
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'executed', 'expired', 'invalid')),
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Trading positions - actual positions taken
CREATE TABLE IF NOT EXISTS positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    opportunity_id UUID REFERENCES arbitrage_opportunities(id),
    
    -- Position details
    platform TEXT NOT NULL,
    market_id UUID REFERENCES markets(id),
    outcome TEXT NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('buy', 'sell')),
    
    -- Trade execution
    quantity DECIMAL NOT NULL,
    entry_price DECIMAL NOT NULL,
    entry_time TIMESTAMP DEFAULT NOW(),
    
    -- Current status
    current_price DECIMAL,
    unrealized_pnl DECIMAL DEFAULT 0,
    realized_pnl DECIMAL DEFAULT 0,
    
    -- Position status
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'closed', 'partially_closed')),
    close_price DECIMAL,
    close_time TIMESTAMP,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Portfolio summary - overall performance tracking
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Portfolio metrics
    total_value DECIMAL NOT NULL,
    cash_balance DECIMAL NOT NULL,
    total_positions_value DECIMAL DEFAULT 0,
    unrealized_pnl DECIMAL DEFAULT 0,
    realized_pnl DECIMAL DEFAULT 0,
    total_pnl DECIMAL DEFAULT 0,
    
    -- Performance metrics
    daily_pnl DECIMAL DEFAULT 0,
    win_rate DECIMAL DEFAULT 0,
    total_trades INTEGER DEFAULT 0,
    active_positions INTEGER DEFAULT 0,
    
    -- Risk metrics
    max_drawdown DECIMAL DEFAULT 0,
    sharpe_ratio DECIMAL,
    
    -- Timestamp
    snapshot_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- One snapshot per day
    UNIQUE(snapshot_date)
);

-- Strategy configurations - different trading strategies
CREATE TABLE IF NOT EXISTS strategies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    strategy_type TEXT NOT NULL CHECK (strategy_type IN ('arbitrage', 'insider_info', 'pair_trading', 'mean_reversion')),
    
    -- Strategy parameters stored as JSON
    parameters JSONB NOT NULL DEFAULT '{}',
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Execution logs - track all trading actions
CREATE TABLE IF NOT EXISTS execution_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- What was executed
    action_type TEXT NOT NULL CHECK (action_type IN ('scan_markets', 'find_opportunities', 'execute_trade', 'close_position', 'rebalance')),
    
    -- Related entities
    opportunity_id UUID REFERENCES arbitrage_opportunities(id),
    position_id UUID REFERENCES positions(id),
    
    -- Execution details
    parameters JSONB DEFAULT '{}',
    result JSONB DEFAULT '{}',
    
    -- Status
    status TEXT NOT NULL CHECK (status IN ('started', 'completed', 'failed')),
    error_message TEXT,
    
    -- Timing
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    duration_ms INTEGER
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_markets_platform ON markets(platform);
CREATE INDEX IF NOT EXISTS idx_markets_status ON markets(status);
CREATE INDEX IF NOT EXISTS idx_markets_updated ON markets(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_quotes_market_outcome ON market_quotes(market_id, outcome);
CREATE INDEX IF NOT EXISTS idx_quotes_timestamp ON market_quotes(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_opportunities_status ON arbitrage_opportunities(status);
CREATE INDEX IF NOT EXISTS idx_opportunities_created ON arbitrage_opportunities(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_opportunities_spread ON arbitrage_opportunities(spread_percentage DESC);

CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);
CREATE INDEX IF NOT EXISTS idx_positions_created ON positions(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_execution_logs_action ON execution_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_execution_logs_started ON execution_logs(started_at DESC);

-- Insert default arbitrage strategy
INSERT INTO strategies (name, strategy_type, parameters) VALUES 
('default_arbitrage', 'arbitrage', '{
    "min_spread": 0.02,
    "max_position_size": 1000,
    "risk_threshold": 0.1,
    "min_volume": 100
}') ON CONFLICT (name) DO NOTHING;

-- Enable Row Level Security (optional - for multi-user)
-- ALTER TABLE markets ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE arbitrage_opportunities ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE positions ENABLE ROW LEVEL SECURITY;