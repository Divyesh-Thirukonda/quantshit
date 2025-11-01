# Supabase Database Schema
# SQL commands to set up the database tables

-- Create markets table
CREATE TABLE IF NOT EXISTS markets (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    market_id VARCHAR(255) NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    category VARCHAR(100),
    yes_price DECIMAL(10, 6),
    no_price DECIMAL(10, 6),
    volume DECIMAL(15, 2),
    open_interest DECIMAL(15, 2),
    close_date TIMESTAMPTZ,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(platform, market_id)
);

-- Create arbitrage opportunities table
CREATE TABLE IF NOT EXISTS arbitrage_opportunities (
    id SERIAL PRIMARY KEY,
    market_a_platform VARCHAR(50) NOT NULL,
    market_a_id VARCHAR(255) NOT NULL,
    market_a_price DECIMAL(10, 6) NOT NULL,
    market_b_platform VARCHAR(50) NOT NULL,
    market_b_id VARCHAR(255) NOT NULL,
    market_b_price DECIMAL(10, 6) NOT NULL,
    profit_percentage DECIMAL(8, 4) NOT NULL,
    profit_amount DECIMAL(15, 2),
    confidence_score DECIMAL(3, 2),
    status VARCHAR(50) DEFAULT 'detected',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

-- Create trading positions table
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    opportunity_id INTEGER REFERENCES arbitrage_opportunities(id),
    platform VARCHAR(50) NOT NULL,
    market_id VARCHAR(255) NOT NULL,
    position_type VARCHAR(10) NOT NULL, -- 'long' or 'short'
    quantity DECIMAL(15, 6) NOT NULL,
    entry_price DECIMAL(10, 6) NOT NULL,
    current_price DECIMAL(10, 6),
    status VARCHAR(50) DEFAULT 'open',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    closed_at TIMESTAMPTZ
);

-- Create system logs table
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    level VARCHAR(20) NOT NULL, -- 'info', 'warning', 'error'
    message TEXT NOT NULL,
    component VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_markets_platform_status ON markets(platform, status);
CREATE INDEX IF NOT EXISTS idx_markets_updated_at ON markets(updated_at);
CREATE INDEX IF NOT EXISTS idx_arbitrage_created_at ON arbitrage_opportunities(created_at);
CREATE INDEX IF NOT EXISTS idx_arbitrage_status ON arbitrage_opportunities(status);
CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);
CREATE INDEX IF NOT EXISTS idx_system_logs_level_created ON system_logs(level, created_at);

-- Create RLS (Row Level Security) policies
ALTER TABLE markets ENABLE ROW LEVEL SECURITY;
ALTER TABLE arbitrage_opportunities ENABLE ROW LEVEL SECURITY;
ALTER TABLE positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_logs ENABLE ROW LEVEL SECURITY;

-- Create policies (adjust based on your auth needs)
CREATE POLICY "Allow all operations for authenticated users" ON markets
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all operations for authenticated users" ON arbitrage_opportunities
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all operations for authenticated users" ON positions
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all operations for authenticated users" ON system_logs
    FOR ALL USING (auth.role() = 'authenticated');

-- Insert some sample data for testing
INSERT INTO markets (platform, market_id, title, description, category, yes_price, no_price, volume) VALUES
('KALSHI', 'PRES-2024', 'Presidential Election 2024', 'Who will win the 2024 US Presidential Election?', 'Politics', 0.52, 0.48, 125000),
('POLYMARKET', 'pres-election-2024', '2024 US Presidential Election', 'Winner of 2024 US Presidential Election', 'Politics', 0.51, 0.49, 89000),
('KALSHI', 'FED-RATE-DEC', 'Fed Rate Decision December', 'Will Fed raise rates in December?', 'Economics', 0.25, 0.75, 45000)
ON CONFLICT (platform, market_id) DO NOTHING;