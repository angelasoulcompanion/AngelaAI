"""
Pythia — Backtesting Service
SMA crossover strategy + buy-and-hold benchmark.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

import asyncpg
import numpy as np


@dataclass
class BacktestResult:
    strategy_name: str
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float
    final_value: float
    total_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    n_trades: int
    win_rate: float
    # Benchmark comparison
    benchmark_return: float
    excess_return: float
    # Equity curve
    equity_curve: list[dict] = field(default_factory=list)
    trades: list[dict] = field(default_factory=list)
    success: bool = True
    message: str = ""


async def run_sma_backtest(
    conn: asyncpg.Connection,
    asset_id: UUID,
    short_window: int = 20,
    long_window: int = 50,
    initial_capital: float = 1_000_000,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> BacktestResult:
    """Run SMA crossover strategy backtest."""
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=730)

    # Get symbol
    symbol = await conn.fetchval("SELECT symbol FROM assets WHERE asset_id = $1", asset_id)
    if not symbol:
        return BacktestResult("SMA Crossover", "", "", "", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              success=False, message="Asset not found")

    # Fetch prices
    rows = await conn.fetch("""
        SELECT date, close_price FROM historical_prices
        WHERE asset_id = $1 AND date BETWEEN $2 AND $3
        ORDER BY date
    """, asset_id, start_date, end_date)

    if len(rows) < long_window + 10:
        return BacktestResult("SMA Crossover", symbol, "", "", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              success=False, message=f"Need at least {long_window + 10} data points")

    dates = [r["date"] for r in rows]
    prices = np.array([float(r["close_price"]) for r in rows])

    # Calculate SMAs
    sma_short = np.convolve(prices, np.ones(short_window) / short_window, mode='valid')
    sma_long = np.convolve(prices, np.ones(long_window) / long_window, mode='valid')

    # Align arrays
    offset = long_window - short_window
    sma_short = sma_short[offset:]
    aligned_prices = prices[long_window - 1:]
    aligned_dates = dates[long_window - 1:]

    min_len = min(len(sma_short), len(sma_long), len(aligned_prices))
    sma_short = sma_short[:min_len]
    sma_long = sma_long[:min_len]
    aligned_prices = aligned_prices[:min_len]
    aligned_dates = aligned_dates[:min_len]

    # Generate signals & simulate
    cash = initial_capital
    position = 0.0
    trades: list[dict] = []
    equity_curve: list[dict] = []
    in_position = False

    for i in range(1, min_len):
        # Cross up → buy
        if sma_short[i] > sma_long[i] and sma_short[i - 1] <= sma_long[i - 1] and not in_position:
            shares = int(cash / aligned_prices[i])
            if shares > 0:
                cost = shares * aligned_prices[i]
                cash -= cost
                position = shares
                in_position = True
                trades.append({
                    "date": aligned_dates[i].isoformat(),
                    "type": "BUY",
                    "price": round(float(aligned_prices[i]), 2),
                    "shares": shares,
                })

        # Cross down → sell
        elif sma_short[i] < sma_long[i] and sma_short[i - 1] >= sma_long[i - 1] and in_position:
            proceeds = position * aligned_prices[i]
            pnl = proceeds - sum(t["price"] * t["shares"] for t in trades if t["type"] == "BUY")
            cash += proceeds
            trades.append({
                "date": aligned_dates[i].isoformat(),
                "type": "SELL",
                "price": round(float(aligned_prices[i]), 2),
                "shares": int(position),
                "pnl": round(float(pnl), 2) if len(trades) > 0 else 0,
            })
            position = 0
            in_position = False

        portfolio_val = cash + position * aligned_prices[i]
        equity_curve.append({
            "date": aligned_dates[i].isoformat(),
            "value": round(float(portfolio_val), 2),
        })

    final_value = cash + position * aligned_prices[-1]
    total_ret = (final_value - initial_capital) / initial_capital
    n_days = (aligned_dates[-1] - aligned_dates[0]).days
    years = n_days / 365.25 if n_days > 0 else 1
    ann_ret = (1 + total_ret) ** (1 / years) - 1

    # Benchmark: buy-and-hold
    bench_ret = (float(prices[-1]) - float(prices[0])) / float(prices[0])

    # Max drawdown from equity curve
    if equity_curve:
        vals = np.array([e["value"] for e in equity_curve])
        peak = np.maximum.accumulate(vals)
        dd = (vals - peak) / peak
        max_dd = float(np.min(dd))
    else:
        max_dd = 0

    # Win rate
    sell_trades = [t for t in trades if t["type"] == "SELL"]
    wins = sum(1 for t in sell_trades if t.get("pnl", 0) > 0)
    win_rate = wins / len(sell_trades) if sell_trades else 0

    # Sharpe
    if len(equity_curve) > 1:
        rets = np.diff([e["value"] for e in equity_curve]) / np.array([e["value"] for e in equity_curve[:-1]])
        sharpe = float(np.mean(rets) / np.std(rets) * np.sqrt(252)) if np.std(rets) > 0 else 0
    else:
        sharpe = 0

    return BacktestResult(
        strategy_name=f"SMA({short_window}/{long_window})",
        symbol=symbol,
        start_date=aligned_dates[0].isoformat(),
        end_date=aligned_dates[-1].isoformat(),
        initial_capital=initial_capital,
        final_value=round(final_value, 2),
        total_return=round(total_ret, 6),
        annualized_return=round(ann_ret, 6),
        max_drawdown=round(max_dd, 6),
        sharpe_ratio=round(sharpe, 4),
        n_trades=len(trades),
        win_rate=round(win_rate, 4),
        benchmark_return=round(bench_ret, 6),
        excess_return=round(total_ret - bench_ret, 6),
        equity_curve=equity_curve[-252:],  # Last year only to keep response small
        trades=trades,
    )
