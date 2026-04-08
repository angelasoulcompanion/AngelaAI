-- 003: US Stock Universe table for Alpha Ideas scanning
-- Stores S&P 500 + popular US tickers for batch factor analysis

CREATE TABLE IF NOT EXISTS us_stock_universe (
    ticker_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(255),
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap_group VARCHAR(20) DEFAULT 'large',  -- large, mid, small
    index_membership VARCHAR(50),  -- SP500, NASDAQ100, DJIA, RUSSELL2000
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_us_universe_active ON us_stock_universe(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_us_universe_index ON us_stock_universe(index_membership);
