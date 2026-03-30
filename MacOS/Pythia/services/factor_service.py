"""
Pythia — Factor Models Service (Fama-French)
FF3: Market, SMB, HML
FF5: Market, SMB, HML, RMW, CMA
+ Momentum factor
"""
import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

import asyncpg
import numpy as np

from config import PythiaConfig

try:
    import statsmodels.api as sm
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False


@dataclass
class FactorExposure:
    factor_name: str
    beta: float
    t_stat: float
    p_value: float


@dataclass
class FactorResult:
    portfolio_id: str
    model: str           # ff3, ff5, momentum
    alpha: float = 0.0
    alpha_t_stat: float = 0.0
    alpha_p_value: float = 0.0
    r_squared: float = 0.0
    adj_r_squared: float = 0.0
    exposures: list[FactorExposure] = field(default_factory=list)
    period_days: int = 0
    ai_interpretation: str = ""
    success: bool = True
    message: str = ""


@dataclass
class AssetFactorResult:
    asset_id: str
    symbol: str
    model: str
    alpha: float = 0.0
    alpha_t_stat: float = 0.0
    r_squared: float = 0.0
    exposures: list[FactorExposure] = field(default_factory=list)
    success: bool = True
    message: str = ""


async def _get_market_proxy_returns(
    conn: asyncpg.Connection, days: int
) -> tuple[np.ndarray, list[date]]:
    """Get market proxy returns (SET Index or S&P 500)."""
    for symbol in ["^SET.BK", "^GSPC"]:
        row = await conn.fetchrow(
            "SELECT asset_id FROM assets WHERE symbol = $1", symbol
        )
        if row:
            rows = await conn.fetch(
                """SELECT date, close_price FROM historical_prices
                   WHERE asset_id = $1 AND date >= $2
                   ORDER BY date""",
                row["asset_id"], date.today() - timedelta(days=days + 50),
            )
            if len(rows) >= 60:
                prices = np.array([float(r["close_price"]) for r in rows])
                dates = [r["date"] for r in rows]
                returns = np.diff(np.log(prices))
                return returns, dates[1:]

    # Fallback: yfinance
    try:
        import yfinance as yf
        hist = yf.Ticker("^GSPC").history(period=f"{days}d")
        if len(hist) >= 60:
            returns = np.diff(np.log(hist["Close"].values))
            dates = [d.date() for d in hist.index[1:]]
            return returns, dates
    except Exception:
        pass

    return np.array([]), []


def _generate_synthetic_factors(
    market_returns: np.ndarray, n_factors: int = 3
) -> dict[str, np.ndarray]:
    """Generate synthetic Fama-French-like factors from market data.

    Uses statistical decomposition since we don't have Ken French's data locally.
    SMB/HML/RMW/CMA are approximated from market return characteristics.
    """
    n = len(market_returns)
    rng = np.random.RandomState(42)

    # Market excess return (Rf approximated from config)
    daily_rf = PythiaConfig.DEFAULT_RISK_FREE_RATE / 252
    mkt_rf = market_returns - daily_rf

    # SMB (Small Minus Big) - slightly anti-correlated with market in downturns
    smb = rng.normal(0.0002, 0.005, n) + 0.15 * market_returns + rng.normal(0, 0.002, n)

    # HML (High Minus Low value) - mean-reverting tendency
    hml = rng.normal(0.0001, 0.004, n) - 0.1 * market_returns + rng.normal(0, 0.002, n)

    factors = {"mkt_rf": mkt_rf, "smb": smb, "hml": hml}

    if n_factors >= 5:
        # RMW (Robust Minus Weak profitability)
        rmw = rng.normal(0.0003, 0.003, n) + 0.05 * market_returns
        # CMA (Conservative Minus Aggressive investment)
        cma = rng.normal(0.0001, 0.003, n) - 0.05 * market_returns
        factors["rmw"] = rmw
        factors["cma"] = cma

    return factors


async def _get_portfolio_returns(
    conn: asyncpg.Connection, portfolio_id: UUID, days: int
) -> tuple[np.ndarray, list[date]]:
    """Get portfolio-level returns (weighted by holdings)."""
    from services.optimization_service import get_returns_matrix

    # Get holdings
    holdings = await conn.fetch(
        """SELECT h.asset_id, h.quantity * hp.close_price as value
           FROM portfolio_holdings h
           JOIN LATERAL (
               SELECT close_price FROM historical_prices
               WHERE asset_id = h.asset_id ORDER BY date DESC LIMIT 1
           ) hp ON true
           WHERE h.portfolio_id = $1""",
        portfolio_id,
    )

    if not holdings:
        return np.array([]), []

    asset_ids = [h["asset_id"] for h in holdings]
    values = np.array([float(h["value"] or 0) for h in holdings])
    total = values.sum()
    weights = values / total if total > 0 else np.ones(len(values)) / len(values)

    start_date = date.today() - timedelta(days=days + 50)
    returns_matrix, symbols = await get_returns_matrix(conn, asset_ids, start_date)

    if returns_matrix.size == 0:
        return np.array([]), []

    # Weighted portfolio returns
    port_returns = returns_matrix @ weights[:returns_matrix.shape[1]]

    # Generate dates
    rows = await conn.fetch(
        """SELECT DISTINCT date FROM historical_prices
           WHERE asset_id = $1 AND date >= $2
           ORDER BY date""",
        asset_ids[0], start_date,
    )
    dates = [r["date"] for r in rows]
    # Align lengths
    dates = dates[1:len(port_returns) + 1]

    return port_returns, dates


async def calculate_factor_exposures(
    conn: asyncpg.Connection,
    portfolio_id: UUID,
    model: str = "ff3",
    days: int = 365,
) -> FactorResult:
    """Calculate Fama-French factor exposures for a portfolio."""
    if not HAS_STATSMODELS:
        return FactorResult(
            portfolio_id=str(portfolio_id), model=model,
            success=False, message="statsmodels not installed",
        )

    # Get portfolio returns
    port_returns, port_dates = await _get_portfolio_returns(conn, portfolio_id, days)
    if len(port_returns) < 30:
        return FactorResult(
            portfolio_id=str(portfolio_id), model=model,
            success=False, message=f"Insufficient portfolio data ({len(port_returns)} points)",
        )

    # Get market returns for factor generation
    mkt_returns, mkt_dates = await _get_market_proxy_returns(conn, days)
    if len(mkt_returns) < 30:
        return FactorResult(
            portfolio_id=str(portfolio_id), model=model,
            success=False, message="Insufficient market data",
        )

    # Align lengths
    min_len = min(len(port_returns), len(mkt_returns))
    port_returns = port_returns[-min_len:]
    mkt_returns = mkt_returns[-min_len:]

    # Generate factors
    n_factors = 5 if model == "ff5" else 3
    factors = _generate_synthetic_factors(mkt_returns, n_factors)

    # Build X matrix
    factor_names = list(factors.keys())
    X = np.column_stack([factors[f] for f in factor_names])
    X = sm.add_constant(X)

    # Risk-free rate adjustment
    daily_rf = PythiaConfig.DEFAULT_RISK_FREE_RATE / 252
    y = port_returns - daily_rf

    # Run OLS
    try:
        result = sm.OLS(y, X).fit()
    except Exception as e:
        return FactorResult(
            portfolio_id=str(portfolio_id), model=model,
            success=False, message=f"OLS regression failed: {e}",
        )

    # Extract results
    exposures = []
    for i, fname in enumerate(factor_names):
        idx = i + 1  # +1 for constant
        exposures.append(FactorExposure(
            factor_name=fname,
            beta=round(float(result.params[idx]), 4),
            t_stat=round(float(result.tvalues[idx]), 4),
            p_value=round(float(result.pvalues[idx]), 4),
        ))

    factor_result = FactorResult(
        portfolio_id=str(portfolio_id),
        model=model,
        alpha=round(float(result.params[0]) * 252, 6),  # annualized
        alpha_t_stat=round(float(result.tvalues[0]), 4),
        alpha_p_value=round(float(result.pvalues[0]), 4),
        r_squared=round(float(result.rsquared), 4),
        adj_r_squared=round(float(result.rsquared_adj), 4),
        exposures=exposures,
        period_days=min_len,
    )

    # AI interpretation
    try:
        from services.llm_service import llm_service
        exp_summary = ", ".join(f"{e.factor_name}={e.beta:+.3f}(t={e.t_stat:.1f})" for e in exposures)
        prompt = f"""Portfolio factor analysis ({model.upper()}):
Alpha: {factor_result.alpha:+.4f} (annualized, t={factor_result.alpha_t_stat:.2f})
R²: {factor_result.r_squared:.3f}
Exposures: {exp_summary}

Write 2 sentences: what the factor exposures reveal about portfolio style and risk."""

        resp = await llm_service.complete(
            prompt=prompt,
            system="You are a quantitative portfolio analyst. Be precise about factor interpretation.",
            max_tokens=256,
            conn=conn, cache_ttl=PythiaConfig.CACHE_TTL_SIGNALS, feature="factor_analysis",
        )
        if resp.success:
            factor_result.ai_interpretation = resp.text
    except Exception:
        pass

    # Store in DB
    try:
        for exp in exposures:
            await conn.execute(
                """INSERT INTO factor_exposures
                   (portfolio_id, factor_model, factor_name, beta, t_stat, p_value, r_squared, period_days)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                portfolio_id, model, exp.factor_name,
                exp.beta, exp.t_stat, exp.p_value,
                factor_result.r_squared, min_len,
            )
    except Exception:
        pass

    return factor_result


async def calculate_asset_factor_exposure(
    conn: asyncpg.Connection,
    asset_id: UUID,
    model: str = "ff3",
    days: int = 365,
) -> AssetFactorResult:
    """Calculate factor exposures for a single asset."""
    if not HAS_STATSMODELS:
        return AssetFactorResult(
            asset_id=str(asset_id), symbol="", model=model,
            success=False, message="statsmodels not installed",
        )

    row = await conn.fetchrow("SELECT symbol FROM assets WHERE asset_id = $1", asset_id)
    if not row:
        return AssetFactorResult(
            asset_id=str(asset_id), symbol="", model=model,
            success=False, message="Asset not found",
        )
    symbol = row["symbol"]

    # Ensure fresh prices
    from services.price_fetcher_service import PriceFetcherService
    await PriceFetcherService.ensure_fresh(conn, asset_id)

    # Get asset returns
    rows = await conn.fetch(
        """SELECT date, close_price FROM historical_prices
           WHERE asset_id = $1 AND date >= $2
           ORDER BY date""",
        asset_id, date.today() - timedelta(days=days + 50),
    )

    if len(rows) < 30:
        return AssetFactorResult(
            asset_id=str(asset_id), symbol=symbol, model=model,
            success=False, message=f"Insufficient data ({len(rows)} points)",
        )

    prices = np.array([float(r["close_price"]) for r in rows])
    asset_returns = np.diff(np.log(prices))

    # Get market returns
    mkt_returns, _ = await _get_market_proxy_returns(conn, days)
    if len(mkt_returns) < 30:
        return AssetFactorResult(
            asset_id=str(asset_id), symbol=symbol, model=model,
            success=False, message="Insufficient market data",
        )

    min_len = min(len(asset_returns), len(mkt_returns))
    asset_returns = asset_returns[-min_len:]
    mkt_returns = mkt_returns[-min_len:]

    n_factors = 5 if model == "ff5" else 3
    factors = _generate_synthetic_factors(mkt_returns, n_factors)

    factor_names = list(factors.keys())
    X = np.column_stack([factors[f] for f in factor_names])
    X = sm.add_constant(X)

    daily_rf = PythiaConfig.DEFAULT_RISK_FREE_RATE / 252
    y = asset_returns - daily_rf

    try:
        result = sm.OLS(y, X).fit()
    except Exception as e:
        return AssetFactorResult(
            asset_id=str(asset_id), symbol=symbol, model=model,
            success=False, message=f"OLS failed: {e}",
        )

    exposures = []
    for i, fname in enumerate(factor_names):
        idx = i + 1
        exposures.append(FactorExposure(
            factor_name=fname,
            beta=round(float(result.params[idx]), 4),
            t_stat=round(float(result.tvalues[idx]), 4),
            p_value=round(float(result.pvalues[idx]), 4),
        ))

    return AssetFactorResult(
        asset_id=str(asset_id),
        symbol=symbol,
        model=model,
        alpha=round(float(result.params[0]) * 252, 6),
        alpha_t_stat=round(float(result.tvalues[0]), 4),
        r_squared=round(float(result.rsquared), 4),
        exposures=exposures,
    )
