"""
Pythia Router — Options Pricing (Black-Scholes) + Multi-leg Strategy Builder
"""
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from db import get_conn
from services.black_scholes_service import (
    price_option,
    implied_volatility,
    generate_greeks_surface,
    analyze_option,
)

router = APIRouter(prefix="/api/options", tags=["Options"])


# ── Strategy Models ───────────────────────────────────────────

class StrategyLeg(BaseModel):
    option_type: str  # "call" or "put"
    strike: float
    position: str     # "long" or "short"
    quantity: int = 1

class StrategyRequest(BaseModel):
    spot: float
    legs: List[StrategyLeg]
    time_to_expiry: float = 0.25
    risk_free_rate: float = 0.0225
    volatility: float = 0.20

PRESET_STRATEGIES = {
    "bull_call_spread":  {"name": "Bull Call Spread",  "description": "Buy lower Call + Sell higher Call", "outlook": "Moderately Bullish"},
    "bear_put_spread":   {"name": "Bear Put Spread",   "description": "Buy higher Put + Sell lower Put", "outlook": "Moderately Bearish"},
    "long_straddle":     {"name": "Long Straddle",     "description": "Buy ATM Call + Buy ATM Put", "outlook": "High Volatility Expected"},
    "long_strangle":     {"name": "Long Strangle",     "description": "Buy OTM Call + Buy OTM Put", "outlook": "Very High Volatility Expected"},
    "iron_condor":       {"name": "Iron Condor",       "description": "Sell Strangle + Buy Wings", "outlook": "Neutral / Low Volatility"},
    "butterfly":         {"name": "Butterfly Spread",  "description": "Buy 1 low + Sell 2 mid + Buy 1 high Call", "outlook": "Neutral / Pin to Strike"},
    "covered_call":      {"name": "Covered Call",      "description": "Long Stock + Sell OTM Call", "outlook": "Slightly Bullish"},
    "protective_put":    {"name": "Protective Put",    "description": "Long Stock + Buy OTM Put", "outlook": "Bullish with Downside Protection"},
}


@router.get("/price")
async def option_price(
    option_type: str = Query("call", description="call | put"),
    spot: float = Query(..., description="Current spot price"),
    strike: float = Query(..., description="Strike price"),
    time_to_expiry: float = Query(..., description="Time to expiry in years"),
    risk_free_rate: float = Query(0.0225, ge=0, le=0.5),
    volatility: float = Query(0.20, ge=0.01, le=5.0),
    dividend_yield: float = Query(0.0, ge=0, le=0.2),
):
    result = price_option(option_type, spot, strike, time_to_expiry, risk_free_rate, volatility, dividend_yield)
    return {
        "option_type": result.option_type,
        "spot": result.spot,
        "strike": result.strike,
        "time_to_expiry": result.time_to_expiry,
        "price": result.price,
        "intrinsic_value": result.intrinsic_value,
        "time_value": result.time_value,
        "greeks": {
            "delta": result.delta,
            "gamma": result.gamma,
            "theta": result.theta,
            "vega": result.vega,
            "rho": result.rho,
        },
    }


@router.get("/analyze")
async def option_analyze(
    asset_id: str = Query(..., description="Asset UUID"),
    strike: float = Query(0, description="Strike price (0 = auto ATM)"),
    time_to_expiry: float = Query(0.25, description="Time to expiry in years"),
    risk_free_rate: float = Query(0.0225, ge=0, le=0.5),
    conn=Depends(get_conn),
):
    """Full option analysis: live market data + BS pricing + AI suggestion."""
    # Resolve asset_id → symbol
    row = await conn.fetchrow(
        "SELECT symbol, exchange FROM assets WHERE asset_id = $1::uuid", asset_id
    )
    if not row:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")

    symbol = row["symbol"]
    exchange = row["exchange"]
    if exchange and exchange.upper() in ("SET", "MAI"):
        symbol = f"{symbol}.BK" if not symbol.endswith(".BK") else symbol

    result = analyze_option(symbol, strike, time_to_expiry, risk_free_rate)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Analysis failed"))
    return result


@router.get("/implied-volatility")
async def calc_implied_volatility(
    option_type: str = Query("call"),
    market_price: float = Query(..., description="Observed market price"),
    spot: float = Query(...),
    strike: float = Query(...),
    time_to_expiry: float = Query(...),
    risk_free_rate: float = Query(0.0225),
    dividend_yield: float = Query(0.0),
):
    result = implied_volatility(option_type, market_price, spot, strike, time_to_expiry, risk_free_rate, dividend_yield)
    return result


@router.get("/strategies")
async def list_strategies():
    """List all available preset option strategies."""
    return {"strategies": PRESET_STRATEGIES}


@router.get("/strategy/preset/{strategy_name}")
async def preset_strategy(
    strategy_name: str,
    spot: float = Query(..., description="Current spot price"),
    time_to_expiry: float = Query(0.25),
    risk_free_rate: float = Query(0.0225),
    volatility: float = Query(0.20),
    width: float = Query(0, description="Spread width (0 = auto 5% OTM)"),
):
    """Generate a preset strategy with auto-calculated strikes."""
    if strategy_name not in PRESET_STRATEGIES:
        raise HTTPException(status_code=404, detail=f"Strategy '{strategy_name}' not found")

    S = spot
    w = width if width > 0 else round(S * 0.05, 2)
    K_atm = round(S)

    leg_defs = {
        "bull_call_spread": [
            {"option_type": "call", "strike": K_atm, "position": "long"},
            {"option_type": "call", "strike": K_atm + w, "position": "short"},
        ],
        "bear_put_spread": [
            {"option_type": "put", "strike": K_atm, "position": "long"},
            {"option_type": "put", "strike": K_atm - w, "position": "short"},
        ],
        "long_straddle": [
            {"option_type": "call", "strike": K_atm, "position": "long"},
            {"option_type": "put", "strike": K_atm, "position": "long"},
        ],
        "long_strangle": [
            {"option_type": "call", "strike": K_atm + w, "position": "long"},
            {"option_type": "put", "strike": K_atm - w, "position": "long"},
        ],
        "iron_condor": [
            {"option_type": "put", "strike": K_atm - 2*w, "position": "long"},
            {"option_type": "put", "strike": K_atm - w, "position": "short"},
            {"option_type": "call", "strike": K_atm + w, "position": "short"},
            {"option_type": "call", "strike": K_atm + 2*w, "position": "long"},
        ],
        "butterfly": [
            {"option_type": "call", "strike": K_atm - w, "position": "long"},
            {"option_type": "call", "strike": K_atm, "position": "short", "quantity": 2},
            {"option_type": "call", "strike": K_atm + w, "position": "long"},
        ],
        "covered_call": [
            {"option_type": "stock", "strike": S, "position": "long"},
            {"option_type": "call", "strike": K_atm + w, "position": "short"},
        ],
        "protective_put": [
            {"option_type": "stock", "strike": S, "position": "long"},
            {"option_type": "put", "strike": K_atm - w, "position": "long"},
        ],
    }

    legs = leg_defs[strategy_name]
    return _compute_strategy(S, legs, time_to_expiry, risk_free_rate, volatility, strategy_name)


@router.post("/strategy/custom")
async def custom_strategy(req: StrategyRequest):
    """Compute a custom multi-leg option strategy."""
    legs = [leg.model_dump() for leg in req.legs]
    return _compute_strategy(req.spot, legs, req.time_to_expiry, req.risk_free_rate, req.volatility, "custom")


def _compute_strategy(spot, legs, T, r, vol, strategy_name):
    """Core strategy computation: pricing, combined Greeks, payoff curve, breakevens."""
    import numpy as np

    meta = PRESET_STRATEGIES.get(strategy_name, {"name": "Custom Strategy", "description": "", "outlook": ""})

    # Price each leg
    leg_results = []
    total_cost = 0.0
    combined_greeks = {"delta": 0, "gamma": 0, "theta": 0, "vega": 0, "rho": 0}

    for leg in legs:
        qty = leg.get("quantity", 1)
        sign = 1 if leg["position"] == "long" else -1

        if leg["option_type"] == "stock":
            # Stock position
            leg_results.append({
                "option_type": "stock", "strike": leg["strike"], "position": leg["position"],
                "quantity": qty, "price": spot, "greeks": {"delta": sign * qty, "gamma": 0, "theta": 0, "vega": 0, "rho": 0},
            })
            total_cost += sign * qty * spot
            combined_greeks["delta"] += sign * qty
            continue

        opt = price_option(leg["option_type"], spot, leg["strike"], T, r, vol)
        premium = opt.price * qty
        total_cost += sign * premium

        for g in combined_greeks:
            combined_greeks[g] += sign * qty * getattr(opt, g)

        leg_results.append({
            "option_type": leg["option_type"], "strike": leg["strike"],
            "position": leg["position"], "quantity": qty,
            "price": round(opt.price, 4), "premium": round(premium, 4),
            "greeks": {g: round(sign * qty * getattr(opt, g), 6) for g in combined_greeks},
        })

    # Round combined greeks
    for g in combined_greeks:
        combined_greeks[g] = round(combined_greeks[g], 6)

    # Payoff curve (80 points)
    all_strikes = [l["strike"] for l in legs]
    K_min, K_max = min(all_strikes), max(all_strikes)
    spread = K_max - K_min if K_max > K_min else spot * 0.1
    spot_range = np.linspace(max(K_min - spread * 2, spot * 0.5), K_max + spread * 2, 80)

    payoff_at_expiry = []
    value_now = []

    for s_price in spot_range:
        pnl_expiry = 0.0
        pnl_now = 0.0

        for leg in legs:
            qty = leg.get("quantity", 1)
            sign = 1 if leg["position"] == "long" else -1
            K = leg["strike"]

            if leg["option_type"] == "stock":
                pnl_expiry += sign * qty * (s_price - K)
                pnl_now += sign * qty * (s_price - K)
                continue

            # Payoff at expiry
            if leg["option_type"] == "call":
                intrinsic = max(s_price - K, 0)
            else:
                intrinsic = max(K - s_price, 0)

            opt_orig = price_option(leg["option_type"], spot, K, T, r, vol)
            pnl_expiry += sign * qty * (intrinsic - opt_orig.price)

            # Current value (B-S with remaining time)
            if T > 0.001:
                opt_now = price_option(leg["option_type"], s_price, K, T, r, vol)
                pnl_now += sign * qty * (opt_now.price - opt_orig.price)
            else:
                pnl_now += sign * qty * (intrinsic - opt_orig.price)

        payoff_at_expiry.append(round(float(pnl_expiry), 4))
        value_now.append(round(float(pnl_now), 4))

    spot_list = [round(float(s), 4) for s in spot_range]

    # Max profit / max loss / breakevens
    max_profit = round(max(payoff_at_expiry), 4)
    max_loss = round(min(payoff_at_expiry), 4)

    # Find breakevens (where payoff crosses zero)
    breakevens = []
    for i in range(len(payoff_at_expiry) - 1):
        if payoff_at_expiry[i] * payoff_at_expiry[i+1] < 0:
            # Linear interpolation
            x1, x2 = spot_list[i], spot_list[i+1]
            y1, y2 = payoff_at_expiry[i], payoff_at_expiry[i+1]
            be = x1 - y1 * (x2 - x1) / (y2 - y1)
            breakevens.append(round(be, 2))

    risk_reward = abs(max_profit / max_loss) if max_loss != 0 else 999.0

    return {
        "success": True,
        "strategy": meta,
        "spot": spot,
        "time_to_expiry": T,
        "volatility": vol,
        "risk_free_rate": r,
        "legs": leg_results,
        "net_cost": round(total_cost, 4),
        "combined_greeks": combined_greeks,
        "max_profit": max_profit,
        "max_loss": max_loss,
        "breakevens": breakevens,
        "risk_reward_ratio": round(risk_reward, 2),
        "payoff_curve": {
            "spot_range": spot_list,
            "payoff_at_expiry": payoff_at_expiry,
            "value_now": value_now,
        },
    }


@router.get("/strategy/watchlist-scan")
async def scan_watchlist_strategies(
    watchlist_name: str = Query("Angles", description="Watchlist name"),
    time_to_expiry: float = Query(0.25),
    risk_free_rate: float = Query(0.0225),
    conn=Depends(get_conn),
):
    """
    Scan all assets in a watchlist → analyze direction → suggest optimal strategy → rank by gain.
    """
    import numpy as np
    from datetime import date, timedelta

    # Find watchlist
    wl = await conn.fetchrow(
        "SELECT watchlist_id FROM watchlists WHERE LOWER(name) = LOWER($1) AND is_active = true",
        watchlist_name,
    )
    if not wl:
        raise HTTPException(status_code=404, detail=f"Watchlist '{watchlist_name}' not found")

    items = await conn.fetch("""
        SELECT a.asset_id, a.symbol, a.name, a.sector
        FROM watchlist_items wi JOIN assets a ON wi.asset_id = a.asset_id
        WHERE wi.watchlist_id = $1 ORDER BY a.symbol
    """, wl["watchlist_id"])

    if not items:
        return {"success": True, "results": [], "watchlist": watchlist_name}

    # Batch fetch prices from DB (fast, no rate limit)
    asset_ids = [item["asset_id"] for item in items]
    cutoff = date.today() - timedelta(days=120)
    price_rows = await conn.fetch(
        """SELECT asset_id, date, close_price
           FROM historical_prices
           WHERE asset_id = ANY($1) AND date >= $2
           ORDER BY asset_id, date""",
        asset_ids, cutoff,
    )
    # Group by asset_id
    prices_by_asset: dict = {}
    for r in price_rows:
        aid = r["asset_id"]
        if aid not in prices_by_asset:
            prices_by_asset[aid] = []
        prices_by_asset[aid].append(float(r["close_price"]))

    results = []
    for item in items:
        sym = item["symbol"]
        try:
            closes = prices_by_asset.get(item["asset_id"], [])
            if len(closes) < 10:
                continue

            spot = closes[-1]
            if not np.isfinite(spot) or spot <= 0:
                continue
            closes_arr = np.array(closes)
            returns_arr = np.diff(np.log(closes_arr))
            vol = float(np.std(returns_arr) * np.sqrt(252))
            if not np.isfinite(vol) or vol < 0.01:
                vol = 0.20

            # Direction analysis from DB prices
            n = len(closes_arr)
            ma20 = float(np.mean(closes_arr[-20:])) if n >= 20 else spot
            ma50 = float(np.mean(closes_arr[-50:])) if n >= 50 else spot
            momentum = float(np.sum(returns_arr[-5:])) if len(returns_arr) >= 5 else 0
            rsi_delta = float(np.mean(returns_arr[-14:])) if len(returns_arr) >= 14 else 0

            score = 0
            if spot > ma20: score += 1
            if spot > ma50: score += 1
            if momentum > 0: score += 1
            if rsi_delta > 0: score += 1
            if spot < ma20: score -= 1
            if spot < ma50: score -= 1
            if momentum < 0: score -= 1
            if rsi_delta < 0: score -= 1

            # Select best strategy based on direction + volatility
            if score >= 2:
                if vol > 0.35:
                    strategy = "bull_call_spread"  # high vol → spread to cap cost
                else:
                    strategy = "covered_call"  # low vol → premium income
                direction = "bullish"
            elif score <= -2:
                if vol > 0.35:
                    strategy = "bear_put_spread"
                else:
                    strategy = "protective_put"
                direction = "bearish"
            else:
                if vol > 0.30:
                    strategy = "long_straddle"  # high vol → profit from movement
                else:
                    strategy = "iron_condor"  # low vol → profit from range
                direction = "neutral"

            # Compute strategy
            K_atm = round(spot) if spot < 1e8 else spot
            w = round(spot * 0.05, 2)
            if w < 0.01:
                w = max(spot * 0.05, 0.01)
            leg_defs = {
                "bull_call_spread": [
                    {"option_type": "call", "strike": K_atm, "position": "long"},
                    {"option_type": "call", "strike": K_atm + w, "position": "short"},
                ],
                "bear_put_spread": [
                    {"option_type": "put", "strike": K_atm, "position": "long"},
                    {"option_type": "put", "strike": K_atm - w, "position": "short"},
                ],
                "long_straddle": [
                    {"option_type": "call", "strike": K_atm, "position": "long"},
                    {"option_type": "put", "strike": K_atm, "position": "long"},
                ],
                "iron_condor": [
                    {"option_type": "put", "strike": K_atm - 2*w, "position": "long"},
                    {"option_type": "put", "strike": K_atm - w, "position": "short"},
                    {"option_type": "call", "strike": K_atm + w, "position": "short"},
                    {"option_type": "call", "strike": K_atm + 2*w, "position": "long"},
                ],
                "covered_call": [
                    {"option_type": "stock", "strike": spot, "position": "long"},
                    {"option_type": "call", "strike": K_atm + w, "position": "short"},
                ],
                "protective_put": [
                    {"option_type": "stock", "strike": spot, "position": "long"},
                    {"option_type": "put", "strike": K_atm - w, "position": "long"},
                ],
            }

            legs = leg_defs.get(strategy, leg_defs["bull_call_spread"])
            # Validate all strikes are finite
            if any(not np.isfinite(l["strike"]) for l in legs):
                continue

            strat_result = _compute_strategy(spot, legs, time_to_expiry, risk_free_rate, vol, strategy)

            max_profit = strat_result["max_profit"]
            max_loss = strat_result["max_loss"]
            net_cost = strat_result["net_cost"]
            rr = strat_result.get("risk_reward_ratio")

            # Gain score = risk_reward * direction_confidence
            confidence = abs(score) / 4.0
            gain_score = (rr if rr and rr > 0 else 0) * confidence

            results.append({
                "symbol": sym,
                "name": item["name"],
                "sector": item.get("sector"),
                "spot": round(spot, 2),
                "volatility": round(vol, 4),
                "direction": direction,
                "direction_score": score,
                "strategy": PRESET_STRATEGIES[strategy],
                "strategy_key": strategy,
                "max_profit": max_profit,
                "max_loss": max_loss,
                "net_cost": net_cost,
                "risk_reward": rr,
                "breakevens": strat_result["breakevens"],
                "gain_score": round(gain_score, 2),
                "combined_greeks": strat_result["combined_greeks"],
            })
        except Exception as e:
            results.append({
                "symbol": sym, "name": item["name"], "error": str(e),
                "gain_score": 0,
            })

    # Sort by gain_score descending
    results.sort(key=lambda x: x.get("gain_score", 0), reverse=True)

    return {
        "success": True,
        "watchlist": watchlist_name,
        "count": len(results),
        "results": results,
    }


@router.get("/greeks-surface")
async def greeks_surface(
    option_type: str = Query("call"),
    spot: float = Query(...),
    risk_free_rate: float = Query(0.0225),
    volatility: float = Query(0.20),
    n_strikes: int = Query(20, ge=5, le=50),
    n_expiries: int = Query(20, ge=5, le=50),
):
    result = generate_greeks_surface(option_type, spot, risk_free_rate, volatility,
                                     n_strikes=n_strikes, n_expiries=n_expiries)
    return result
