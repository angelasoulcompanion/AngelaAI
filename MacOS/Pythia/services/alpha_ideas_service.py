"""
Pythia — Alpha Ideas Service (Factor Research Scanner)
Scans Thai or US stocks and ranks by 7 academic alpha factors:
  1. BAB (Betting Against Beta)
  2. Value (HML — Book/Price)
  3. Size (SMB — Small minus Big)
  4. Short-term Reversal (1-week)
  5. Momentum (6-12 month, skip last month)
  6. Long-term Reversal (3-year)
  7. BAV (Betting Against Volatility / Lottery)
Supports market='TH' (Thai stocks from assets table)
         market='US' (US stocks from us_stock_universe table → auto-inserts into assets)
"""
import asyncio
import time
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

import asyncpg
import numpy as np

from helpers.financial_utils import get_yahoo_symbol

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False

# ── Module-level cache for yfinance .info ────────────────
_INFO_CACHE: dict[str, tuple[float, dict]] = {}
_INFO_CACHE_TTL = 3600  # 1 hour


# ── Dataclasses ──────────────────────────────────────────

@dataclass
class AlphaIdeaStock:
    asset_id: str
    symbol: str
    name: str
    sector: str
    price: float
    bab_score: Optional[float] = None
    value_score: Optional[float] = None
    size_score: Optional[float] = None
    str_score: Optional[float] = None
    mom_score: Optional[float] = None
    ltr_score: Optional[float] = None
    bav_score: Optional[float] = None
    composite_score: float = 0.0
    beta: Optional[float] = None
    pb_ratio: Optional[float] = None
    market_cap: Optional[float] = None
    return_1w: Optional[float] = None
    return_6m: Optional[float] = None
    return_12m: Optional[float] = None
    return_3y: Optional[float] = None
    annual_vol: Optional[float] = None


@dataclass
class AlphaIdea:
    idea_id: str
    name: str
    description: str
    long_rationale: str
    short_rationale: str
    long_candidates: list[dict] = field(default_factory=list)
    short_candidates: list[dict] = field(default_factory=list)


@dataclass
class AlphaIdeasResult:
    ideas: list[AlphaIdea] = field(default_factory=list)
    composite_ranking: list[dict] = field(default_factory=list)
    total_stocks_scanned: int = 0
    scan_time_seconds: float = 0.0
    success: bool = True
    message: str = ""


# ── Idea Definitions ─────────────────────────────────────

IDEA_DEFS = [
    {
        "idea_id": "bab",
        "name": "Betting Against Beta",
        "description": "หุ้นที่มี Beta ต่ำมักสร้างผลตอบแทนส่วนเกินได้ดีกว่า ในขณะที่หุ้น Beta สูงกลับ underperform — ขัดกับ CAPM",
        "long_rationale": "Long หุ้น Low Beta — ผลตอบแทนต่อหน่วยความเสี่ยงดีกว่า",
        "short_rationale": "Short หุ้น High Beta — overpriced จาก leverage constraint",
        "score_field": "bab_score",
    },
    {
        "idea_id": "value",
        "name": "Value (HML)",
        "description": "หุ้นที่มีราคาต่ำเมื่อเทียบกับมูลค่าทางบัญชี (High Book/Price) มักถูกกดราคาเกินจริง เมื่อ risk คลี่คลายจะ outperform",
        "long_rationale": "Long หุ้น High B/P (Low P/B) — undervalued relative to book",
        "short_rationale": "Short หุ้น Low B/P (High P/B) — overvalued, glamour stocks",
        "score_field": "value_score",
    },
    {
        "idea_id": "size",
        "name": "Size (SMB)",
        "description": "หุ้นขนาดเล็กมีสภาพคล่องต่ำและถูกติดตามน้อย เกิด inefficiency ในการกำหนดราคา premium จาก liquidity + information gap",
        "long_rationale": "Long หุ้น Small Cap — information premium + liquidity premium",
        "short_rationale": "Short หุ้น Large Cap — fully priced, no information edge",
        "score_field": "size_score",
    },
    {
        "idea_id": "str",
        "name": "Short-term Reversal",
        "description": "ในระยะสั้น (1 สัปดาห์) หุ้นที่ตกแรงมักเด้งกลับจาก microstructure effects เช่น bid-ask bounce, overreaction",
        "long_rationale": "Long หุ้นที่ตกหนักในสัปดาห์ที่ผ่านมา — mean reversion",
        "short_rationale": "Short หุ้นที่ขึ้นแรงในสัปดาห์ที่ผ่านมา — overbought snap-back",
        "score_field": "str_score",
    },
    {
        "idea_id": "mom",
        "name": "Momentum (MOM)",
        "description": "ในระยะกลาง (6-12 เดือน) หุ้นที่ขึ้นต่อเนื่องมักขึ้นต่อ จากการตอบสนองที่ล่าช้าของนักลงทุน (underreaction)",
        "long_rationale": "Long หุ้นที่ให้ผลตอบแทนดีใน 2-12 เดือน — momentum continuation",
        "short_rationale": "Short หุ้นที่ให้ผลตอบแทนแย่ใน 2-12 เดือน — continued decline",
        "score_field": "mom_score",
    },
    {
        "idea_id": "ltr",
        "name": "Long-term Reversal",
        "description": "ในระยะยาว (3-5 ปี) หุ้นที่ขึ้นมามากจะปรับตัวกลับตามปัจจัยพื้นฐาน (overreaction → correction)",
        "long_rationale": "Long หุ้นที่ underperform ในระยะยาว 3 ปี — deep value recovery",
        "short_rationale": "Short หุ้นที่ outperform ในระยะยาว 3 ปี — mean reversion to fundamentals",
        "score_field": "ltr_score",
    },
    {
        "idea_id": "bav",
        "name": "Betting Against Volatility",
        "description": "นักลงทุนชอบหุ้น lottery-like (Vol สูง) ทำให้ราคาสูงเกินจริง หุ้น Vol ต่ำกลับให้ risk-adjusted return ที่ดีกว่า",
        "long_rationale": "Long หุ้น Low Volatility — stable, risk-adjusted outperformance",
        "short_rationale": "Short หุ้น High Volatility — lottery premium overpricing",
        "score_field": "bav_score",
    },
]


# ── Main Entry Point ─────────────────────────────────────

async def scan_alpha_ideas(
    conn: asyncpg.Connection,
    top_n: int = 10,
    market: str = "TH",
) -> AlphaIdeasResult:
    """Scan stocks and compute 7 alpha idea factor scores.
    market: 'TH' = Thai stocks, 'US' = US stocks from us_stock_universe.
    """
    t0 = time.time()
    market = market.upper()

    # 1. Get stocks based on market
    if market == "US":
        stocks = await _get_us_stocks(conn)
    else:
        stocks = await _get_all_thai_stocks(conn)

    label = "US" if market == "US" else "Thai"
    if len(stocks) < 5:
        return AlphaIdeasResult(
            success=False, message=f"Only {len(stocks)} {label} stocks found — need at least 5"
        )

    asset_ids = [s["asset_id"] for s in stocks]

    # 2. Batch fetch prices + market proxy (sequential — asyncpg single conn)
    prices_map = await _batch_fetch_prices(conn, asset_ids, days=1300)
    mkt_returns = await _get_market_returns(conn, days=1300, market=market)

    # 3. Fetch fundamentals from yfinance (P/B, market cap)
    symbols_map = {s["symbol"]: s["exchange"] for s in stocks}
    fundamentals = await _batch_fetch_fundamentals(symbols_map)

    # 4. Compute raw metrics per stock
    scored = []
    for stock in stocks:
        aid = stock["asset_id"]
        sym = stock["symbol"]
        prices = prices_map.get(aid, [])

        if len(prices) < 60:
            continue

        closes = np.array([float(p["close_price"]) for p in prices])
        current_price = float(closes[-1])

        info = fundamentals.get(sym, {})
        raw = _compute_raw_metrics(closes, mkt_returns, info)

        s = AlphaIdeaStock(
            asset_id=str(aid),
            symbol=sym,
            name=stock.get("name", sym),
            sector=stock.get("sector", ""),
            price=current_price,
            beta=raw.get("beta"),
            pb_ratio=raw.get("pb_ratio"),
            market_cap=raw.get("market_cap"),
            return_1w=raw.get("return_1w"),
            return_6m=raw.get("return_6m"),
            return_12m=raw.get("return_12m"),
            return_3y=raw.get("return_3y"),
            annual_vol=raw.get("annual_vol"),
        )
        s._raw = raw  # stash for z-score computation
        scored.append(s)

    if len(scored) < 3:
        return AlphaIdeasResult(
            success=False,
            message=f"Only {len(scored)} stocks with sufficient price data",
        )

    # 5. Cross-sectional z-scores
    _apply_z_scores(scored)

    # 6. Composite score
    for s in scored:
        scores = [
            v for v in [
                s.bab_score, s.value_score, s.size_score,
                s.str_score, s.mom_score, s.ltr_score, s.bav_score,
            ] if v is not None
        ]
        s.composite_score = float(np.mean(scores)) if scores else 0.0

    # 7. Build ideas
    scored.sort(key=lambda x: x.composite_score, reverse=True)
    ideas = _build_ideas(scored, top_n)
    composite_ranking = [_stock_to_dict(s) for s in scored[:top_n * 3]]

    elapsed = round(time.time() - t0, 2)
    return AlphaIdeasResult(
        ideas=ideas,
        composite_ranking=composite_ranking,
        total_stocks_scanned=len(scored),
        scan_time_seconds=elapsed,
        success=True,
        message=f"Scanned {len(scored)} stocks in {elapsed}s",
    )


# ── Data Fetching ────────────────────────────────────────

async def _get_all_thai_stocks(conn: asyncpg.Connection) -> list[dict]:
    rows = await conn.fetch(
        """SELECT asset_id, symbol, name, sector, exchange
           FROM assets
           WHERE is_active = true
             AND (exchange IN ('SET', 'MAI') OR asset_type = 'thai_stock')
           ORDER BY symbol"""
    )
    return [dict(r) for r in rows]


async def _batch_fetch_prices(
    conn: asyncpg.Connection,
    asset_ids: list[UUID],
    days: int = 1300,
) -> dict[UUID, list[dict]]:
    cutoff = date.today() - timedelta(days=days)
    rows = await conn.fetch(
        """SELECT asset_id, date, close_price, volume
           FROM historical_prices
           WHERE asset_id = ANY($1) AND date >= $2
           ORDER BY asset_id, date""",
        asset_ids, cutoff,
    )
    result: dict[UUID, list[dict]] = {}
    for r in rows:
        aid = r["asset_id"]
        if aid not in result:
            result[aid] = []
        result[aid].append(dict(r))
    return result


async def _get_market_returns(
    conn: asyncpg.Connection, days: int, market: str = "TH"
) -> np.ndarray:
    """Get market index daily log returns. TH=SET, US=S&P500."""
    if market == "US":
        candidates = ["^GSPC", "SPY"]
        fallback_yf = "^GSPC"
    else:
        candidates = ["^SET.BK", "^SET"]
        fallback_yf = "^SET.BK"

    for symbol in candidates:
        row = await conn.fetchrow(
            "SELECT asset_id FROM assets WHERE symbol = $1", symbol
        )
        if row:
            rows = await conn.fetch(
                """SELECT close_price FROM historical_prices
                   WHERE asset_id = $1 AND date >= $2
                   ORDER BY date""",
                row["asset_id"], date.today() - timedelta(days=days + 50),
            )
            if len(rows) >= 60:
                prices = np.array([float(r["close_price"]) for r in rows])
                return np.diff(np.log(prices))

    # Fallback: yfinance
    if HAS_YFINANCE:
        try:
            hist = yf.Ticker(fallback_yf).history(period=f"{days}d")
            if len(hist) >= 60:
                return np.diff(np.log(hist["Close"].values))
        except Exception:
            pass
    return np.array([])


async def _get_us_stocks(conn: asyncpg.Connection) -> list[dict]:
    """Get US stocks from us_stock_universe, ensuring they exist in assets table."""
    # Ensure universe is seeded
    count = await conn.fetchval(
        "SELECT count(*) FROM us_stock_universe WHERE is_active = true"
    )
    if count == 0:
        await seed_us_universe(conn)

    # Get universe tickers
    universe = await conn.fetch(
        """SELECT symbol, name, sector, industry, market_cap_group, index_membership
           FROM us_stock_universe WHERE is_active = true ORDER BY symbol"""
    )

    # Ensure each ticker exists in assets table
    for row in universe:
        existing = await conn.fetchrow(
            "SELECT asset_id FROM assets WHERE symbol = $1 AND asset_type = 'us_stock'",
            row["symbol"],
        )
        if not existing:
            await conn.execute(
                """INSERT INTO assets (symbol, name, asset_type, exchange, currency, sector, industry, country, is_active)
                   VALUES ($1, $2, 'us_stock', 'US', 'USD', $3, $4, 'United States', true)
                   ON CONFLICT DO NOTHING""",
                row["symbol"], row["name"] or row["symbol"],
                row["sector"], row["industry"],
            )

    # Now fetch from assets
    rows = await conn.fetch(
        """SELECT a.asset_id, a.symbol, a.name, a.sector, a.exchange
           FROM assets a
           JOIN us_stock_universe u ON u.symbol = a.symbol AND u.is_active = true
           WHERE a.asset_type = 'us_stock' AND a.is_active = true
           ORDER BY a.symbol"""
    )
    return [dict(r) for r in rows]


# ── US Universe Seeding ──────────────────────────────────

SP500_CORE = [
    # Top 50 S&P 500 by market cap + sector diversity
    ("AAPL", "Apple Inc.", "Technology", "Consumer Electronics", "large", "SP500"),
    ("MSFT", "Microsoft Corp.", "Technology", "Software", "large", "SP500"),
    ("AMZN", "Amazon.com Inc.", "Consumer Cyclical", "Internet Retail", "large", "SP500"),
    ("NVDA", "NVIDIA Corp.", "Technology", "Semiconductors", "large", "SP500"),
    ("GOOGL", "Alphabet Inc.", "Communication Services", "Internet Content", "large", "SP500"),
    ("META", "Meta Platforms Inc.", "Communication Services", "Internet Content", "large", "SP500"),
    ("TSLA", "Tesla Inc.", "Consumer Cyclical", "Auto Manufacturers", "large", "SP500"),
    ("BRK-B", "Berkshire Hathaway B", "Financial Services", "Insurance", "large", "SP500"),
    ("JPM", "JPMorgan Chase & Co.", "Financial Services", "Banks", "large", "SP500"),
    ("V", "Visa Inc.", "Financial Services", "Credit Services", "large", "SP500"),
    ("UNH", "UnitedHealth Group", "Healthcare", "Health Care Plans", "large", "SP500"),
    ("JNJ", "Johnson & Johnson", "Healthcare", "Drug Manufacturers", "large", "SP500"),
    ("XOM", "Exxon Mobil Corp.", "Energy", "Oil & Gas", "large", "SP500"),
    ("MA", "Mastercard Inc.", "Financial Services", "Credit Services", "large", "SP500"),
    ("PG", "Procter & Gamble Co.", "Consumer Defensive", "Household Products", "large", "SP500"),
    ("HD", "Home Depot Inc.", "Consumer Cyclical", "Home Improvement", "large", "SP500"),
    ("AVGO", "Broadcom Inc.", "Technology", "Semiconductors", "large", "SP500"),
    ("CVX", "Chevron Corp.", "Energy", "Oil & Gas", "large", "SP500"),
    ("MRK", "Merck & Co. Inc.", "Healthcare", "Drug Manufacturers", "large", "SP500"),
    ("ABBV", "AbbVie Inc.", "Healthcare", "Drug Manufacturers", "large", "SP500"),
    ("COST", "Costco Wholesale", "Consumer Defensive", "Discount Stores", "large", "SP500"),
    ("KO", "Coca-Cola Co.", "Consumer Defensive", "Beverages", "large", "SP500"),
    ("PEP", "PepsiCo Inc.", "Consumer Defensive", "Beverages", "large", "SP500"),
    ("WMT", "Walmart Inc.", "Consumer Defensive", "Discount Stores", "large", "SP500"),
    ("BAC", "Bank of America Corp.", "Financial Services", "Banks", "large", "SP500"),
    ("CRM", "Salesforce Inc.", "Technology", "Software", "large", "SP500"),
    ("TMO", "Thermo Fisher Scientific", "Healthcare", "Diagnostics", "large", "SP500"),
    ("CSCO", "Cisco Systems Inc.", "Technology", "Communication Equipment", "large", "SP500"),
    ("ACN", "Accenture plc", "Technology", "IT Services", "large", "SP500"),
    ("LIN", "Linde plc", "Basic Materials", "Specialty Chemicals", "large", "SP500"),
    ("AMD", "Advanced Micro Devices", "Technology", "Semiconductors", "large", "SP500"),
    ("NFLX", "Netflix Inc.", "Communication Services", "Entertainment", "large", "SP500"),
    ("ORCL", "Oracle Corp.", "Technology", "Software", "large", "SP500"),
    ("ADBE", "Adobe Inc.", "Technology", "Software", "large", "SP500"),
    ("TXN", "Texas Instruments", "Technology", "Semiconductors", "large", "SP500"),
    ("WFC", "Wells Fargo & Co.", "Financial Services", "Banks", "large", "SP500"),
    ("PM", "Philip Morris International", "Consumer Defensive", "Tobacco", "large", "SP500"),
    ("NEE", "NextEra Energy Inc.", "Utilities", "Utilities", "large", "SP500"),
    ("UNP", "Union Pacific Corp.", "Industrials", "Railroads", "large", "SP500"),
    ("RTX", "RTX Corp.", "Industrials", "Aerospace & Defense", "large", "SP500"),
    ("LOW", "Lowe's Companies", "Consumer Cyclical", "Home Improvement", "large", "SP500"),
    ("INTC", "Intel Corp.", "Technology", "Semiconductors", "large", "SP500"),
    ("SPGI", "S&P Global Inc.", "Financial Services", "Financial Data", "large", "SP500"),
    ("HON", "Honeywell International", "Industrials", "Conglomerates", "large", "SP500"),
    ("QCOM", "Qualcomm Inc.", "Technology", "Semiconductors", "large", "SP500"),
    ("CAT", "Caterpillar Inc.", "Industrials", "Farm & Heavy Equipment", "large", "SP500"),
    ("BA", "Boeing Co.", "Industrials", "Aerospace & Defense", "large", "SP500"),
    ("GS", "Goldman Sachs Group", "Financial Services", "Capital Markets", "large", "SP500"),
    ("DE", "Deere & Co.", "Industrials", "Farm & Heavy Equipment", "large", "SP500"),
    ("AMGN", "Amgen Inc.", "Healthcare", "Drug Manufacturers", "large", "SP500"),
]


async def seed_us_universe(conn: asyncpg.Connection) -> int:
    """Seed us_stock_universe table with S&P 500 core tickers. Returns count inserted."""
    inserted = 0
    for sym, name, sector, industry, cap_group, index_mem in SP500_CORE:
        result = await conn.execute(
            """INSERT INTO us_stock_universe (symbol, name, sector, industry, market_cap_group, index_membership)
               VALUES ($1, $2, $3, $4, $5, $6)
               ON CONFLICT (symbol) DO NOTHING""",
            sym, name, sector, industry, cap_group, index_mem,
        )
        if "INSERT" in result:
            inserted += 1
    return inserted


async def _batch_fetch_fundamentals(
    symbols_map: dict[str, str],
) -> dict[str, dict]:
    """Fetch P/B and market_cap from yfinance .info for all symbols."""
    if not HAS_YFINANCE:
        return {}

    now = time.time()
    results: dict[str, dict] = {}
    to_fetch: list[tuple[str, str]] = []

    for sym, exchange in symbols_map.items():
        cached = _INFO_CACHE.get(sym)
        if cached and (now - cached[0]) < _INFO_CACHE_TTL:
            results[sym] = cached[1]
        else:
            to_fetch.append((sym, exchange))

    if not to_fetch:
        return results

    sem = asyncio.Semaphore(10)

    async def _fetch_one(sym: str, exchange: str) -> tuple[str, dict]:
        async with sem:
            try:
                yahoo_sym = get_yahoo_symbol(sym, exchange)
                info = await asyncio.to_thread(
                    lambda: yf.Ticker(yahoo_sym).info
                )
                extracted = {
                    "pb_ratio": info.get("priceToBook"),
                    "market_cap": info.get("marketCap"),
                }
                _INFO_CACHE[sym] = (time.time(), extracted)
                return sym, extracted
            except Exception:
                return sym, {}

    tasks = [_fetch_one(s, e) for s, e in to_fetch]
    fetched = await asyncio.gather(*tasks, return_exceptions=True)
    for item in fetched:
        if isinstance(item, tuple):
            results[item[0]] = item[1]

    return results


# ── Factor Computation ───────────────────────────────────

def _compute_raw_metrics(
    closes: np.ndarray,
    mkt_returns: np.ndarray,
    info: dict,
) -> dict:
    """Compute raw factor metrics for a single stock."""
    n = len(closes)
    log_returns = np.diff(np.log(closes))
    raw: dict = {}

    # Beta (252-day window)
    if len(log_returns) >= 252 and len(mkt_returns) >= 252:
        sr = log_returns[-252:]
        mr = mkt_returns[-252:]
        min_len = min(len(sr), len(mr))
        sr, mr = sr[-min_len:], mr[-min_len:]
        cov = np.cov(sr, mr)
        if cov[1, 1] > 1e-12:
            raw["beta"] = float(cov[0, 1] / cov[1, 1])

    # Value: P/B from yfinance
    pb = info.get("pb_ratio")
    if pb and pb > 0:
        raw["pb_ratio"] = float(pb)
        raw["bp_ratio"] = 1.0 / float(pb)  # Book/Price for scoring

    # Size: market cap from yfinance
    mc = info.get("market_cap")
    if mc and mc > 0:
        raw["market_cap"] = float(mc)

    # Short-term return (5 trading days)
    if n > 5:
        raw["return_1w"] = float(np.log(closes[-1] / closes[-6]))

    # Medium-term momentum (skip last 21 days, use 2-12 months)
    if n > 252:
        raw["return_6m"] = float(np.log(closes[-22] / closes[-126])) if n > 126 else None
        raw["return_12m"] = float(np.log(closes[-22] / closes[-252]))
    elif n > 126:
        raw["return_6m"] = float(np.log(closes[-22] / closes[-126])) if n > 22 else None

    # Momentum score: use 2-12m return (skip last month)
    if n > 252:
        raw["mom_return"] = float(np.log(closes[-22] / closes[-252]))
    elif n > 126:
        raw["mom_return"] = float(np.log(closes[-22] / closes[-126])) if n > 22 else None

    # Long-term return (3 years ~756 days)
    if n > 756:
        raw["return_3y"] = float(np.log(closes[-1] / closes[-756]))

    # Annual volatility (252-day)
    if len(log_returns) >= 252:
        raw["annual_vol"] = float(np.std(log_returns[-252:]) * np.sqrt(252))
    elif len(log_returns) >= 60:
        raw["annual_vol"] = float(np.std(log_returns[-60:]) * np.sqrt(252))

    return raw


def _apply_z_scores(stocks: list[AlphaIdeaStock]) -> None:
    """Compute cross-sectional z-scores for each factor and assign to stocks."""
    factor_map = [
        ("beta", "bab_score", True),          # negate: low beta = high score
        ("bp_ratio", "value_score", False),    # high B/P = high score
        ("market_cap", "size_score", True),    # negate: small cap = high score
        ("return_1w", "str_score", True),      # negate: recent loser = high score
        ("mom_return", "mom_score", False),     # high momentum = high score
        ("return_3y", "ltr_score", True),      # negate: long-term loser = high score
        ("annual_vol", "bav_score", True),     # negate: low vol = high score
    ]

    for raw_key, score_attr, negate in factor_map:
        values = []
        indices = []
        for i, s in enumerate(stocks):
            v = getattr(s, '_raw', {}).get(raw_key)
            if v is not None and np.isfinite(v):
                values.append(v)
                indices.append(i)

        if len(values) < 3:
            continue

        arr = np.array(values)
        mean = np.mean(arr)
        std = np.std(arr)
        if std < 1e-12:
            continue

        z_scores = (arr - mean) / std
        if negate:
            z_scores = -z_scores

        for j, idx in enumerate(indices):
            setattr(stocks[idx], score_attr, round(float(z_scores[j]), 4))


# ── Build Ideas ──────────────────────────────────────────

def _build_ideas(
    scored_stocks: list[AlphaIdeaStock],
    top_n: int,
) -> list[AlphaIdea]:
    ideas = []
    for defn in IDEA_DEFS:
        score_field = defn["score_field"]
        candidates = [
            s for s in scored_stocks
            if getattr(s, score_field) is not None
        ]
        candidates.sort(key=lambda s: getattr(s, score_field), reverse=True)

        long_list = [_stock_to_dict(s) for s in candidates[:top_n]]
        short_list = [_stock_to_dict(s) for s in candidates[-top_n:]][::-1]

        ideas.append(AlphaIdea(
            idea_id=defn["idea_id"],
            name=defn["name"],
            description=defn["description"],
            long_rationale=defn["long_rationale"],
            short_rationale=defn["short_rationale"],
            long_candidates=long_list,
            short_candidates=short_list,
        ))

    return ideas


def _stock_to_dict(s: AlphaIdeaStock) -> dict:
    return {
        "asset_id": s.asset_id,
        "symbol": s.symbol,
        "name": s.name,
        "sector": s.sector,
        "price": round(s.price, 2),
        "bab_score": s.bab_score,
        "value_score": s.value_score,
        "size_score": s.size_score,
        "str_score": s.str_score,
        "mom_score": s.mom_score,
        "ltr_score": s.ltr_score,
        "bav_score": s.bav_score,
        "composite_score": round(s.composite_score, 4),
        "beta": _round_opt(s.beta, 3),
        "pb_ratio": _round_opt(s.pb_ratio, 2),
        "market_cap": s.market_cap,
        "return_1w": _round_opt(s.return_1w, 4),
        "return_6m": _round_opt(s.return_6m, 4),
        "return_12m": _round_opt(s.return_12m, 4),
        "return_3y": _round_opt(s.return_3y, 4),
        "annual_vol": _round_opt(s.annual_vol, 4),
    }


def _round_opt(v: Optional[float], digits: int) -> Optional[float]:
    return round(v, digits) if v is not None else None
