"""
Pythia — Global Monitor Service
Batch-fetches 15 world indices + cross-asset + FX + futures + risk data
via yfinance, computes market open/closed status from exchange hours + timezone,
and returns a Bloomberg-style command-center payload.

Cache: 2-minute in-memory TTL (same pattern as market_breadth_service).
"""
import calendar
import logging
import time
from datetime import datetime, timedelta
from typing import Optional

import pytz
import yfinance as yf

logger = logging.getLogger(__name__)

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
    {"symbol": "399001.SZ","name": "Shenzhen",   "region": "Asia-Pac",  "country": "CN", "flag": "\U0001f1e8\U0001f1f3"},
    # Global indicators
    {"symbol": "^VIX",     "name": "VIX",         "region": "Global",    "country": "GL", "flag": "\U0001f310"},
    {"symbol": "DX-Y.NYB", "name": "DXY",         "region": "Global",    "country": "GL", "flag": "\U0001f4b5"},
]

# ── Cross-Asset Definitions ──────────────────────────────

CROSS_ASSET_DEFS = [
    {"symbol": "GC=F",    "name": "Gold",      "unit": "USD/oz"},
    {"symbol": "CL=F",    "name": "Crude Oil",  "unit": "USD/bbl"},
    {"symbol": "^TNX",    "name": "10Y Yield",  "unit": "%"},
    {"symbol": "BTC-USD", "name": "Bitcoin",    "unit": "USD"},
    {"symbol": "HG=F",    "name": "Copper",     "unit": "USD/lb"},
]

# ── FX Pairs ─────────────────────────────────────────────

FX_DEFS = [
    {"symbol": "EURUSD=X", "name": "EUR/USD"},
    {"symbol": "JPY=X",    "name": "USD/JPY"},
    {"symbol": "GBPUSD=X", "name": "GBP/USD"},
    {"symbol": "CNY=X",    "name": "USD/CNY"},
    {"symbol": "THB=X",    "name": "USD/THB"},
    {"symbol": "AUDUSD=X", "name": "AUD/USD"},
]

# ── Futures → Index Mapping ──────────────────────────────

FUTURES_MAP = {
    "^GSPC": {"future": "ES=F",  "name": "S&P Futures"},
    "^DJI":  {"future": "YM=F",  "name": "Dow Futures"},
    "^IXIC": {"future": "NQ=F",  "name": "NASDAQ Futures"},
    "^N225": {"future": "NKD=F", "name": "Nikkei Futures"},
}

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
    "399001.SZ": (9, 30, 15, 0,  "Asia/Shanghai",      "SZSE"),
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

    # ── Fetch extra data (cross-asset, FX, futures, risk) ──
    extra = _fetch_extra_data()

    # ── Attach futures hints to closed indices ──
    futures_data = extra.get("futures_raw", {})
    for idx in indices_data:
        fm = FUTURES_MAP.get(idx["symbol"])
        if fm and not idx["is_open"] and fm["future"] in futures_data:
            fd = futures_data[fm["future"]]
            idx["futures_hint"] = {
                "name": fm["name"],
                "price": fd.get("price"),
                "change_percent": fd.get("change_percent"),
            }
        else:
            idx["futures_hint"] = None

    # ── Performance ranking (sort non-global by change%) ──
    ranked = sorted(
        [i for i in indices_data if i["region"] != "Global" and i["change_percent"] is not None],
        key=lambda x: x["change_percent"],
        reverse=True,
    )
    performance_ranking = [
        {
            "name": i["name"],
            "flag": i["flag"],
            "change_percent": i["change_percent"],
        }
        for i in ranked
    ]

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
        "headlines": _fetch_headlines(),
        # ── New sections ──
        "cross_asset": extra.get("cross_asset", []),
        "fx_pairs": extra.get("fx_pairs", []),
        "yield_curve": extra.get("yield_curve", {}),
        "risk_regime": extra.get("risk_regime", {}),
        "performance_ranking": performance_ranking,
        "economic_calendar": _build_economic_calendar(),
    }

    _set_cached("global_monitor", payload)
    return payload


def _fetch_headlines(max_items: int = 8) -> list[dict]:
    """Fetch market news headlines from yfinance (S&P 500 ticker news)."""
    try:
        ticker = yf.Ticker("^GSPC")
        news = ticker.news
        if not news:
            return []

        items = []
        for article in news[:max_items]:
            content = article.get("content", {})
            if not content:
                continue
            title = content.get("title", "")
            provider = content.get("provider", {}).get("displayName", "")
            pub_date = content.get("pubDate", "")
            url = content.get("canonicalUrl", {}).get("url", "")

            if title:
                items.append({
                    "title": title,
                    "source": provider,
                    "published": pub_date,
                    "url": url,
                })
        return items
    except Exception:
        return []


# ── Extra Data Fetch (Cross-Asset, FX, Futures, Risk) ────

def _fetch_extra_data() -> dict:
    """Batch fetch cross-asset, FX, futures, yield curve, risk data."""
    extra_symbols = (
        ["GC=F", "CL=F", "BTC-USD", "HG=F"]          # cross-asset (^TNX in main)
        + ["^IRX", "^FVX", "^TYX"]                     # yield curve
        + ["ES=F", "NQ=F", "YM=F", "NKD=F"]            # futures
        + ["EURUSD=X", "JPY=X", "GBPUSD=X", "CNY=X", "THB=X", "AUDUSD=X"]  # FX
        + ["^VIX3M", "HYG", "IEF"]                     # risk composite
    )

    prices: dict[str, dict] = {}  # symbol → {price, prev, change, change_percent}

    try:
        hist = yf.download(
            extra_symbols,
            period="5d",
            interval="1d",
            group_by="ticker",
            threads=True,
            progress=False,
        )

        for sym in extra_symbols:
            try:
                col = hist[sym] if sym in hist.columns.get_level_values(0) else None
                if col is not None and not col.empty:
                    closes = col["Close"].dropna()
                    if len(closes) >= 1:
                        price = round(float(closes.iloc[-1]), 4)
                        prev = round(float(closes.iloc[-2]), 4) if len(closes) >= 2 else None
                        chg = round(price - prev, 4) if prev else None
                        chg_pct = round((chg / prev) * 100, 2) if prev and prev != 0 else None
                        prices[sym] = {
                            "price": price,
                            "previous": prev,
                            "change": chg,
                            "change_percent": chg_pct,
                        }
            except Exception:
                pass
    except Exception as e:
        logger.warning(f"Extra data batch download failed: {e}")

    # Also grab ^TNX and ^VIX from main cache if available (already fetched)
    cached_main = _get_cached("global_monitor")
    tnx_price = None
    vix_price = None
    if cached_main:
        for gi in cached_main.get("global_indicators", []):
            if gi["symbol"] == "^TNX":
                tnx_price = gi.get("current_price")
            if gi["symbol"] == "^VIX":
                vix_price = gi.get("current_price")

    # If ^TNX not in cache, try from extra download (it's in CROSS_ASSET_DEFS)
    if tnx_price is None and "^TNX" not in prices:
        try:
            t = yf.Ticker("^TNX")
            tnx_price = round(float(t.fast_info.get("lastPrice", 0)), 2)
        except Exception:
            pass

    # ── Build cross-asset ──
    cross_asset = []
    for ca in CROSS_ASSET_DEFS:
        sym = ca["symbol"]
        if sym == "^TNX":
            # Use main index data or fallback
            p = prices.get(sym, {})
            cross_asset.append({
                "name": ca["name"],
                "unit": ca["unit"],
                "price": tnx_price or p.get("price"),
                "change_percent": p.get("change_percent"),
            })
        elif sym in prices:
            p = prices[sym]
            cross_asset.append({
                "name": ca["name"],
                "unit": ca["unit"],
                "price": p["price"],
                "change_percent": p.get("change_percent"),
            })
        else:
            cross_asset.append({"name": ca["name"], "unit": ca["unit"], "price": None, "change_percent": None})

    # ── Build FX pairs ──
    fx_pairs = []
    for fx in FX_DEFS:
        sym = fx["symbol"]
        if sym in prices:
            p = prices[sym]
            fx_pairs.append({
                "name": fx["name"],
                "rate": p["price"],
                "change_percent": p.get("change_percent"),
            })
        else:
            fx_pairs.append({"name": fx["name"], "rate": None, "change_percent": None})

    # ── Build futures raw data ──
    futures_raw = {}
    for idx_sym, fm in FUTURES_MAP.items():
        fsym = fm["future"]
        if fsym in prices:
            futures_raw[fsym] = prices[fsym]

    # ── Build yield curve ──
    tnx_val = tnx_price  # 10Y
    irx_val = prices.get("^IRX", {}).get("price")  # 13-week T-bill
    fvx_val = prices.get("^FVX", {}).get("price")  # 5Y
    tyx_val = prices.get("^TYX", {}).get("price")  # 30Y

    spread_10y_3m = round(tnx_val - irx_val, 2) if tnx_val and irx_val else None
    if spread_10y_3m is not None:
        if spread_10y_3m < -0.1:
            curve_status = "Inverted"
        elif spread_10y_3m < 0.2:
            curve_status = "Flat"
        else:
            curve_status = "Normal"
    else:
        curve_status = "Unknown"

    yield_curve = {
        "t_3m": round(irx_val, 2) if irx_val else None,
        "t_5y": round(fvx_val, 2) if fvx_val else None,
        "t_10y": round(tnx_val, 2) if tnx_val else None,
        "t_30y": round(tyx_val, 2) if tyx_val else None,
        "spread_10y_3m": spread_10y_3m,
        "status": curve_status,
    }

    # ── Build risk regime ──
    vix3m = prices.get("^VIX3M", {}).get("price")
    hyg_price = prices.get("HYG", {}).get("price")
    ief_price = prices.get("IEF", {}).get("price")
    hyg_chg = prices.get("HYG", {}).get("change_percent")

    # VIX term structure: contango (normal) if VIX < VIX3M
    vix_term = None
    if vix_price and vix3m:
        vix_term = "Contango" if vix_price < vix3m else "Backwardation"

    # Credit spread proxy: HYG/IEF ratio
    credit_ratio = round(hyg_price / ief_price, 4) if hyg_price and ief_price else None

    # Composite regime score: 0-100 (higher = more risk-on)
    score = 50  # neutral baseline
    if vix_price:
        if vix_price < 15:
            score += 20
        elif vix_price < 20:
            score += 10
        elif vix_price > 30:
            score -= 25
        elif vix_price > 25:
            score -= 15
    if vix_term == "Contango":
        score += 10
    elif vix_term == "Backwardation":
        score -= 15
    if hyg_chg:
        if hyg_chg > 0:
            score += 5
        elif hyg_chg < -0.5:
            score -= 10

    score = max(0, min(100, score))
    if score >= 65:
        regime = "Risk-On"
    elif score <= 35:
        regime = "Risk-Off"
    else:
        regime = "Neutral"

    risk_regime = {
        "regime": regime,
        "score": score,
        "vix": vix_price,
        "vix_3m": round(vix3m, 1) if vix3m else None,
        "vix_term_structure": vix_term,
        "hyg_change": hyg_chg,
        "credit_ratio": credit_ratio,
    }

    return {
        "cross_asset": cross_asset,
        "fx_pairs": fx_pairs,
        "futures_raw": futures_raw,
        "yield_curve": yield_curve,
        "risk_regime": risk_regime,
    }


# ── Economic Calendar ────────────────────────────────────

def _build_economic_calendar(max_items: int = 5) -> list[dict]:
    """Build upcoming high-impact economic events."""
    now = datetime.utcnow()
    events = []

    # FOMC meeting dates 2026 (approximate, 2-day meetings ending on these dates)
    fomc_dates = [
        (2026, 1, 28), (2026, 3, 18), (2026, 5, 6), (2026, 6, 17),
        (2026, 7, 29), (2026, 9, 16), (2026, 11, 4), (2026, 12, 16),
    ]
    for y, m, d in fomc_dates:
        dt = datetime(y, m, d, 18, 0)  # 2PM ET = 18:00 UTC
        if dt > now:
            events.append({
                "event": "FOMC Rate Decision",
                "country": "US",
                "flag": "\U0001f1fa\U0001f1f8",
                "datetime": dt.isoformat() + "Z",
                "impact": "high",
            })

    # US CPI: ~13th of each month
    for month_offset in range(6):
        m = now.month + month_offset
        y = now.year + (m - 1) // 12
        m = ((m - 1) % 12) + 1
        cpi_day = 13
        if cpi_day > calendar.monthrange(y, m)[1]:
            cpi_day = calendar.monthrange(y, m)[1]
        dt = datetime(y, m, cpi_day, 12, 30)  # 8:30 AM ET = 12:30 UTC
        if dt > now:
            events.append({
                "event": "US CPI",
                "country": "US",
                "flag": "\U0001f1fa\U0001f1f8",
                "datetime": dt.isoformat() + "Z",
                "impact": "high",
            })

    # NFP: first Friday of each month
    for month_offset in range(6):
        m = now.month + month_offset
        y = now.year + (m - 1) // 12
        m = ((m - 1) % 12) + 1
        first_day_weekday = calendar.monthrange(y, m)[0]  # 0=Mon
        first_friday = (4 - first_day_weekday) % 7 + 1
        dt = datetime(y, m, first_friday, 12, 30)
        if dt > now:
            events.append({
                "event": "US Non-Farm Payrolls",
                "country": "US",
                "flag": "\U0001f1fa\U0001f1f8",
                "datetime": dt.isoformat() + "Z",
                "impact": "high",
            })

    # ECB meetings 2026
    ecb_dates = [
        (2026, 1, 22), (2026, 3, 5), (2026, 4, 16), (2026, 6, 4),
        (2026, 7, 16), (2026, 9, 10), (2026, 10, 29), (2026, 12, 10),
    ]
    for y, m, d in ecb_dates:
        dt = datetime(y, m, d, 12, 15)
        if dt > now:
            events.append({
                "event": "ECB Rate Decision",
                "country": "EU",
                "flag": "\U0001f1ea\U0001f1fa",
                "datetime": dt.isoformat() + "Z",
                "impact": "high",
            })

    # BoJ meetings 2026
    boj_dates = [
        (2026, 1, 24), (2026, 3, 13), (2026, 4, 28), (2026, 6, 17),
        (2026, 7, 31), (2026, 9, 17), (2026, 10, 30), (2026, 12, 18),
    ]
    for y, m, d in boj_dates:
        dt = datetime(y, m, d, 3, 0)  # morning JST = 03:00 UTC
        if dt > now:
            events.append({
                "event": "BoJ Rate Decision",
                "country": "JP",
                "flag": "\U0001f1ef\U0001f1f5",
                "datetime": dt.isoformat() + "Z",
                "impact": "medium",
            })

    # Sort by datetime, return next N
    events.sort(key=lambda e: e["datetime"])
    for ev in events:
        ev_dt = datetime.fromisoformat(ev["datetime"].replace("Z", ""))
        diff = ev_dt - now
        days = diff.days
        hours = diff.seconds // 3600
        if days > 0:
            ev["countdown"] = f"in {days}d {hours}h"
        elif hours > 0:
            ev["countdown"] = f"in {hours}h"
        else:
            ev["countdown"] = "< 1h"

    return events[:max_items]
