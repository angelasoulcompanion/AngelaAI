"""
Pythia — Black-Scholes Options Pricing Service
European options: Call/Put pricing, Greeks, Implied Volatility.
"""
from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq

from config import PythiaConfig


@dataclass
class OptionPrice:
    option_type: str  # call or put
    spot: float
    strike: float
    time_to_expiry: float
    risk_free_rate: float
    volatility: float
    price: float
    intrinsic_value: float
    time_value: float
    # Greeks
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    success: bool = True
    message: str = ""


def price_option(
    option_type: str,
    spot: float,
    strike: float,
    time_to_expiry: float,
    risk_free_rate: float,
    volatility: float,
    dividend_yield: float = 0.0,
) -> OptionPrice:
    """Price a European option using Black-Scholes-Merton."""
    if time_to_expiry <= 0:
        intrinsic = max(spot - strike, 0) if option_type == "call" else max(strike - spot, 0)
        return OptionPrice(
            option_type=option_type, spot=spot, strike=strike,
            time_to_expiry=0, risk_free_rate=risk_free_rate, volatility=volatility,
            price=intrinsic, intrinsic_value=intrinsic, time_value=0,
            delta=1.0 if option_type == "call" and spot > strike else (-1.0 if option_type == "put" and spot < strike else 0.0),
            gamma=0, theta=0, vega=0, rho=0,
        )

    T = time_to_expiry
    S = spot
    K = strike
    r = risk_free_rate
    q = dividend_yield
    sigma = volatility

    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == "call":
        price = S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        delta = np.exp(-q * T) * norm.cdf(d1)
        intrinsic = max(S - K, 0)
        rho_val = K * T * np.exp(-r * T) * norm.cdf(d2) / 100
    else:  # put
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)
        delta = -np.exp(-q * T) * norm.cdf(-d1)
        intrinsic = max(K - S, 0)
        rho_val = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100

    gamma = np.exp(-q * T) * norm.pdf(d1) / (S * sigma * np.sqrt(T))
    theta = (-(S * sigma * np.exp(-q * T) * norm.pdf(d1)) / (2 * np.sqrt(T))
             - r * K * np.exp(-r * T) * (norm.cdf(d2) if option_type == "call" else norm.cdf(-d2))
             + q * S * np.exp(-q * T) * (norm.cdf(d1) if option_type == "call" else norm.cdf(-d1))) / 365
    vega = S * np.exp(-q * T) * norm.pdf(d1) * np.sqrt(T) / 100

    return OptionPrice(
        option_type=option_type, spot=spot, strike=strike,
        time_to_expiry=T, risk_free_rate=r, volatility=sigma,
        price=round(float(price), 4),
        intrinsic_value=round(float(intrinsic), 4),
        time_value=round(float(price - intrinsic), 4),
        delta=round(float(delta), 6),
        gamma=round(float(gamma), 6),
        theta=round(float(theta), 6),
        vega=round(float(vega), 6),
        rho=round(float(rho_val), 6),
    )


def implied_volatility(
    option_type: str,
    market_price: float,
    spot: float,
    strike: float,
    time_to_expiry: float,
    risk_free_rate: float,
    dividend_yield: float = 0.0,
) -> dict:
    """Calculate implied volatility from market price using Brent's method."""
    def objective(sigma: float) -> float:
        result = price_option(option_type, spot, strike, time_to_expiry, risk_free_rate, sigma, dividend_yield)
        return result.price - market_price

    try:
        iv = brentq(objective, 0.001, 5.0, xtol=1e-8)
        return {
            "implied_volatility": round(float(iv), 6),
            "market_price": market_price,
            "success": True,
        }
    except ValueError:
        return {
            "implied_volatility": None,
            "market_price": market_price,
            "success": False,
            "message": "Cannot find implied volatility in range [0.1%, 500%]",
        }


def analyze_option(
    symbol: str,
    strike: float,
    time_to_expiry: float,
    risk_free_rate: float = 0.0225,
) -> dict:
    """
    Full option analysis: fetch market data, price call+put, generate AI suggestion.
    Uses yfinance for live data + technical indicators.
    """
    import yfinance as yf

    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="1y", interval="1d")
    if hist.empty:
        return {"success": False, "error": f"No data for {symbol}"}

    info = ticker.info or {}
    spot = info.get("regularMarketPrice") or info.get("currentPrice") or float(hist["Close"].iloc[-1])
    if not spot or spot <= 0:
        return {"success": False, "error": f"Cannot get price for {symbol}"}

    name = info.get("shortName") or info.get("longName") or symbol
    prev_close = info.get("regularMarketPreviousClose") or info.get("previousClose") or spot
    change_pct = (spot - prev_close) / prev_close if prev_close else 0

    # Historical volatility (30-day annualized)
    returns = np.log(hist["Close"] / hist["Close"].shift(1)).dropna()
    vol_std = returns[-30:].std() if len(returns) >= 30 else returns.std()
    hist_vol = float(vol_std * np.sqrt(252)) if vol_std and vol_std > 0 else 0.20

    # Auto strike = spot rounded if not provided meaningfully
    if strike <= 0:
        strike = round(spot, 0)
    if strike <= 0:
        strike = spot

    # Price BOTH call and put
    call = price_option("call", spot, strike, time_to_expiry, risk_free_rate, hist_vol)
    put = price_option("put", spot, strike, time_to_expiry, risk_free_rate, hist_vol)

    # --- Technical Signal Analysis ---
    closes = hist["Close"].values
    score = 0
    signals = []

    # 1. MA Trend (50 & 200)
    if len(closes) >= 50:
        ma50 = float(np.mean(closes[-50:]))
        above_50 = spot > ma50
    else:
        ma50 = None
        above_50 = None

    if len(closes) >= 200:
        ma200 = float(np.mean(closes[-200:]))
        above_200 = spot > ma200
    else:
        ma200 = None
        above_200 = None

    if above_50 is not None and above_200 is not None:
        if above_50 and above_200:
            score += 2
            signals.append({"name": "MA Trend", "value": "Bullish", "detail": f"Price above 50MA ({ma50:.2f}) & 200MA ({ma200:.2f})", "signal": "bullish"})
        elif above_50:
            score += 1
            signals.append({"name": "MA Trend", "value": "Mixed", "detail": f"Above 50MA ({ma50:.2f}), below 200MA ({ma200:.2f})", "signal": "neutral"})
        else:
            score -= 2
            signals.append({"name": "MA Trend", "value": "Bearish", "detail": f"Price below 50MA ({ma50:.2f}) & 200MA ({ma200:.2f})", "signal": "bearish"})
    elif above_50 is not None:
        if above_50:
            score += 1
            signals.append({"name": "MA Trend", "value": "Bullish", "detail": f"Price above 50MA ({ma50:.2f})", "signal": "bullish"})
        else:
            score -= 1
            signals.append({"name": "MA Trend", "value": "Bearish", "detail": f"Price below 50MA ({ma50:.2f})", "signal": "bearish"})

    # 2. RSI (14)
    if len(returns) >= 14:
        deltas = hist["Close"].diff().dropna().values[-14:]
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        rs = avg_gain / avg_loss if avg_loss > 0 else 100
        rsi = 100 - (100 / (1 + rs))
        rsi = round(float(rsi), 1)

        if rsi > 70:
            score -= 1
            signals.append({"name": "RSI (14)", "value": rsi, "detail": "Overbought — reversal risk", "signal": "bearish"})
        elif rsi < 30:
            score += 1
            signals.append({"name": "RSI (14)", "value": rsi, "detail": "Oversold — bounce expected", "signal": "bullish"})
        else:
            signals.append({"name": "RSI (14)", "value": rsi, "detail": "Neutral range", "signal": "neutral"})

    # 3. MACD (12, 26, 9)
    if len(closes) >= 26:
        ema12 = _ema_calc(closes, 12)
        ema26 = _ema_calc(closes, 26)
        macd_line = ema12 - ema26
        signal_line = _ema_calc(macd_line[-9:], 9) if len(macd_line) >= 9 else np.array([0])

        macd_val = float(macd_line[-1])
        sig_val = float(signal_line[-1])
        if macd_val > sig_val:
            score += 1
            signals.append({"name": "MACD", "value": f"{macd_val:.3f}", "detail": "Bullish crossover (MACD > Signal)", "signal": "bullish"})
        else:
            score -= 1
            signals.append({"name": "MACD", "value": f"{macd_val:.3f}", "detail": "Bearish crossover (MACD < Signal)", "signal": "bearish"})

    # 4. 1-Month momentum
    if len(closes) >= 22:
        ret_1m = (closes[-1] / closes[-22] - 1) * 100
        ret_1m = round(float(ret_1m), 1)
        if ret_1m > 0:
            score += 1
            signals.append({"name": "Momentum 1M", "value": f"+{ret_1m}%", "detail": "Positive short-term trend", "signal": "bullish"})
        else:
            score -= 1
            signals.append({"name": "Momentum 1M", "value": f"{ret_1m}%", "detail": "Negative short-term trend", "signal": "bearish"})

    # Direction & confidence
    if score >= 2:
        direction, confidence = "call", "high"
    elif score == 1:
        direction, confidence = "call", "medium"
    elif score == 0:
        direction, confidence = "neutral", "low"
    elif score == -1:
        direction, confidence = "put", "medium"
    else:
        direction, confidence = "put", "high"

    # Summary
    if direction == "call":
        summary = f"Technical signals lean bullish (score {score}) — แนะนำ Call"
    elif direction == "put":
        summary = f"Technical signals lean bearish (score {score}) — แนะนำ Put"
    else:
        summary = f"Mixed signals (score {score}) — ไม่มีแนวโน้มชัดเจน consider Straddle"

    # --- Recommended Contract ---
    # OTM strike ~5% away for directional bet, ATM for neutral
    if direction == "call":
        rec_strike = round(spot * 1.05, 2)  # 5% OTM call
        rec_option = price_option("call", spot, rec_strike, time_to_expiry, risk_free_rate, hist_vol)
        rec_premium = rec_option.price
        rec_breakeven = rec_strike + rec_premium
        rec_profit_target = round(spot * 1.10, 2)  # 10% up from spot
        rec_max_loss = rec_premium
        rec_type = "call"
    elif direction == "put":
        rec_strike = round(spot * 0.95, 2)  # 5% OTM put
        rec_option = price_option("put", spot, rec_strike, time_to_expiry, risk_free_rate, hist_vol)
        rec_premium = rec_option.price
        rec_breakeven = rec_strike - rec_premium
        rec_profit_target = round(spot * 0.90, 2)  # 10% down from spot
        rec_max_loss = rec_premium
        rec_type = "put"
    else:
        # Neutral — ATM straddle
        rec_strike = strike
        rec_premium = call.price + put.price
        rec_breakeven = strike  # simplified
        rec_profit_target = spot
        rec_max_loss = rec_premium
        rec_type = "straddle"

    contract = {
        "type": rec_type,
        "strike": round(rec_strike, 2),
        "expiry_years": time_to_expiry,
        "premium": round(rec_premium, 4),
        "breakeven": round(rec_breakeven, 4),
        "profit_target": round(rec_profit_target, 2),
        "max_loss": round(rec_max_loss, 4),
        "risk_reward": round((abs(rec_profit_target - rec_breakeven) / rec_premium), 2) if rec_premium > 0 else 0,
    }

    def _option_dict(op: OptionPrice) -> dict:
        return {
            "price": op.price,
            "intrinsic_value": op.intrinsic_value,
            "time_value": op.time_value,
            "greeks": {
                "delta": op.delta, "gamma": op.gamma,
                "theta": op.theta, "vega": op.vega, "rho": op.rho,
            },
        }

    # B-S model internals for display
    T = time_to_expiry
    sigma = hist_vol
    d1_val = (np.log(spot / strike) + (risk_free_rate + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2_val = d1_val - sigma * np.sqrt(T)

    return {
        "success": True,
        "symbol": symbol,
        "spot": round(spot, 4),
        "historical_vol": round(hist_vol, 4),
        "bs_model": {
            "d1": round(float(d1_val), 6),
            "d2": round(float(d2_val), 6),
            "n_d1": round(float(norm.cdf(d1_val)), 6),
            "n_d2": round(float(norm.cdf(d2_val)), 6),
            "n_neg_d1": round(float(norm.cdf(-d1_val)), 6),
            "n_neg_d2": round(float(norm.cdf(-d2_val)), 6),
            "discount_factor": round(float(np.exp(-risk_free_rate * T)), 6),
            "forward_price": round(float(spot * np.exp(risk_free_rate * T)), 4),
        },
        "quote": {
            "current_price": round(spot, 4),
            "change_percent": round(change_pct, 4),
            "name": name,
        },
        "strike": strike,
        "time_to_expiry": time_to_expiry,
        "risk_free_rate": risk_free_rate,
        "call": _option_dict(call),
        "put": _option_dict(put),
        "suggestion": {
            "direction": direction,
            "confidence": confidence,
            "score": score,
            "signals": signals,
            "summary": summary,
            "contract": contract,
        },
    }


def _ema_calc(data, period: int):
    """Simple EMA calculation for numpy array."""
    arr = np.asarray(data, dtype=float)
    if len(arr) < period:
        return arr
    k = 2.0 / (period + 1)
    result = np.empty_like(arr)
    result[0] = arr[0]
    for i in range(1, len(arr)):
        result[i] = arr[i] * k + result[i - 1] * (1 - k)
    return result


def generate_greeks_surface(
    option_type: str,
    spot: float,
    risk_free_rate: float,
    volatility: float,
    strike_range: tuple[float, float] = (0.8, 1.2),
    expiry_range: tuple[float, float] = (0.05, 2.0),
    n_strikes: int = 20,
    n_expiries: int = 20,
) -> dict:
    """Generate Greeks surface data for 3D visualization."""
    strikes = np.linspace(spot * strike_range[0], spot * strike_range[1], n_strikes)
    expiries = np.linspace(expiry_range[0], expiry_range[1], n_expiries)

    surface = []
    for K in strikes:
        for T in expiries:
            result = price_option(option_type, spot, float(K), float(T), risk_free_rate, volatility)
            surface.append({
                "strike": round(float(K), 2),
                "expiry": round(float(T), 4),
                "price": result.price,
                "delta": result.delta,
                "gamma": result.gamma,
                "theta": result.theta,
                "vega": result.vega,
            })

    return {
        "option_type": option_type,
        "spot": spot,
        "volatility": volatility,
        "risk_free_rate": risk_free_rate,
        "surface": surface,
    }
