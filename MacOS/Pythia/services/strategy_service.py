"""
Pythia — Strategy Builder Service
Composable trading strategies with entry/exit rules, filters, and position sizing.
"""
import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

import asyncpg
import numpy as np

from config import PythiaConfig


@dataclass
class StrategyConfig:
    name: str
    strategy_type: str  # momentum, mean_reversion, signal_based, custom
    entry_rules: list[dict] = field(default_factory=list)
    exit_rules: list[dict] = field(default_factory=list)
    filters: list[dict] = field(default_factory=list)
    position_sizing: dict = field(default_factory=lambda: {"method": "fixed", "size_pct": 0.10})
    universe: list[str] = field(default_factory=list)


@dataclass
class Trade:
    entry_date: str
    exit_date: str
    direction: str  # long, short
    entry_price: float
    exit_price: float
    pnl_pct: float
    pnl_value: float
    holding_days: int
    exit_reason: str  # take_profit, stop_loss, trailing_stop, signal_exit, end_of_data


@dataclass
class StrategyEvalResult:
    strategy_id: str
    strategy_name: str
    total_return: float = 0.0
    annualized_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    total_trades: int = 0
    avg_holding_days: float = 0.0
    trades: list[Trade] = field(default_factory=list)
    equity_curve: list[dict] = field(default_factory=list)
    success: bool = True
    message: str = ""


# ── CRUD ──────────────────────────────────────────────────

async def create_strategy(conn: asyncpg.Connection, config: dict) -> str:
    """Create a new strategy and return its ID."""
    row = await conn.fetchrow(
        """INSERT INTO strategies (name, description, strategy_type, config)
           VALUES ($1, $2, $3, $4)
           RETURNING strategy_id""",
        config.get("name", "Untitled"),
        config.get("description", ""),
        config.get("strategy_type", "custom"),
        json.dumps(config),
    )
    return str(row["strategy_id"])


async def list_strategies(conn: asyncpg.Connection) -> list[dict]:
    """List all strategies."""
    rows = await conn.fetch(
        "SELECT strategy_id, name, description, strategy_type, is_active, created_at FROM strategies ORDER BY created_at DESC"
    )
    return [
        {
            "strategy_id": str(r["strategy_id"]),
            "name": r["name"],
            "description": r["description"],
            "strategy_type": r["strategy_type"],
            "is_active": r["is_active"],
            "created_at": str(r["created_at"]),
        }
        for r in rows
    ]


async def get_strategy(conn: asyncpg.Connection, strategy_id: UUID) -> Optional[dict]:
    """Get strategy by ID."""
    row = await conn.fetchrow(
        "SELECT * FROM strategies WHERE strategy_id = $1", strategy_id
    )
    if not row:
        return None
    return {
        "strategy_id": str(row["strategy_id"]),
        "name": row["name"],
        "description": row["description"],
        "strategy_type": row["strategy_type"],
        "config": json.loads(row["config"]) if row["config"] else {},
        "is_active": row["is_active"],
        "created_at": str(row["created_at"]),
    }


async def update_strategy(conn: asyncpg.Connection, strategy_id: UUID, config: dict) -> bool:
    """Update strategy config."""
    result = await conn.execute(
        """UPDATE strategies SET name = $2, description = $3, strategy_type = $4,
           config = $5, updated_at = NOW()
           WHERE strategy_id = $1""",
        strategy_id,
        config.get("name", "Untitled"),
        config.get("description", ""),
        config.get("strategy_type", "custom"),
        json.dumps(config),
    )
    return "UPDATE 1" in result


async def delete_strategy(conn: asyncpg.Connection, strategy_id: UUID) -> bool:
    result = await conn.execute("DELETE FROM strategies WHERE strategy_id = $1", strategy_id)
    return "DELETE 1" in result


# ── Evaluation Engine ─────────────────────────────────────

async def evaluate_strategy(
    conn: asyncpg.Connection,
    strategy_id: UUID,
    asset_id: UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    initial_capital: float = 100000,
) -> StrategyEvalResult:
    """Evaluate a strategy on historical data."""
    strategy = await get_strategy(conn, strategy_id)
    if not strategy:
        return StrategyEvalResult(
            strategy_id=str(strategy_id), strategy_name="",
            success=False, message="Strategy not found",
        )

    config = strategy["config"]
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=365)

    # Ensure fresh prices
    from services.price_fetcher_service import PriceFetcherService
    await PriceFetcherService.ensure_fresh(conn, asset_id)

    # Get price data
    rows = await conn.fetch(
        """SELECT date, close_price, volume FROM historical_prices
           WHERE asset_id = $1 AND date BETWEEN $2 AND $3
           ORDER BY date""",
        asset_id, start_date, end_date,
    )

    if len(rows) < 20:
        return StrategyEvalResult(
            strategy_id=str(strategy_id), strategy_name=strategy["name"],
            success=False, message=f"Insufficient data ({len(rows)} points)",
        )

    closes = np.array([float(r["close_price"]) for r in rows])
    volumes = np.array([float(r["volume"] or 0) for r in rows])
    dates = [r["date"] for r in rows]
    returns = np.diff(np.log(closes))

    # Parse strategy rules
    entry_rules = config.get("entry_rules", [])
    exit_rules = config.get("exit_rules", [])
    sizing = config.get("position_sizing", {"method": "fixed", "size_pct": 0.10})
    size_pct = sizing.get("size_pct", 0.10)
    txn_cost_bps = config.get("transaction_cost_bps", PythiaConfig.DEFAULT_TRANSACTION_COST_BPS)

    # Run simulation
    trades = []
    equity = initial_capital
    equity_curve = [{"date": str(dates[0]), "equity": equity}]
    in_trade = False
    entry_price = 0.0
    entry_idx = 0
    direction = "long"
    peak_equity = equity

    for i in range(20, len(closes)):
        price = float(closes[i])

        if not in_trade:
            # Check entry signals
            signal = _check_entry(closes, volumes, returns, i, entry_rules)
            if signal:
                in_trade = True
                entry_price = price
                entry_idx = i
                direction = signal
        else:
            # Check exit signals
            exit_reason = _check_exit(closes, i, entry_price, entry_idx, direction, exit_rules)
            if exit_reason:
                # Close trade
                if direction == "long":
                    pnl_pct = (price - entry_price) / entry_price
                else:
                    pnl_pct = (entry_price - price) / entry_price

                # Subtract transaction costs
                pnl_pct -= 2 * txn_cost_bps / 10000  # entry + exit

                pnl_value = equity * size_pct * pnl_pct
                equity += pnl_value

                trades.append(Trade(
                    entry_date=str(dates[entry_idx]),
                    exit_date=str(dates[i]),
                    direction=direction,
                    entry_price=round(entry_price, 4),
                    exit_price=round(price, 4),
                    pnl_pct=round(pnl_pct, 6),
                    pnl_value=round(pnl_value, 2),
                    holding_days=i - entry_idx,
                    exit_reason=exit_reason,
                ))
                in_trade = False

        equity_curve.append({"date": str(dates[i]), "equity": round(equity, 2)})
        peak_equity = max(peak_equity, equity)

    # Calculate metrics
    total_return = (equity - initial_capital) / initial_capital
    days = (dates[-1] - dates[0]).days
    ann_return = total_return * (365 / max(days, 1))

    # Drawdown
    equities = np.array([e["equity"] for e in equity_curve])
    running_max = np.maximum.accumulate(equities)
    drawdowns = (equities - running_max) / running_max
    max_dd = float(np.min(drawdowns))

    # Win rate / profit factor
    winning = [t for t in trades if t.pnl_pct > 0]
    losing = [t for t in trades if t.pnl_pct <= 0]
    win_rate = len(winning) / max(len(trades), 1)
    gross_profit = sum(t.pnl_value for t in winning)
    gross_loss = abs(sum(t.pnl_value for t in losing))
    profit_factor = gross_profit / max(gross_loss, 1)

    # Sharpe
    if len(trades) > 1:
        trade_returns = [t.pnl_pct for t in trades]
        sharpe = float(np.mean(trade_returns) / (np.std(trade_returns) + 1e-10)) * np.sqrt(252 / max(np.mean([t.holding_days for t in trades]), 1))
    else:
        sharpe = 0.0

    avg_hold = float(np.mean([t.holding_days for t in trades])) if trades else 0

    result = StrategyEvalResult(
        strategy_id=str(strategy_id),
        strategy_name=strategy["name"],
        total_return=round(total_return, 4),
        annualized_return=round(ann_return, 4),
        sharpe_ratio=round(sharpe, 4),
        max_drawdown=round(max_dd, 4),
        win_rate=round(win_rate, 4),
        profit_factor=round(profit_factor, 4),
        total_trades=len(trades),
        avg_holding_days=round(avg_hold, 1),
        trades=trades[-50:],  # last 50 trades
        equity_curve=equity_curve[::max(1, len(equity_curve) // 200)],  # downsample
    )

    # Store result
    try:
        await conn.execute(
            """INSERT INTO backtest_results (strategy_id, config, metrics, equity_curve, trades)
               VALUES ($1, $2, $3, $4, $5)""",
            strategy_id,
            json.dumps({"asset_id": str(asset_id), "start": str(start_date), "end": str(end_date)}),
            json.dumps({"total_return": result.total_return, "sharpe": result.sharpe_ratio,
                        "max_dd": result.max_drawdown, "win_rate": result.win_rate}),
            json.dumps(result.equity_curve[:100]),
            json.dumps([{"entry": t.entry_date, "exit": t.exit_date, "pnl": t.pnl_pct} for t in trades[:20]]),
        )
    except Exception:
        pass

    return result


def _check_entry(
    closes: np.ndarray, volumes: np.ndarray, returns: np.ndarray,
    i: int, rules: list[dict]
) -> Optional[str]:
    """Check entry rules. Returns 'long', 'short', or None."""
    if not rules:
        # Default: SMA crossover
        if i >= 50:
            sma20 = np.mean(closes[i - 20:i])
            sma50 = np.mean(closes[i - 50:i])
            if sma20 > sma50 and np.mean(closes[i - 21:i - 1]) <= np.mean(closes[i - 51:i - 1]):
                return "long"
        return None

    for rule in rules:
        rule_type = rule.get("type", "")

        if rule_type == "sma_cross":
            fast = rule.get("fast_period", 20)
            slow = rule.get("slow_period", 50)
            if i >= slow:
                sma_fast = np.mean(closes[i - fast:i])
                sma_slow = np.mean(closes[i - slow:i])
                prev_fast = np.mean(closes[i - fast - 1:i - 1])
                prev_slow = np.mean(closes[i - slow - 1:i - 1])
                if prev_fast <= prev_slow and sma_fast > sma_slow:
                    return rule.get("direction", "long")

        elif rule_type == "rsi_threshold":
            if i >= 14:
                gains = np.where(returns[i - 14:i] > 0, returns[i - 14:i], 0)
                losses = np.where(returns[i - 14:i] < 0, -returns[i - 14:i], 0)
                rs = np.mean(gains) / (np.mean(losses) + 1e-10)
                rsi = 100 - 100 / (1 + rs)
                threshold = rule.get("threshold", 30)
                if rule.get("condition", "below") == "below" and rsi < threshold:
                    return "long"
                elif rule.get("condition") == "above" and rsi > threshold:
                    return "short"

        elif rule_type == "momentum":
            lookback = rule.get("lookback", 20)
            threshold = rule.get("threshold", 0.05)
            if i >= lookback:
                ret = float(np.sum(returns[i - lookback:i]))
                if ret > threshold:
                    return "long"
                elif ret < -threshold:
                    return "short"

        elif rule_type == "breakout":
            lookback = rule.get("lookback", 20)
            if i >= lookback:
                high = float(np.max(closes[i - lookback:i]))
                if float(closes[i]) > high:
                    return "long"

        elif rule_type == "volume_spike":
            if i >= 20 and np.mean(volumes[i - 20:i]) > 0:
                ratio = float(volumes[i]) / float(np.mean(volumes[i - 20:i]))
                if ratio > rule.get("threshold", 2.0):
                    return "long" if returns[i - 1] > 0 else "short"

    return None


def _check_exit(
    closes: np.ndarray, i: int,
    entry_price: float, entry_idx: int, direction: str,
    rules: list[dict]
) -> Optional[str]:
    """Check exit rules. Returns exit reason or None."""
    price = float(closes[i])

    if not rules:
        # Default exits
        if direction == "long":
            pnl = (price - entry_price) / entry_price
        else:
            pnl = (entry_price - price) / entry_price

        if pnl >= 0.10:
            return "take_profit"
        if pnl <= -0.05:
            return "stop_loss"
        if i - entry_idx >= 20:
            return "time_exit"
        return None

    for rule in rules:
        rule_type = rule.get("type", "")

        if direction == "long":
            pnl = (price - entry_price) / entry_price
        else:
            pnl = (entry_price - price) / entry_price

        if rule_type == "take_profit":
            if pnl >= rule.get("pct", 0.10):
                return "take_profit"

        elif rule_type == "stop_loss":
            if pnl <= -rule.get("pct", 0.05):
                return "stop_loss"

        elif rule_type == "trailing_stop":
            trail_pct = rule.get("pct", 0.08)
            if direction == "long":
                peak = float(np.max(closes[entry_idx:i + 1]))
                if (peak - price) / peak >= trail_pct:
                    return "trailing_stop"
            else:
                trough = float(np.min(closes[entry_idx:i + 1]))
                if (price - trough) / trough >= trail_pct:
                    return "trailing_stop"

        elif rule_type == "time_exit":
            if i - entry_idx >= rule.get("max_days", 20):
                return "time_exit"

    return None


# ── Preset Strategies ─────────────────────────────────────

PRESET_STRATEGIES = {
    "sma_crossover": {
        "name": "SMA Crossover (20/50)",
        "strategy_type": "momentum",
        "description": "Buy when SMA20 crosses above SMA50, sell on trailing stop or take profit",
        "entry_rules": [{"type": "sma_cross", "fast_period": 20, "slow_period": 50, "direction": "long"}],
        "exit_rules": [{"type": "take_profit", "pct": 0.15}, {"type": "trailing_stop", "pct": 0.08}],
        "position_sizing": {"method": "fixed", "size_pct": 0.10},
    },
    "rsi_mean_reversion": {
        "name": "RSI Mean Reversion",
        "strategy_type": "mean_reversion",
        "description": "Buy when RSI < 30 (oversold), sell when RSI > 70 or stop loss",
        "entry_rules": [{"type": "rsi_threshold", "threshold": 30, "condition": "below"}],
        "exit_rules": [{"type": "take_profit", "pct": 0.10}, {"type": "stop_loss", "pct": 0.05}, {"type": "time_exit", "max_days": 15}],
        "position_sizing": {"method": "fixed", "size_pct": 0.10},
    },
    "momentum_breakout": {
        "name": "Momentum Breakout",
        "strategy_type": "momentum",
        "description": "Buy on 20-day high breakout with volume confirmation",
        "entry_rules": [{"type": "breakout", "lookback": 20}],
        "exit_rules": [{"type": "trailing_stop", "pct": 0.10}, {"type": "stop_loss", "pct": 0.05}],
        "position_sizing": {"method": "fixed", "size_pct": 0.08},
    },
}
