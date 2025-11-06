-- Supabase Database Schema for Arbitrage Trading Bot
-- Run this in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Markets table - stores market data from both exchanges
CREATE TABLE markets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    market_id TEXT NOT NULL,
    exchange TEXT NOT NULL, -- 'kalshi' or 'polymarket'
    title TEXT NOT NULL,
    outcome TEXT, -- 'yes' or 'no'
    price DECIMAL(10, 4),
    volume DECIMAL(15, 2),
    liquidity DECIMAL(15, 2),
    open_interest DECIMAL(15, 2),
    status TEXT NOT NULL, -- 'open', 'closed', 'resolved'
    close_date TIMESTAMPTZ,
    metadata JSONB, -- Additional market-specific data
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Composite unique constraint
    UNIQUE(market_id, exchange, outcome)
);

-- Market matches table - stores matched pairs found by the Matcher
CREATE TABLE market_matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    kalshi_market_id UUID REFERENCES markets(id) ON DELETE CASCADE,
    polymarket_market_id UUID REFERENCES markets(id) ON DELETE CASCADE,
    similarity_score DECIMAL(5, 4) NOT NULL, -- 0.0000 to 1.0000
    status TEXT DEFAULT 'active', -- 'active', 'stale', 'closed'
    matched_at TIMESTAMPTZ DEFAULT NOW(),
    last_checked TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure unique pairs
    UNIQUE(kalshi_market_id, polymarket_market_id)
);

-- Opportunities table - detected arbitrage opportunities
CREATE TABLE opportunities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id UUID REFERENCES market_matches(id) ON DELETE CASCADE,
    outcome TEXT NOT NULL, -- 'yes' or 'no'
    
    -- Price information
    buy_price DECIMAL(10, 4) NOT NULL,
    sell_price DECIMAL(10, 4) NOT NULL,
    buy_exchange TEXT NOT NULL,
    sell_exchange TEXT NOT NULL,
    
    -- Profitability metrics
    spread DECIMAL(10, 4) NOT NULL,
    profit_pct DECIMAL(10, 4) NOT NULL,
    estimated_profit DECIMAL(15, 2) NOT NULL,
    
    -- Sizing and risk
    recommended_size DECIMAL(15, 2) NOT NULL,
    max_size DECIMAL(15, 2),
    confidence_score DECIMAL(5, 4),
    
    -- Metadata
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    status TEXT DEFAULT 'new', -- 'new', 'evaluated', 'executed', 'expired', 'rejected'
    metadata JSONB
);

-- Positions table - active and closed positions
CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE SET NULL,
    
    -- Position details
    outcome TEXT NOT NULL,
    size DECIMAL(15, 2) NOT NULL,
    entry_price_buy DECIMAL(10, 4) NOT NULL,
    entry_price_sell DECIMAL(10, 4) NOT NULL,
    buy_exchange TEXT NOT NULL,
    sell_exchange TEXT NOT NULL,
    
    -- Exit information
    exit_price_buy DECIMAL(10, 4),
    exit_price_sell DECIMAL(10, 4),
    realized_pnl DECIMAL(15, 2),
    
    -- Status tracking
    status TEXT DEFAULT 'open', -- 'open', 'closing', 'closed'
    opened_at TIMESTAMPTZ DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    
    -- Metadata
    metadata JSONB
);

-- Orders table - individual orders placed on exchanges
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    position_id UUID REFERENCES positions(id) ON DELETE CASCADE,
    
    -- Order details
    exchange_order_id TEXT, -- ID from the exchange
    exchange TEXT NOT NULL,
    market_id TEXT NOT NULL,
    side TEXT NOT NULL, -- 'buy' or 'sell'
    outcome TEXT NOT NULL,
    
    -- Pricing and sizing
    price DECIMAL(10, 4) NOT NULL,
    quantity DECIMAL(15, 2) NOT NULL,
    filled_quantity DECIMAL(15, 2) DEFAULT 0,
    
    -- Status
    status TEXT DEFAULT 'pending', -- 'pending', 'filled', 'partial', 'cancelled', 'failed'
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    filled_at TIMESTAMPTZ,
    
    -- Metadata
    error_message TEXT,
    metadata JSONB
);

-- Scan logs table - track scanning activity
CREATE TABLE scan_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_type TEXT NOT NULL, -- 'scheduled', 'manual'
    
    -- Metrics
    kalshi_markets_found INTEGER,
    polymarket_markets_found INTEGER,
    matches_found INTEGER,
    opportunities_detected INTEGER,
    
    -- Timing
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    
    -- Status
    status TEXT DEFAULT 'running', -- 'running', 'completed', 'failed'
    error_message TEXT,
    metadata JSONB
);

-- Create indexes for performance
CREATE INDEX idx_markets_exchange ON markets(exchange);
CREATE INDEX idx_markets_status ON markets(status);
CREATE INDEX idx_markets_updated ON markets(updated_at);
CREATE INDEX idx_market_matches_status ON market_matches(status);
CREATE INDEX idx_market_matches_matched_at ON market_matches(matched_at);
CREATE INDEX idx_opportunities_status ON opportunities(status);
CREATE INDEX idx_opportunities_detected_at ON opportunities(detected_at);
CREATE INDEX idx_positions_status ON positions(status);
CREATE INDEX idx_positions_opened_at ON positions(opened_at);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_position_id ON orders(position_id);
CREATE INDEX idx_scan_logs_started_at ON scan_logs(started_at);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add updated_at triggers
CREATE TRIGGER update_markets_updated_at BEFORE UPDATE ON markets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for convenience
CREATE OR REPLACE VIEW active_opportunities AS
SELECT 
    o.id,
    o.outcome,
    o.buy_price,
    o.sell_price,
    o.buy_exchange,
    o.sell_exchange,
    o.spread,
    o.profit_pct,
    o.estimated_profit,
    o.recommended_size,
    o.confidence_score,
    o.detected_at,
    mm.similarity_score,
    mk.title as kalshi_title,
    mp.title as polymarket_title
FROM opportunities o
JOIN market_matches mm ON o.match_id = mm.id
JOIN markets mk ON mm.kalshi_market_id = mk.id
JOIN markets mp ON mm.polymarket_market_id = mp.id
WHERE o.status = 'new'
ORDER BY o.profit_pct DESC;

CREATE OR REPLACE VIEW open_positions AS
SELECT 
    p.id,
    p.outcome,
    p.size,
    p.entry_price_buy,
    p.entry_price_sell,
    p.buy_exchange,
    p.sell_exchange,
    p.opened_at,
    p.status,
    COUNT(o.id) as order_count
FROM positions p
LEFT JOIN orders o ON p.id = o.position_id
WHERE p.status IN ('open', 'closing')
GROUP BY p.id
ORDER BY p.opened_at DESC;

CREATE OR REPLACE VIEW trading_stats AS
SELECT
    COUNT(DISTINCT CASE WHEN status = 'open' THEN id END) as open_positions,
    COUNT(DISTINCT CASE WHEN status = 'closed' THEN id END) as closed_positions,
    SUM(CASE WHEN status = 'closed' AND realized_pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
    SUM(CASE WHEN status = 'closed' AND realized_pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
    COALESCE(SUM(CASE WHEN status = 'closed' THEN realized_pnl END), 0) as total_pnl,
    COALESCE(AVG(CASE WHEN status = 'closed' THEN realized_pnl END), 0) as avg_pnl_per_trade
FROM positions;

-- Grant necessary permissions (adjust based on your Supabase setup)
-- If using authenticated users:
-- ALTER TABLE markets ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Allow read access to all authenticated users" ON markets FOR SELECT USING (auth.role() = 'authenticated');
-- (Repeat for other tables as needed)

-- Insert initial data or configuration if needed
-- ...

COMMENT ON TABLE markets IS 'Stores market data from Kalshi and Polymarket';
COMMENT ON TABLE market_matches IS 'Pairs of matched markets found by the Matcher service';
COMMENT ON TABLE opportunities IS 'Detected arbitrage opportunities ready for execution';
COMMENT ON TABLE positions IS 'Open and closed trading positions';
COMMENT ON TABLE orders IS 'Individual orders placed on exchanges';
COMMENT ON TABLE scan_logs IS 'Logs of market scanning operations';
