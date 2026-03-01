-- ============================================================
-- Pythia Database Schema
-- Quantitative Finance + AI Analysis Platform
-- Version: 1.0
-- Created: 2026-03-01
-- Based on: CQFOracle schema + AI extensions
-- ============================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ============================================================
-- ENUM TYPES
-- ============================================================

CREATE TYPE asset_type AS ENUM (
    'thai_stock', 'us_stock', 'crypto', 'etf', 'mutual_fund',
    'bond', 'commodity', 'forex', 'index', 'other'
);

CREATE TYPE transaction_type AS ENUM (
    'buy', 'sell', 'dividend', 'split', 'transfer_in',
    'transfer_out', 'fee', 'interest'
);

CREATE TYPE option_type AS ENUM ('call', 'put');
CREATE TYPE exercise_style AS ENUM ('european', 'american', 'bermudan');
CREATE TYPE settlement_type AS ENUM ('cash', 'physical');
CREATE TYPE position_type AS ENUM ('long', 'short');

-- ============================================================
-- 1. CORE ENTITIES
-- ============================================================

-- 1.1 Assets
CREATE TABLE assets (
    asset_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    asset_type asset_type NOT NULL,
    exchange VARCHAR(50),
    currency VARCHAR(10) DEFAULT 'THB',
    sector VARCHAR(100),
    industry VARCHAR(100),
    country VARCHAR(50) DEFAULT 'Thailand',
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_assets_symbol_exchange ON assets(symbol, exchange);
CREATE INDEX idx_assets_type ON assets(asset_type);
CREATE INDEX idx_assets_sector ON assets(sector);

-- 1.2 Portfolios
CREATE TABLE portfolios (
    portfolio_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    base_currency VARCHAR(10) DEFAULT 'THB',
    benchmark_symbol VARCHAR(20) DEFAULT '^SET',
    risk_free_rate DECIMAL(8,6) DEFAULT 0.02,
    initial_capital DECIMAL(20,2),
    inception_date DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 1.3 Portfolio Holdings
CREATE TABLE portfolio_holdings (
    holding_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    asset_id UUID NOT NULL REFERENCES assets(asset_id) ON DELETE RESTRICT,
    weight DECIMAL(8,6) NOT NULL CHECK (weight >= 0 AND weight <= 1),
    quantity DECIMAL(20,8),
    average_cost DECIMAL(20,8),
    market_value DECIMAL(20,2),
    target_weight DECIMAL(8,6) CHECK (target_weight IS NULL OR (target_weight >= 0 AND target_weight <= 1)),
    min_weight DECIMAL(8,6) DEFAULT 0.00,
    max_weight DECIMAL(8,6) DEFAULT 1.00,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_portfolio_asset UNIQUE (portfolio_id, asset_id)
);

CREATE INDEX idx_holdings_portfolio ON portfolio_holdings(portfolio_id);

-- 1.4 Historical Prices
CREATE TABLE historical_prices (
    price_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES assets(asset_id) ON DELETE CASCADE,
    date DATE NOT NULL,
    open_price DECIMAL(20,8),
    high_price DECIMAL(20,8),
    low_price DECIMAL(20,8),
    close_price DECIMAL(20,8) NOT NULL,
    adj_close DECIMAL(20,8),
    volume BIGINT,
    dividends DECIMAL(20,8) DEFAULT 0,
    stock_splits DECIMAL(10,6) DEFAULT 1,
    source VARCHAR(50) DEFAULT 'yahoo_finance',
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_asset_date UNIQUE (asset_id, date)
);

CREATE INDEX idx_prices_asset_date ON historical_prices(asset_id, date DESC);
CREATE INDEX idx_prices_date ON historical_prices(date DESC);

-- 1.5 Transactions
CREATE TABLE transactions (
    transaction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    asset_id UUID NOT NULL REFERENCES assets(asset_id) ON DELETE RESTRICT,
    transaction_type transaction_type NOT NULL,
    quantity DECIMAL(20,8) NOT NULL,
    price DECIMAL(20,8) NOT NULL,
    fees DECIMAL(20,8) DEFAULT 0,
    taxes DECIMAL(20,8) DEFAULT 0,
    total_amount DECIMAL(20,2) NOT NULL,
    transaction_date DATE NOT NULL,
    settlement_date DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_transactions_portfolio ON transactions(portfolio_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date DESC);

-- ============================================================
-- 2. MODERN PORTFOLIO THEORY
-- ============================================================

CREATE TABLE optimization_results (
    result_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    optimization_type VARCHAR(50) NOT NULL,
    target_return DECIMAL(10,6),
    risk_free_rate DECIMAL(8,6) NOT NULL,
    expected_return DECIMAL(10,6) NOT NULL,
    expected_volatility DECIMAL(10,6) NOT NULL,
    sharpe_ratio DECIMAL(10,6),
    optimal_weights JSONB NOT NULL,
    constraints_used JSONB DEFAULT '{}',
    input_parameters JSONB DEFAULT '{}',
    solver_status VARCHAR(50),
    calculated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_optimization_portfolio ON optimization_results(portfolio_id);

CREATE TABLE efficient_frontier (
    frontier_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    result_id UUID NOT NULL REFERENCES optimization_results(result_id) ON DELETE CASCADE,
    point_type VARCHAR(20) NOT NULL,
    return_value DECIMAL(10,6) NOT NULL,
    risk_value DECIMAL(10,6) NOT NULL,
    sharpe_ratio DECIMAL(10,6),
    weights JSONB NOT NULL,
    point_order INTEGER
);

CREATE INDEX idx_frontier_result ON efficient_frontier(result_id);

CREATE TABLE correlation_matrices (
    matrix_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    asset_ids UUID[] NOT NULL,
    asset_symbols VARCHAR(20)[],
    correlation_matrix DOUBLE PRECISION[][] NOT NULL,
    covariance_matrix DOUBLE PRECISION[][] NOT NULL,
    annualized BOOLEAN DEFAULT true,
    calculated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE portfolio_metrics (
    metric_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    calc_date DATE NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    period_type VARCHAR(20),
    total_return DECIMAL(12,6),
    annualized_return DECIMAL(10,6),
    cumulative_return DECIMAL(12,6),
    benchmark_return DECIMAL(10,6),
    active_return DECIMAL(10,6),
    volatility DECIMAL(10,6),
    downside_deviation DECIMAL(10,6),
    max_drawdown DECIMAL(10,6),
    var_95 DECIMAL(10,6),
    var_99 DECIMAL(10,6),
    cvar_95 DECIMAL(10,6),
    sharpe_ratio DECIMAL(10,6),
    sortino_ratio DECIMAL(10,6),
    treynor_ratio DECIMAL(10,6),
    calmar_ratio DECIMAL(10,6),
    information_ratio DECIMAL(10,6),
    jensens_alpha DECIMAL(10,6),
    beta DECIMAL(10,6),
    correlation_to_benchmark DECIMAL(10,6),
    tracking_error DECIMAL(10,6),
    systematic_risk DECIMAL(10,6),
    idiosyncratic_risk DECIMAL(10,6),
    r_squared DECIMAL(10,6),
    risk_free_rate DECIMAL(8,6),
    num_observations INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_portfolio_calc_date UNIQUE (portfolio_id, calc_date, period_type)
);

-- ============================================================
-- 3. OPTIONS PRICING
-- ============================================================

CREATE TABLE option_contracts (
    option_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    underlying_id UUID NOT NULL REFERENCES assets(asset_id) ON DELETE RESTRICT,
    option_type option_type NOT NULL,
    strike_price DECIMAL(20,8) NOT NULL,
    expiry_date DATE NOT NULL,
    exercise_style exercise_style DEFAULT 'european',
    contract_size INTEGER DEFAULT 100,
    contract_symbol VARCHAR(50),
    exchange VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE option_valuations (
    valuation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    option_id UUID NOT NULL REFERENCES option_contracts(option_id) ON DELETE CASCADE,
    valuation_date DATE NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    spot_price DECIMAL(20,8) NOT NULL,
    risk_free_rate DECIMAL(10,6) NOT NULL,
    volatility DECIMAL(10,6) NOT NULL,
    dividend_yield DECIMAL(10,6) DEFAULT 0,
    time_to_expiry DECIMAL(10,6) NOT NULL,
    option_price DECIMAL(20,8) NOT NULL,
    intrinsic_value DECIMAL(20,8),
    time_value DECIMAL(20,8),
    implied_volatility DECIMAL(10,6),
    model_params JSONB DEFAULT '{}',
    calculated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE option_greeks (
    greek_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    valuation_id UUID NOT NULL REFERENCES option_valuations(valuation_id) ON DELETE CASCADE,
    delta DECIMAL(12,8),
    theta DECIMAL(12,8),
    vega DECIMAL(12,8),
    rho DECIMAL(12,8),
    gamma DECIMAL(12,8),
    vanna DECIMAL(12,8),
    charm DECIMAL(12,8),
    volga DECIMAL(12,8),
    speed DECIMAL(12,8),
    color DECIMAL(12,8),
    calculated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 4. RISK MANAGEMENT
-- ============================================================

CREATE TABLE var_calculations (
    var_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    calc_date DATE NOT NULL,
    method VARCHAR(50) NOT NULL,
    confidence_level DECIMAL(5,4) NOT NULL,
    holding_period INTEGER DEFAULT 1,
    lookback_period INTEGER DEFAULT 252,
    portfolio_value DECIMAL(20,2),
    var_value DECIMAL(20,2) NOT NULL,
    var_percent DECIMAL(10,6),
    cvar_value DECIMAL(20,2),
    cvar_percent DECIMAL(10,6),
    marginal_var JSONB,
    component_var JSONB,
    model_params JSONB DEFAULT '{}',
    calculated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE stress_tests (
    stress_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    test_name VARCHAR(100) NOT NULL,
    test_type VARCHAR(50) NOT NULL,
    description TEXT,
    shock_params JSONB NOT NULL,
    portfolio_value_before DECIMAL(20,2),
    portfolio_value_after DECIMAL(20,2),
    pnl_change DECIMAL(20,2),
    pnl_change_percent DECIMAL(10,6),
    worst_assets JSONB,
    best_assets JSONB,
    calculated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 5. MONTE CARLO
-- ============================================================

CREATE TABLE mc_simulations (
    simulation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID REFERENCES portfolios(portfolio_id) ON DELETE SET NULL,
    asset_id UUID REFERENCES assets(asset_id) ON DELETE SET NULL,
    simulation_type VARCHAR(50) NOT NULL,
    simulation_name VARCHAR(100),
    num_simulations INTEGER NOT NULL DEFAULT 10000,
    time_horizon INTEGER NOT NULL,
    time_steps INTEGER NOT NULL,
    initial_value DECIMAL(20,2),
    mean_final_value DECIMAL(20,2),
    std_final_value DECIMAL(20,2),
    median_final_value DECIMAL(20,2),
    var_95 DECIMAL(20,2),
    var_99 DECIMAL(20,2),
    probability_of_loss DECIMAL(10,6),
    expected_shortfall DECIMAL(20,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE mc_results (
    result_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    simulation_id UUID NOT NULL REFERENCES mc_simulations(simulation_id) ON DELETE CASCADE,
    percentile DECIMAL(5,2) NOT NULL,
    value DECIMAL(20,2) NOT NULL,
    return_value DECIMAL(10,6)
);

CREATE TABLE mc_paths (
    path_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    simulation_id UUID NOT NULL REFERENCES mc_simulations(simulation_id) ON DELETE CASCADE,
    path_number INTEGER NOT NULL,
    path_type VARCHAR(20),
    path_values DECIMAL[] NOT NULL,
    final_value DECIMAL(20,2),
    final_return DECIMAL(10,6)
);

-- ============================================================
-- 6. WATCHLISTS
-- ============================================================

CREATE TABLE watchlists (
    watchlist_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE watchlist_items (
    item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    watchlist_id UUID NOT NULL REFERENCES watchlists(watchlist_id) ON DELETE CASCADE,
    asset_id UUID NOT NULL REFERENCES assets(asset_id) ON DELETE CASCADE,
    added_at TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT,
    CONSTRAINT unique_watchlist_asset UNIQUE (watchlist_id, asset_id)
);

-- ============================================================
-- 7. AI EXTENSIONS
-- ============================================================

-- AI Advisor conversations
CREATE TABLE ai_conversations (
    conversation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID REFERENCES portfolios(portfolio_id) ON DELETE SET NULL,
    title VARCHAR(255),
    model VARCHAR(50) DEFAULT 'claude',
    messages JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- AI Sentiment analysis results
CREATE TABLE ai_sentiment_results (
    sentiment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID REFERENCES assets(asset_id) ON DELETE CASCADE,
    source VARCHAR(50) NOT NULL,
    headline TEXT,
    sentiment_score DECIMAL(5,4),
    confidence DECIMAL(5,4),
    topics JSONB,
    analyzed_at TIMESTAMPTZ DEFAULT NOW()
);

-- AI Forecast results
CREATE TABLE ai_forecasts (
    forecast_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES assets(asset_id) ON DELETE CASCADE,
    model_type VARCHAR(50) NOT NULL,
    forecast_horizon INTEGER NOT NULL,
    predictions JSONB NOT NULL,
    metrics JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Research documents for RAG
CREATE TABLE research_documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    source VARCHAR(100),
    content TEXT NOT NULL,
    embedding vector(1024),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_research_embedding ON research_documents USING ivfflat (embedding vector_cosine_ops);

-- ============================================================
-- 8. SYSTEM TABLES
-- ============================================================

CREATE TABLE app_settings (
    setting_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    value_type VARCHAR(20) DEFAULT 'string',
    description TEXT,
    category VARCHAR(50),
    is_sensitive BOOLEAN DEFAULT false,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO app_settings (setting_key, setting_value, value_type, category, description) VALUES
    ('default_risk_free_rate', '0.0225', 'decimal', 'mpt', 'Default risk-free rate (Thai)'),
    ('default_benchmark', '^SET', 'string', 'mpt', 'Default benchmark symbol'),
    ('yahoo_finance_enabled', 'true', 'boolean', 'data', 'Enable Yahoo Finance'),
    ('var_confidence_level', '0.95', 'decimal', 'risk', 'Default VaR confidence level'),
    ('mc_default_simulations', '10000', 'integer', 'monte_carlo', 'Default MC simulations'),
    ('price_history_days', '365', 'integer', 'data', 'Days of price history');

CREATE TABLE calculation_log (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    module VARCHAR(50) NOT NULL,
    operation VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    input_params JSONB,
    result_summary JSONB,
    execution_time_ms INTEGER,
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_calc_log_module ON calculation_log(module);
CREATE INDEX idx_calc_log_date ON calculation_log(created_at DESC);

-- ============================================================
-- HELPER FUNCTIONS
-- ============================================================

CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_assets_updated
    BEFORE UPDATE ON assets FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trigger_portfolios_updated
    BEFORE UPDATE ON portfolios FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trigger_holdings_updated
    BEFORE UPDATE ON portfolio_holdings FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ============================================================
DO $$
BEGIN
    RAISE NOTICE '================================================';
    RAISE NOTICE 'Pythia Database Schema Created Successfully!';
    RAISE NOTICE 'Tables: Core(5) + MPT(4) + Options(3) + Risk(2) + MC(3) + Watchlist(2) + AI(4) + System(2) = 25';
    RAISE NOTICE '================================================';
END $$;
