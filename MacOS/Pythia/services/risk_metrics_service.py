"""
Pythia — Risk Metrics Service (ported from CQFOracle)
Comprehensive risk/performance metrics: Sharpe, Sortino, Treynor, Calmar,
Max Drawdown, Beta, Alpha, Information Ratio, Tracking Error, etc.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

import asyncpg
import numpy as np
from scipy.stats import norm, skew, kurtosis

from config import PythiaConfig
from services.optimization_service import get_returns_matrix

TRADING_DAYS = PythiaConfig.TRADING_DAYS_PER_YEAR


@dataclass
class RiskMetrics:
    # Returns
    total_return: float = 0.0
    annualized_return: float = 0.0
    # Volatility
    volatility: float = 0.0
    downside_deviation: float = 0.0
    # Ratios
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    treynor_ratio: float = 0.0
    information_ratio: float = 0.0
    # Drawdown
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    # Distribution
    skewness: float = 0.0
    excess_kurtosis: float = 0.0
    # VaR
    var_95: float = 0.0
    var_99: float = 0.0
    cvar_95: float = 0.0
    # Market
    beta: float = 0.0
    alpha: float = 0.0
    r_squared: float = 0.0
    tracking_error: float = 0.0
    # Meta
    n_observations: int = 0
    period_days: int = 0
    success: bool = True
    message: str = ""


@dataclass
class DrawdownPeriod:
    start_date: str
    end_date: str
    trough_date: str
    drawdown: float
    duration_days: int
    recovery_days: int


async def calculate_portfolio_metrics(
    conn: asyncpg.Connection,
    portfolio_id: UUID,
    days: int = 365,
    risk_free_rate: Optional[float] = None,
) -> RiskMetrics:
    """Calculate comprehensive risk/performance metrics for a portfolio."""
    if risk_free_rate is None:
        row = await conn.fetchrow(
            "SELECT risk_free_rate FROM portfolios WHERE portfolio_id = $1", portfolio_id
        )
        risk_free_rate = float(row["risk_free_rate"]) if row else PythiaConfig.DEFAULT_RISK_FREE_RATE

    rows = await conn.fetch("""
        SELECT h.asset_id, h.weight
        FROM portfolio_holdings h
        WHERE h.portfolio_id = $1
    """, portfolio_id)
    if not rows:
        return RiskMetrics(success=False, message="No holdings")

    asset_ids = [r["asset_id"] for r in rows]
    weights = np.array([float(r["weight"]) for r in rows])
    w_sum = weights.sum()
    if w_sum > 0:
        weights = weights / w_sum

    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    returns_matrix, dates = await get_returns_matrix(conn, asset_ids, start_date, end_date)

    if returns_matrix.size == 0 or len(dates) < 2:
        return RiskMetrics(success=False, message="Insufficient data")

    port_returns = returns_matrix @ weights
    return _compute_metrics(port_returns, risk_free_rate, days, len(dates))


async def calculate_portfolio_metrics_with_benchmark(
    conn: asyncpg.Connection,
    portfolio_id: UUID,
    benchmark_asset_id: UUID,
    days: int = 365,
    risk_free_rate: Optional[float] = None,
) -> RiskMetrics:
    """Calculate metrics including beta, alpha, tracking error vs benchmark."""
    if risk_free_rate is None:
        risk_free_rate = PythiaConfig.DEFAULT_RISK_FREE_RATE

    rows = await conn.fetch("""
        SELECT h.asset_id, h.weight
        FROM portfolio_holdings h
        WHERE h.portfolio_id = $1
    """, portfolio_id)
    if not rows:
        return RiskMetrics(success=False, message="No holdings")

    asset_ids = [r["asset_id"] for r in rows]
    weights = np.array([float(r["weight"]) for r in rows])
    w_sum = weights.sum()
    if w_sum > 0:
        weights = weights / w_sum

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Get portfolio and benchmark returns aligned
    all_ids = asset_ids + [benchmark_asset_id]
    returns_matrix, dates = await get_returns_matrix(conn, all_ids, start_date, end_date)

    if returns_matrix.size == 0 or len(dates) < 2:
        return RiskMetrics(success=False, message="Insufficient data")

    n_assets = len(asset_ids)
    port_returns = returns_matrix[:, :n_assets] @ weights
    bench_returns = returns_matrix[:, n_assets]

    metrics = _compute_metrics(port_returns, risk_free_rate, days, len(dates))

    # Beta & Alpha
    cov_pb = np.cov(port_returns, bench_returns)
    bench_var = cov_pb[1, 1]
    if bench_var > 0:
        metrics.beta = round(float(cov_pb[0, 1] / bench_var), 4)
    bench_ann_ret = float(np.mean(bench_returns)) * TRADING_DAYS
    metrics.alpha = round(metrics.annualized_return - (risk_free_rate + metrics.beta * (bench_ann_ret - risk_free_rate)), 6)

    # R-squared
    corr = np.corrcoef(port_returns, bench_returns)[0, 1]
    metrics.r_squared = round(float(corr ** 2), 4)

    # Tracking error & Information ratio
    active_returns = port_returns - bench_returns
    te = float(np.std(active_returns)) * np.sqrt(TRADING_DAYS)
    metrics.tracking_error = round(te, 6)
    if te > 0:
        metrics.information_ratio = round(float(np.mean(active_returns) * TRADING_DAYS / te), 4)

    # Treynor
    if metrics.beta != 0:
        metrics.treynor_ratio = round((metrics.annualized_return - risk_free_rate) / metrics.beta, 4)

    return metrics


async def get_drawdown_analysis(
    conn: asyncpg.Connection,
    portfolio_id: UUID,
    days: int = 365,
    top_n: int = 5,
) -> dict:
    """Analyze top drawdown periods."""
    rows = await conn.fetch("""
        SELECT h.asset_id, h.weight
        FROM portfolio_holdings h
        WHERE h.portfolio_id = $1
    """, portfolio_id)
    if not rows:
        return {"error": "No holdings"}

    asset_ids = [r["asset_id"] for r in rows]
    weights = np.array([float(r["weight"]) for r in rows])
    w_sum = weights.sum()
    if w_sum > 0:
        weights = weights / w_sum

    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    returns_matrix, dates = await get_returns_matrix(conn, asset_ids, start_date, end_date)

    if returns_matrix.size == 0:
        return {"error": "Insufficient data"}

    port_returns = returns_matrix @ weights
    cumulative = np.cumprod(1 + port_returns)
    running_max = np.maximum.accumulate(cumulative)
    drawdowns = (cumulative - running_max) / running_max

    # Find drawdown periods
    in_dd = False
    dd_start = 0
    periods: list[dict] = []

    for i in range(len(drawdowns)):
        if drawdowns[i] < 0 and not in_dd:
            in_dd = True
            dd_start = i
        elif drawdowns[i] >= 0 and in_dd:
            in_dd = False
            trough_idx = dd_start + np.argmin(drawdowns[dd_start:i])
            periods.append({
                "start_date": dates[dd_start],
                "end_date": dates[i - 1],
                "trough_date": dates[int(trough_idx)],
                "drawdown": round(float(drawdowns[int(trough_idx)]), 6),
                "duration_days": i - dd_start,
            })

    if in_dd:
        trough_idx = dd_start + np.argmin(drawdowns[dd_start:])
        periods.append({
            "start_date": dates[dd_start],
            "end_date": dates[-1],
            "trough_date": dates[int(trough_idx)],
            "drawdown": round(float(drawdowns[int(trough_idx)]), 6),
            "duration_days": len(drawdowns) - dd_start,
        })

    periods.sort(key=lambda x: x["drawdown"])

    return {
        "max_drawdown": round(float(np.min(drawdowns)), 6),
        "current_drawdown": round(float(drawdowns[-1]), 6) if len(drawdowns) > 0 else 0,
        "top_drawdowns": periods[:top_n],
        "drawdown_series": [round(float(d), 6) for d in drawdowns],
        "dates": dates,
    }


async def calculate_rolling_metrics(
    conn: asyncpg.Connection,
    portfolio_id: UUID,
    window: int = 60,
    days: int = 365,
) -> dict:
    """Calculate rolling volatility & Sharpe ratio."""
    rows = await conn.fetch("""
        SELECT h.asset_id, h.weight
        FROM portfolio_holdings h
        WHERE h.portfolio_id = $1
    """, portfolio_id)
    if not rows:
        return {"error": "No holdings"}

    asset_ids = [r["asset_id"] for r in rows]
    weights = np.array([float(r["weight"]) for r in rows])
    w_sum = weights.sum()
    if w_sum > 0:
        weights = weights / w_sum

    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    returns_matrix, dates = await get_returns_matrix(conn, asset_ids, start_date, end_date)

    if returns_matrix.size == 0 or len(dates) < window:
        return {"error": "Insufficient data for rolling window"}

    port_returns = returns_matrix @ weights
    rf_daily = PythiaConfig.DEFAULT_RISK_FREE_RATE / TRADING_DAYS

    rolling_vol = []
    rolling_sharpe = []
    rolling_dates = []

    for i in range(window, len(port_returns) + 1):
        chunk = port_returns[i - window:i]
        vol = float(np.std(chunk)) * np.sqrt(TRADING_DAYS)
        mean_ret = float(np.mean(chunk)) * TRADING_DAYS
        sharpe = (mean_ret - PythiaConfig.DEFAULT_RISK_FREE_RATE) / vol if vol > 0 else 0

        rolling_vol.append(round(vol, 6))
        rolling_sharpe.append(round(sharpe, 4))
        rolling_dates.append(dates[i - 1])

    return {
        "window": window,
        "dates": rolling_dates,
        "rolling_volatility": rolling_vol,
        "rolling_sharpe": rolling_sharpe,
    }


def _compute_metrics(
    returns: np.ndarray,
    risk_free_rate: float,
    period_days: int,
    n_obs: int,
) -> RiskMetrics:
    """Compute all metrics from a returns array."""
    m = RiskMetrics()
    m.n_observations = n_obs
    m.period_days = period_days

    # Total & annualized return
    cumulative = np.prod(1 + returns) - 1
    m.total_return = round(float(cumulative), 6)
    years = n_obs / TRADING_DAYS
    m.annualized_return = round(float((1 + cumulative) ** (1 / years) - 1) if years > 0 else 0, 6)

    # Volatility
    daily_vol = float(np.std(returns))
    m.volatility = round(daily_vol * np.sqrt(TRADING_DAYS), 6)

    # Downside deviation (MAR = risk-free)
    rf_daily = risk_free_rate / TRADING_DAYS
    downside = returns[returns < rf_daily] - rf_daily
    m.downside_deviation = round(float(np.std(downside) * np.sqrt(TRADING_DAYS)) if len(downside) > 0 else 0, 6)

    # Sharpe
    m.sharpe_ratio = round(
        (m.annualized_return - risk_free_rate) / m.volatility if m.volatility > 0 else 0, 4
    )

    # Sortino
    m.sortino_ratio = round(
        (m.annualized_return - risk_free_rate) / m.downside_deviation if m.downside_deviation > 0 else 0, 4
    )

    # Max Drawdown
    cumulative_wealth = np.cumprod(1 + returns)
    running_max = np.maximum.accumulate(cumulative_wealth)
    drawdowns = (cumulative_wealth - running_max) / running_max
    m.max_drawdown = round(float(np.min(drawdowns)), 6)

    # Max drawdown duration
    in_dd = False
    dd_start = 0
    max_dur = 0
    for i in range(len(drawdowns)):
        if drawdowns[i] < 0 and not in_dd:
            in_dd = True
            dd_start = i
        elif drawdowns[i] >= 0 and in_dd:
            in_dd = False
            max_dur = max(max_dur, i - dd_start)
    if in_dd:
        max_dur = max(max_dur, len(drawdowns) - dd_start)
    m.max_drawdown_duration = max_dur

    # Calmar
    m.calmar_ratio = round(
        m.annualized_return / abs(m.max_drawdown) if m.max_drawdown != 0 else 0, 4
    )

    # Distribution
    m.skewness = round(float(skew(returns)), 4)
    m.excess_kurtosis = round(float(kurtosis(returns)), 4)

    # VaR
    sorted_rets = np.sort(returns)
    idx_95 = int(0.05 * len(sorted_rets))
    idx_99 = int(0.01 * len(sorted_rets))
    m.var_95 = round(float(sorted_rets[max(idx_95, 0)]), 6)
    m.var_99 = round(float(sorted_rets[max(idx_99, 0)]), 6)
    m.cvar_95 = round(float(np.mean(sorted_rets[:max(idx_95, 1)])), 6)

    return m
