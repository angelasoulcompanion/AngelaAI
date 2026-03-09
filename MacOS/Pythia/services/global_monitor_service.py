"""
Pythia — Global Monitor Service
Batch-fetches 15 world indices via yfinance, computes market open/closed status
from exchange hours + timezone, and returns a command-center payload.

Cache: 2-minute in-memory TTL (same pattern as market_breadth_service).
"""
import time
from datetime import datetime, timedelta
from typing import Optional

import pytz
import yfinance as yf

# ── Index Definitions ────────────────────────────────────

INDICES = [
    # Americas
    {"symbol": "^GSPC",    "name": "S&P 500",     "region": "Americas",  "country": "US", "flag": "\U0001f1fa\U0001f1f8"},
    {"symbol": "^DJI",     "name": "Dow Jones",   "region": "Americas",  "country": "US", "flag": "\U0001f1fa\U0001f1f8"},
    {"symbol": "^IXIC",    "name": "NASDAQ",      "region": "Americas",  "country": "US", "flag": "\U0001f1fa\U0001f1f8"},
    {"symbol": "^BVSP",    "name": "Bovespa",     "region": "Americas",  "country": "BR", "flag": "\U0001f1e7\U0001f1f7"},
    # Europe
    {"symbol": "^FTSE",    "name": "FTSE 100",    "region": "Europe",    "country": "GB", "flag": "\U0001f1ec\U0001f1e7"},
    {"symbol": "^GDAXI",   "name": "DAX",         "region": "Europe",    "country": "DE", "flag": "\U0001f1e9\U0001f1ea"},
    {"symbol": "^FCHI",    "name": "CAC 40",      "region": "Europe",    "country": "FR", "flag": "\U0001f1eb\U0001f1f7"},
    # Asia-Pacific
    {"symbol": "^SET.BK",  "name": "SET Index",   "region": "Asia-Pac",  "country": "TH", "flag": "\U0001f1f9\U0001f1ed"},
    {"symbol": "^N225",    "name": "Nikkei 225",  "region": "Asia-Pac",  "country": "JP", "flag": "\U0001f1ef\U0001f1f5"},
    {"symbol": "^HSI",     "name": "Hang Seng",   "region": "Asia-Pac",  "country": "HK", "flag": "\U0001f1ed\U0001f1f0"},
    {"symbol": "^AXJO",    "name": "ASX 200",     "region": "Asia-Pac",  "country": "AU", "flag": "\U0001f1e6\U0001f1fa"},
    {"symbol": "^KS11",    "name": "KOSPI",       "region": "Asia-Pac",  "country": "KR", "flag": "\U0001f1f0\U0001f1f7"},
    {"symbol": "000001.SS","name": "Shanghai",    "region": "Asia-Pac",  "country": "CN", "flag": "\U0001f1e8\U0001f1f3"},
    # Global indicators
    {"symbol": "^VIX",     "name": "VIX",         "region": "Global",    "country": "GL", "flag": "\U0001f310"},
    {"symbol": "DX-Y.NYB", "name": "DXY",         "region": "Global",    "country": "GL", "flag": "\U0001f4b5"},
]

# Exchange hours: (open_hour, open_min, close_hour, close_min, timezone, exchange_name)
EXCHANGE_HOURS: dict[str, tuple[int, int, int, int, str, str]] = {
    "^GSPC":     (9, 30, 16, 0, "America/New_York",    "NYSE"),
    "^DJI":      (9, 30, 16, 0, "America/New_York",    "NYSE"),
    "^IXIC":     (9, 30, 16, 0, "America/New_York",    "NASDAQ"),
    "^BVSP":     (10, 0, 17, 0, "America/Sao_Paulo",   "B3"),
    "^FTSE":     (8, 0,  16, 30, "Europe/London",      "LSE"),
    "^GDAXI":    (9, 0,  17, 30, "Europe/Berlin",      "XETRA"),
    "^FCHI":     (9, 0,  17, 30, "Europe/Paris",       "Euronext"),
    "^SET.BK":   (10, 0, 16, 30, "Asia/Bangkok",       "SET"),
    "^N225":     (9, 0,  15, 0,  "Asia/Tokyo",         "TSE"),
    "^HSI":      (9, 30, 16, 0,  "Asia/Hong_Kong",     "HKEX"),
    "^AXJO":     (10, 0, 16, 0,  "Australia/Sydney",   "ASX"),
    "^KS11":     (9, 0,  15, 30, "Asia/Seoul",         "KRX"),
    "000001.SS": (9, 30, 15, 0,  "Asia/Shanghai",      "SSE"),
    "^VIX":      (9, 30, 16, 0,  "America/New_York",   "CBOE"),
    "DX-Y.NYB":  (20, 0, 17, 0,  "America/New_York",   "ICE"),  # nearly 24h
}

# Timeline bars (UTC hours for visualization)
TIMELINE_EXCHANGES = [
    {"name": "NYSE",    "utc_open": 14.5, "utc_close": 21.0},
    {"name": "NASDAQ",  "utc_open": 14.5, "utc_close": 21.0},
    {"name": "LSE",     "utc_open": 8.0,  "utc_close": 16.5},
    {"name": "XETRA",   "utc_open": 8.0,  "utc_close": 16.5},
    {"name": "SET",     "utc_open": 3.0,  "utc_close": 9.5},
    {"name": "TSE",     "utc_open": 0.0,  "utc_close": 6.0},
    {"name": "HKEX",    "utc_open": 1.5,  "utc_close": 8.0},
    {"name": "SSE",     "utc_open": 1.5,  "utc_close": 7.0},
    {"name": "ASX",     "utc_open": 0.0,  "utc_close": 6.0},
    {"name": "KRX",     "utc_open": 0.0,  "utc_close": 6.5},
    {"name": "B3",      "utc_open": 13.0, "utc_close": 20.0},
]

# ── Cache ────────────────────────────────────────────────

_cache: dict[str, tuple[float, dict]] = {}
CACHE_TTL = 120  # 2 minutes


def _get_cached(key: str) -> Optional[dict]:
    if key in _cache:
        ts, data = _cache[key]
        if time.time() - ts < CACHE_TTL:
            return data
    return None


def _set_cached(key: str, data: dict) -> None:
    _cache[key] = (time.time(), data)


# ── Market Status ────────────────────────────────────────

def _is_market_open(symbol: str) -> tuple[bool, str]:
    """Check if exchange is currently open. Returns (is_open, exchange_name)."""
    info = EXCHANGE_HOURS.get(symbol)
    if not info:
        return False, "Unknown"

    oh, om, ch, cm, tz_name, exchange_name = info
    tz = pytz.timezone(tz_name)
    now = datetime.now(tz)

    # Weekend check
    if now.weekday() >= 5:
        return False, exchange_name

    current_minutes = now.hour * 60 + now.minute
    open_minutes = oh * 60 + om
    close_minutes = ch * 60 + cm

    if open_minutes < close_minutes:
        is_open = open_minutes <= current_minutes < close_minutes
    else:
        # Overnight session (e.g. ICE/DXY)
        is_open = current_minutes >= open_minutes or current_minutes < close_minutes

    return is_open, exchange_name


# ── Main Fetch ───────────────────────────────────────────

def fetch_global_monitor() -> dict:
    """Fetch all 15 indices with 5-day sparklines, compute status, build payload."""
    cached = _get_cached("global_monitor")
    if cached:
        return cached

    symbols = [idx["symbol"] for idx in INDICES]

    # Batch download 5-day history for sparklines
    try:
        hist = yf.download(
            symbols,
            period="5d",
            interval="1d",
            group_by="ticker",
            threads=True,
            progress=False,
        )
    except Exception:
        hist = None

    indices_data = []
    region_status: dict[str, dict] = {
        "Americas": {"open_count": 0, "total": 0},
        "Europe":   {"open_count": 0, "total": 0},
        "Asia-Pac": {"open_count": 0, "total": 0},
    }

    for idx_def in INDICES:
        sym = idx_def["symbol"]
        is_open, exchange_name = _is_market_open(sym)

        # Extract price data from batch download
        current_price = None
        previous_close = None
        change = None
        change_percent = None
        sparkline: list[float] = []

        try:
            if hist is not None and not hist.empty:
                if len(symbols) == 1:
                    col = hist
                else:
                    col = hist[sym] if sym in hist.columns.get_level_values(0) else None

                if col is not None and not col.empty:
                    closes = col["Close"].dropna()
                    if len(closes) >= 1:
                        sparkline = [round(float(v), 2) for v in closes.values]
                        current_price = round(float(closes.iloc[-1]), 2)
                    if len(closes) >= 2:
                        previous_close = round(float(closes.iloc[-2]), 2)
                        change = round(current_price - previous_close, 2)
                        change_percent = round((change / previous_close) * 100, 2) if previous_close else None
        except Exception:
            pass

        # Fallback: try single ticker if batch failed
        if current_price is None:
            try:
                ticker = yf.Ticker(sym)
                fast_info = ticker.fast_info
                current_price = round(float(fast_info.get("lastPrice", 0) or fast_info.get("regularMarketPrice", 0)), 2)
                previous_close = round(float(fast_info.get("previousClose", 0) or fast_info.get("regularMarketPreviousClose", 0)), 2)
                if current_price and previous_close:
                    change = round(current_price - previous_close, 2)
                    change_percent = round((change / previous_close) * 100, 2) if previous_close else None
            except Exception:
                pass

        entry = {
            "symbol": sym,
            "name": idx_def["name"],
            "region": idx_def["region"],
            "country": idx_def["country"],
            "flag": idx_def["flag"],
            "exchange": exchange_name,
            "is_open": is_open,
            "current_price": current_price,
            "previous_close": previous_close,
            "change": change,
            "change_percent": change_percent,
            "sparkline": sparkline,
        }
        indices_data.append(entry)

        # Track region open counts (skip Global)
        if idx_def["region"] in region_status:
            region_status[idx_def["region"]]["total"] += 1
            if is_open:
                region_status[idx_def["region"]]["open_count"] += 1

    # Compute summary KPIs
    vix_entry = next((i for i in indices_data if i["symbol"] == "^VIX"), None)
    dxy_entry = next((i for i in indices_data if i["symbol"] == "DX-Y.NYB"), None)
    open_count = sum(1 for i in indices_data if i["is_open"] and i["region"] != "Global")
    total_markets = sum(1 for i in indices_data if i["region"] != "Global")

    # Sentiment: count positive vs negative among non-global indices
    positive = sum(1 for i in indices_data if i["region"] != "Global" and (i["change_percent"] or 0) > 0)
    negative = sum(1 for i in indices_data if i["region"] != "Global" and (i["change_percent"] or 0) < 0)
    with_data = positive + negative
    sentiment = "Bullish" if positive > negative else "Bearish" if negative > positive else "Neutral"

    utc_now = datetime.utcnow()

    payload = {
        "success": True,
        "fetched_at": utc_now.isoformat() + "Z",
        "utc_time": utc_now.strftime("%H:%M:%S"),
        "summary": {
            "markets_open": open_count,
            "markets_total": total_markets,
            "vix": vix_entry["current_price"] if vix_entry else None,
            "vix_change": vix_entry["change_percent"] if vix_entry else None,
            "dxy": dxy_entry["current_price"] if dxy_entry else None,
            "dxy_change": dxy_entry["change_percent"] if dxy_entry else None,
            "sentiment": sentiment,
            "sentiment_detail": f"{positive}/{with_data}",
        },
        "pulse_bar": [
            {
                "exchange": EXCHANGE_HOURS[idx["symbol"]][5],
                "is_open": idx["is_open"],
            }
            for idx in indices_data
            if idx["symbol"] in EXCHANGE_HOURS and idx["region"] != "Global"
        ],
        "regions": {
            region: {
                "is_open": region_status.get(region, {}).get("open_count", 0) > 0,
                "open_count": region_status.get(region, {}).get("open_count", 0),
                "indices": [i for i in indices_data if i["region"] == region],
            }
            for region in ["Americas", "Europe", "Asia-Pac"]
        },
        "heatmap": [
            {
                "symbol": i["symbol"],
                "name": i["name"],
                "change_percent": i["change_percent"],
                "flag": i["flag"],
            }
            for i in indices_data
            if i["region"] != "Global"
        ],
        "timeline": TIMELINE_EXCHANGES,
        "global_indicators": [i for i in indices_data if i["region"] == "Global"],
    }

    _set_cached("global_monitor", payload)
    return payload
