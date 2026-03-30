-- Pythia Migration 002: Quantitative Trading Engine + AI Trading Intelligence
-- Phase 7 & 8 tables for smart trading system

-- ============================================================
-- LLM Response Cache (cost optimization)
-- ============================================================
CREATE TABLE IF NOT EXISTS llm_cache (
    cache_key   VARCHAR(64) PRIMARY KEY,
    response    TEXT NOT NULL,
    provider    VARCHAR(20),
    model       VARCHAR(50),
    tokens_used INTEGER DEFAULT 0,
    feature     VARCHAR(50),
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_llm_cache_expires ON llm_cache(expires_at);

-- ============================================================
-- PHASE 7: Quantitative Trading Engine
-- ============================================================

-- 7.1 Market Regimes (HMM-based classification)
CREATE TABLE IF NOT EXISTS market_regimes (
    regime_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol         VARCHAR(20) NOT NULL,
    regime         VARCHAR(20) NOT NULL,
    probability    DOUBLE PRECISION NOT NULL,
    volatility     DOUBLE PRECISION,
    trend_strength DOUBLE PRECISION,
    detected_at    DATE NOT NULL,
    model_params   JSONB,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_regimes_symbol_date ON market_regimes(symbol, detected_at DESC);

-- 7.2 Trading Signals (multi-factor)
CREATE TABLE IF NOT EXISTS trading_signals (
    signal_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id       UUID NOT NULL REFERENCES assets(asset_id),
    signal_type    VARCHAR(30) NOT NULL,
    signal_name    VARCHAR(100) NOT NULL,
    direction      VARCHAR(10) NOT NULL,
    strength       DOUBLE PRECISION NOT NULL,
    confidence     DOUBLE PRECISION,
    metadata       JSONB,
    expires_at     TIMESTAMPTZ,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_signals_asset_date ON trading_signals(asset_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_type ON trading_signals(signal_type);

-- 7.3 Factor Exposures (Fama-French)
CREATE TABLE IF NOT EXISTS factor_exposures (
    exposure_id    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id   UUID NOT NULL REFERENCES portfolios(portfolio_id),
    factor_model   VARCHAR(30) NOT NULL,
    factor_name    VARCHAR(50) NOT NULL,
    beta           DOUBLE PRECISION NOT NULL,
    t_stat         DOUBLE PRECISION,
    p_value        DOUBLE PRECISION,
    r_squared      DOUBLE PRECISION,
    period_days    INTEGER,
    calculated_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_factors_portfolio ON factor_exposures(portfolio_id);

-- 7.6 Strategies
CREATE TABLE IF NOT EXISTS strategies (
    strategy_id    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name           VARCHAR(100) NOT NULL,
    description    TEXT,
    strategy_type  VARCHAR(30) NOT NULL,
    config         JSONB NOT NULL,
    is_active      BOOLEAN DEFAULT true,
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    updated_at     TIMESTAMPTZ DEFAULT NOW()
);

-- 7.7 Backtest Results (advanced)
CREATE TABLE IF NOT EXISTS backtest_results (
    result_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_id    UUID REFERENCES strategies(strategy_id),
    portfolio_id   UUID REFERENCES portfolios(portfolio_id),
    config         JSONB NOT NULL,
    metrics        JSONB NOT NULL,
    equity_curve   JSONB,
    trades         JSONB,
    walk_forward   JSONB,
    run_at         TIMESTAMPTZ DEFAULT NOW()
);

-- 7.8 Rebalance Plans
CREATE TABLE IF NOT EXISTS rebalance_plans (
    plan_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id   UUID NOT NULL REFERENCES portfolios(portfolio_id),
    plan_type      VARCHAR(30) NOT NULL,
    current_weights JSONB NOT NULL,
    target_weights  JSONB NOT NULL,
    trades_needed   JSONB NOT NULL,
    estimated_cost  DOUBLE PRECISION,
    tax_impact      DOUBLE PRECISION,
    status          VARCHAR(20) DEFAULT 'pending',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- PHASE 8: AI Trading Intelligence
-- ============================================================

-- 8.2 Trade Plans
CREATE TABLE IF NOT EXISTS trade_plans (
    plan_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id       UUID NOT NULL REFERENCES assets(asset_id),
    direction      VARCHAR(10) NOT NULL,
    entry_price    DOUBLE PRECISION NOT NULL,
    stop_loss      DOUBLE PRECISION NOT NULL,
    take_profit_1  DOUBLE PRECISION,
    take_profit_2  DOUBLE PRECISION,
    take_profit_3  DOUBLE PRECISION,
    position_size  DOUBLE PRECISION,
    risk_reward    DOUBLE PRECISION,
    rationale      TEXT,
    signals_used   JSONB,
    regime_context VARCHAR(20),
    llm_provider   VARCHAR(20),
    status         VARCHAR(20) DEFAULT 'active',
    expires_at     TIMESTAMPTZ,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

-- 8.5 Chart Patterns
CREATE TABLE IF NOT EXISTS chart_patterns (
    pattern_id     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id       UUID NOT NULL REFERENCES assets(asset_id),
    pattern_type   VARCHAR(50) NOT NULL,
    direction      VARCHAR(10),
    confidence     DOUBLE PRECISION,
    start_date     DATE,
    end_date       DATE,
    breakout_price DOUBLE PRECISION,
    target_price   DOUBLE PRECISION,
    metadata       JSONB,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

-- 8.8 Alerts
CREATE TABLE IF NOT EXISTS alerts (
    alert_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_type     VARCHAR(30) NOT NULL,
    title          VARCHAR(200) NOT NULL,
    message        TEXT,
    severity       VARCHAR(10) DEFAULT 'info',
    asset_id       UUID REFERENCES assets(asset_id),
    portfolio_id   UUID REFERENCES portfolios(portfolio_id),
    condition      JSONB,
    is_read        BOOLEAN DEFAULT false,
    is_active      BOOLEAN DEFAULT true,
    triggered_at   TIMESTAMPTZ,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_alerts_unread ON alerts(is_read, created_at DESC) WHERE is_read = false
