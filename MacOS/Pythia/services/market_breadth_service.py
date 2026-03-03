"""
Pythia — Market Breadth Service
Computes breadth indicators from constituent prices using yfinance batch download.
10 indicators: A/D Line, A/D Ratio, % Above MA, New Highs/Lows, High-Low Index,
McClellan Oscillator/Summation, TRIN (Arms Index), Zweig Breadth Thrust.
"""
import time
from typing import Optional

import numpy as np
import yfinance as yf

# ── Predefined Universes ─────────────────────────────────

SET50_SYMBOLS = [
    "ADVANC.BK", "AOT.BK", "AWC.BK", "BANPU.BK", "BBL.BK",
    "BDMS.BK", "BEM.BK", "BGRIM.BK", "BH.BK", "BTS.BK",
    "CBG.BK", "CENTEL.BK", "COM7.BK", "CPALL.BK", "CPF.BK",
    "CPN.BK", "CRC.BK", "DELTA.BK", "EA.BK", "EGCO.BK",
    "GLOBAL.BK", "GPSC.BK", "GULF.BK", "HMPRO.BK", "INTUCH.BK",
    "IVL.BK", "KBANK.BK", "KCE.BK", "KTB.BK", "KTC.BK",
    "LH.BK", "MINT.BK", "MTC.BK", "OR.BK", "OSP.BK",
    "PTT.BK", "PTTEP.BK", "PTTGC.BK", "RATCH.BK", "SAWAD.BK",
    "SCB.BK", "SCC.BK", "SCGP.BK", "TISCO.BK", "TOP.BK",
    "TRUE.BK", "TTB.BK", "TU.BK", "WHA.BK", "TIDLOR.BK",
]

SP100_SYMBOLS = [
    "AAPL", "ABBV", "ABT", "ACN", "ADBE", "AIG", "AMD", "AMGN", "AMT", "AMZN",
    "AVGO", "AXP", "BA", "BAC", "BK", "BKNG", "BLK", "BMY", "BRK-B", "C",
    "CAT", "CHTR", "CL", "CMCSA", "COF", "COP", "COST", "CRM", "CSCO", "CVS",
    "CVX", "DE", "DHR", "DIS", "DOW", "DUK", "EMR", "EXC", "F", "FDX",
    "GD", "GE", "GILD", "GM", "GOOG", "GOOGL", "GS", "HD", "HON", "IBM",
    "INTC", "INTU", "JNJ", "JPM", "KHC", "KO", "LIN", "LLY", "LMT", "LOW",
    "MA", "MCD", "MDLZ", "MDT", "MET", "META", "MMM", "MO", "MRK", "MS",
    "MSFT", "NEE", "NFLX", "NKE", "NVDA", "ORCL", "PEP", "PFE", "PG", "PM",
    "PYPL", "QCOM", "RTX", "SBUX", "SCHW", "SO", "SPG", "T", "TGT", "TMO",
    "TMUS", "TSLA", "TXN", "UNH", "UNP", "UPS", "USB", "V", "VZ", "WFC",
]

UNIVERSES = {
    "SET50": {"name": "SET50 Index", "symbols": SET50_SYMBOLS, "type": "index"},
    "SP100": {"name": "S&P 100", "symbols": SP100_SYMBOLS, "type": "index"},
}


# ── Helpers ───────────────────────────────────────────────

def _sma(data: np.ndarray, period: int) -> np.ndarray:
    """Simple Moving Average (vectorized)."""
    result = np.full_like(data, np.nan, dtype=float)
    if len(data) < period:
        return result
    cumsum = np.cumsum(data)
    cumsum = np.insert(cumsum, 0, 0)
    result[period - 1:] = (cumsum[period:] - cumsum[:-period]) / period
    return result


def _ema(data: np.ndarray, period: int) -> np.ndarray:
    """Exponential Moving Average."""
    result = np.full_like(data, np.nan, dtype=float)
    if len(data) < period:
        return result
    k = 2.0 / (period + 1)
    result[period - 1] = np.nanmean(data[:period])
    for i in range(period, len(data)):
        result[i] = data[i] * k + result[i - 1] * (1 - k)
    return result


# ── Cache ─────────────────────────────────────────────────

_cache: dict[str, tuple[float, dict]] = {}
CACHE_TTL = 900  # 15 minutes


def _cache_key(universe: str, period: str) -> str:
    return f"{universe}:{period}"


def _get_cached(key: str) -> Optional[dict]:
    if key in _cache:
        ts, data = _cache[key]
        if time.time() - ts < CACHE_TTL:
            return data
        del _cache[key]
    return None


def _set_cached(key: str, data: dict) -> None:
    _cache[key] = (time.time(), data)


# ── Core Computation ──────────────────────────────────────

def compute_breadth(symbols: list[str], period: str = "1y") -> dict:
    """
    Download OHLCV for all symbols via yfinance batch and compute 10 breadth indicators.
    Returns dict with dates, indicators, current snapshot, and regime classification.
    """
    # 1) Batch download
    raw = yf.download(symbols, period=period, group_by="ticker", threads=True, progress=False)
    if raw.empty:
        return {"success": False, "error": "No data returned from Yahoo Finance"}

    # 2) Build close and volume matrices (dates × stocks)
    dates_idx = raw.index
    n_days = len(dates_idx)

    # Handle single vs multi-ticker DataFrame structure
    if len(symbols) == 1:
        close_matrix = raw["Close"].values.reshape(-1, 1)
        volume_matrix = raw["Volume"].values.reshape(-1, 1)
    else:
        close_cols = []
        volume_cols = []
        valid_symbols = []
        for sym in symbols:
            try:
                c = raw[(sym, "Close")].values
                v = raw[(sym, "Volume")].values
                close_cols.append(c)
                volume_cols.append(v)
                valid_symbols.append(sym)
            except (KeyError, TypeError):
                continue

        if not close_cols:
            return {"success": False, "error": "No valid price data"}

        close_matrix = np.column_stack(close_cols)
        volume_matrix = np.column_stack(volume_cols)

    n_stocks = close_matrix.shape[1]
    dates_str = [d.strftime("%Y-%m-%d") for d in dates_idx]

    # 3) Daily changes
    prev_close = np.roll(close_matrix, 1, axis=0)
    prev_close[0, :] = np.nan
    daily_change = close_matrix - prev_close

    advances = np.nansum(daily_change > 0, axis=1).astype(float)
    declines = np.nansum(daily_change < 0, axis=1).astype(float)
    unchanged = np.nansum(daily_change == 0, axis=1).astype(float)
    advances[0] = np.nan
    declines[0] = np.nan
    unchanged[0] = np.nan

    # 4) A/D Line & Ratio
    ad_diff = advances - declines
    ad_line = np.nancumsum(np.nan_to_num(ad_diff))
    ad_line[0] = np.nan

    ad_ratio = np.where(declines > 0, advances / declines, advances)
    ad_ratio[0] = np.nan

    # 5) % Above 50-day and 200-day MA
    sma50_matrix = np.full_like(close_matrix, np.nan)
    sma200_matrix = np.full_like(close_matrix, np.nan)
    for j in range(n_stocks):
        sma50_matrix[:, j] = _sma(close_matrix[:, j], 50)
        sma200_matrix[:, j] = _sma(close_matrix[:, j], 200)

    above_50 = np.nansum(close_matrix > sma50_matrix, axis=1)
    valid_50 = np.nansum(~np.isnan(sma50_matrix), axis=1)
    pct_above_50ma = np.where(valid_50 > 0, above_50 / valid_50 * 100, np.nan)

    above_200 = np.nansum(close_matrix > sma200_matrix, axis=1)
    valid_200 = np.nansum(~np.isnan(sma200_matrix), axis=1)
    pct_above_200ma = np.where(valid_200 > 0, above_200 / valid_200 * 100, np.nan)

    # 6) New 52-week Highs / Lows (rolling window, min 20 days)
    window = min(252, n_days - 1)
    min_lookback = 20
    new_highs = np.full(n_days, np.nan)
    new_lows = np.full(n_days, np.nan)
    for i in range(min_lookback, n_days):
        lb = min(window, i)
        rolling_max = np.nanmax(close_matrix[i - lb:i + 1, :], axis=0)
        rolling_min = np.nanmin(close_matrix[i - lb:i + 1, :], axis=0)
        new_highs[i] = np.nansum(close_matrix[i, :] >= rolling_max)
        new_lows[i] = np.nansum(close_matrix[i, :] <= rolling_min)

    # 7) High-Low Index: SMA10 of 100 × NH / (NH + NL + 1)
    with np.errstate(invalid="ignore"):
        hl_raw = 100 * new_highs / (new_highs + new_lows + 1)
    hl_raw_clean = np.nan_to_num(hl_raw, nan=50.0)  # neutral=50 for NaN
    high_low_index = _sma(hl_raw_clean, 10)
    # Restore NaN where original data was NaN
    high_low_index[:min_lookback + 9] = np.nan

    # 8) McClellan Oscillator & Summation
    ad_clean = np.nan_to_num(ad_diff)
    ema19 = _ema(ad_clean, 19)
    ema39 = _ema(ad_clean, 39)
    mcclellan_osc = ema19 - ema39
    mcclellan_sum = np.nancumsum(np.nan_to_num(mcclellan_osc))
    # Set initial NaN where ema39 is NaN
    mcclellan_osc[:38] = np.nan
    mcclellan_sum[:38] = np.nan

    # 9) TRIN (Arms Index)
    # TRIN = (A/D) / (AdvVol/DecVol), < 1 = bullish, > 1 = bearish
    adv_volume = np.zeros(n_days)
    dec_volume = np.zeros(n_days)
    for i in range(1, n_days):
        up_mask = daily_change[i, :] > 0
        dn_mask = daily_change[i, :] < 0
        adv_volume[i] = np.nansum(volume_matrix[i, :][up_mask])
        dec_volume[i] = np.nansum(volume_matrix[i, :][dn_mask])

    with np.errstate(divide="ignore", invalid="ignore"):
        vol_ratio = np.where(dec_volume > 0, adv_volume / dec_volume, 1.0)
        trin = np.where(vol_ratio > 0, ad_ratio / vol_ratio, 1.0)
    trin[0] = 1.0  # neutral on day 0 (no prior data)
    trin = np.clip(trin, 0.1, 5.0)  # cap extremes
    trin_10d = _sma(trin, 10)

    # 10) Zweig Breadth Thrust
    # ZBT = EMA10(A / (A + D))
    ad_total = advances + declines
    ad_pct = np.where(ad_total > 0, advances / ad_total, 0.5)
    ad_pct[0] = np.nan
    zbt = _ema(np.nan_to_num(ad_pct), 10)

    # ZBT signal: crosses from <0.40 to >0.615 within 10 days
    zbt_signal = np.zeros(n_days)
    for i in range(10, n_days):
        if not np.isnan(zbt[i]) and zbt[i] > 0.615:
            window_slice = zbt[max(0, i - 10):i]
            if np.any(window_slice[~np.isnan(window_slice)] < 0.40):
                zbt_signal[i] = 1.0

    # ── Helpers ────────────────────────────────────────────

    def _safe_list(arr: np.ndarray) -> list:
        return [None if np.isnan(v) else round(float(v), 4) for v in arr]

    def _last_valid(arr: np.ndarray) -> Optional[float]:
        valid = arr[~np.isnan(arr)]
        return round(float(valid[-1]), 4) if len(valid) > 0 else None

    # ── Regime Classification ─────────────────────────────
    def _classify_regime() -> tuple[str, list[str]]:
        divergences = []
        score = 0.0

        # % above 200MA component (0-40 points)
        last_200 = _last_valid(pct_above_200ma)
        if last_200 is not None:
            if last_200 > 70:
                score += 40
            elif last_200 > 50:
                score += 25
            elif last_200 > 30:
                score += 10

        # A/D trend (0-20 points): compare last vs 20 days ago
        if n_days > 20 and not np.isnan(ad_line[-1]) and not np.isnan(ad_line[-21]):
            if ad_line[-1] > ad_line[-21]:
                score += 20
            elif ad_line[-1] > ad_line[-21] * 0.95:
                score += 10

        # McClellan (0-20 points)
        last_mcc = _last_valid(mcclellan_osc)
        if last_mcc is not None:
            if last_mcc > 50:
                score += 20
            elif last_mcc > 0:
                score += 12
            elif last_mcc > -50:
                score += 5

        # TRIN (0-20 points), inverse: <1 = bullish
        last_trin = _last_valid(trin_10d)
        if last_trin is not None:
            if last_trin < 0.8:
                score += 20
            elif last_trin < 1.0:
                score += 14
            elif last_trin < 1.2:
                score += 7

        # Divergence detection
        if last_200 is not None and last_200 < 40 and score > 50:
            divergences.append("Bearish breadth divergence: price rising but <40% above 200MA")
        if last_mcc is not None and last_mcc < -50 and last_200 is not None and last_200 > 60:
            divergences.append("McClellan divergence: oscillator deeply negative while breadth appears healthy")
        if last_trin is not None and last_trin > 1.5 and score > 40:
            divergences.append("TRIN warning: heavy selling pressure despite positive breadth")

        if score >= 80:
            regime = "strong_bull"
        elif score >= 55:
            regime = "bull"
        elif score >= 35:
            regime = "neutral"
        elif score >= 15:
            regime = "bear"
        else:
            regime = "strong_bear"

        return regime, divergences

    regime, divergences = _classify_regime()

    # ── Build Response ────────────────────────────────────

    return {
        "dates": dates_str,
        "universe_size": n_stocks,
        "indicators": {
            "advances": _safe_list(advances),
            "declines": _safe_list(declines),
            "unchanged": _safe_list(unchanged),
            "ad_line": _safe_list(ad_line),
            "ad_ratio": _safe_list(ad_ratio),
            "pct_above_50ma": _safe_list(pct_above_50ma),
            "pct_above_200ma": _safe_list(pct_above_200ma),
            "new_highs": _safe_list(new_highs),
            "new_lows": _safe_list(new_lows),
            "high_low_index": _safe_list(high_low_index),
            "mcclellan_oscillator": _safe_list(mcclellan_osc),
            "mcclellan_summation": _safe_list(mcclellan_sum),
            "trin": _safe_list(trin),
            "trin_10d_avg": _safe_list(trin_10d),
            "zweig_breadth_thrust": _safe_list(zbt),
            "zbt_signal": _safe_list(zbt_signal),
        },
        "current": {
            "regime": regime,
            "ad_ratio": _last_valid(ad_ratio),
            "pct_above_50ma": _last_valid(pct_above_50ma),
            "pct_above_200ma": _last_valid(pct_above_200ma),
            "mcclellan_oscillator": _last_valid(mcclellan_osc),
            "mcclellan_summation": _last_valid(mcclellan_sum),
            "trin": _last_valid(trin_10d),
            "new_highs": _last_valid(new_highs),
            "new_lows": _last_valid(new_lows),
            "divergences": divergences,
        },
        "success": True,
    }
