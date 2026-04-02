"""
Pythia — Market Regime Detection Service
4-state Gaussian HMM: bull, bear, sideways, crisis
"""
import json
import time
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

import asyncpg
import numpy as np

from config import PythiaConfig

try:
    from hmmlearn.hmm import GaussianHMM
    HAS_HMM = True
except ImportError:
    HAS_HMM = False

# Regime labels by volatility/return characteristics
REGIME_LABELS = {0: "bull", 1: "sideways", 2: "bear", 3: "crisis"}


@dataclass
class RegimeResult:
    symbol: str
    regime: str              # bull, bear, sideways, crisis
    probability: float       # confidence in current state
    all_probabilities: dict[str, float] = field(default_factory=dict)
    volatility: float = 0.0
    trend_strength: float = 0.0  # -1 to 1
    detected_at: str = ""
    success: bool = True
    message: str = ""


@dataclass
class RegimeHistoryPoint:
    date: str
    regime: str
    probability: float
    volatility: float


@dataclass
class MarketStateResult:
    overall_regime: str
    components: list[dict] = field(default_factory=list)
    risk_level: str = "normal"  # low, normal, elevated, high
    success: bool = True
    message: str = ""


# In-memory cache for fitted models
_model_cache: dict[str, tuple[float, object, dict]] = {}


def _label_regimes(model: GaussianHMM) -> dict[int, str]:
    """Label HMM states by mean return and volatility characteristics.

    Strategy: sort states by mean return, assign labels based on rank.
    Handles 2, 3, or 4 states gracefully.
    """
    n = model.n_components
    # Extract mean return per state (first feature = daily return)
    means = np.array([model.means_[i][0] for i in range(n)])

    # Extract volatility per state (first feature = return variance)
    vols = np.ones(n)
    try:
        for i in range(n):
            cov = model.covars_[i]
            if cov.ndim == 2:  # "full" covariance
                vols[i] = np.sqrt(float(cov[0][0]))
            elif cov.ndim == 1:  # "diag" covariance
                vols[i] = np.sqrt(float(cov[0]))
            else:
                vols[i] = np.sqrt(float(cov))
    except Exception:
        pass

    # Sort by mean return ascending → [most bearish, ..., most bullish]
    sorted_indices = np.argsort(means)

    labels = {}
    if n == 2:
        labels[int(sorted_indices[0])] = "bear"
        labels[int(sorted_indices[1])] = "bull"
    elif n == 3:
        labels[int(sorted_indices[0])] = "bear"
        labels[int(sorted_indices[1])] = "sideways"
        labels[int(sorted_indices[2])] = "bull"
    else:  # 4 states
        # Check which of the low-return states has higher vol → crisis
        low_states = sorted_indices[:2]
        if float(vols[low_states[0]]) > float(vols[low_states[1]]):
            labels[int(low_states[0])] = "crisis"
            labels[int(low_states[1])] = "bear"
        else:
            labels[int(low_states[0])] = "bear"
            labels[int(low_states[1])] = "crisis"
        labels[int(sorted_indices[2])] = "sideways"
        labels[int(sorted_indices[3])] = "bull"

    return labels


async def _get_features(
    conn: asyncpg.Connection, symbol: str, days: int
) -> tuple[np.ndarray, list[date]]:
    """Get returns + volatility features for HMM. Returns (features, dates)."""
    # Try to find asset_id by symbol
    row = await conn.fetchrow(
        "SELECT asset_id FROM assets WHERE symbol = $1", symbol
    )
    asset_id = row["asset_id"] if row else None

    if asset_id:
        # Fetch from historical_prices
        rows = await conn.fetch(
            """SELECT date, close_price FROM historical_prices
               WHERE asset_id = $1 AND date >= $2
               ORDER BY date""",
            asset_id, date.today() - timedelta(days=days + 50),
        )
    else:
        rows = []

    if len(rows) < 60:
        # Try fetching via yfinance directly
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=f"{days}d")
            if hist.empty:
                return np.array([]), []
            closes = hist["Close"].values
            dates_list = [d.date() for d in hist.index]
        except Exception:
            return np.array([]), []
    else:
        closes = np.array([float(r["close_price"]) for r in rows])
        dates_list = [r["date"] for r in rows]

    if len(closes) < 60:
        return np.array([]), []

    # Calculate features: daily returns + rolling 20d volatility
    returns = np.diff(np.log(closes))
    dates_list = dates_list[1:]  # align with returns

    # Rolling 20d volatility
    window = 20
    rolling_vol = np.array([
        np.std(returns[max(0, i - window):i]) * np.sqrt(252)
        for i in range(1, len(returns) + 1)
    ])

    # Stack features: [return, rolling_vol]
    features = np.column_stack([returns, rolling_vol])

    return features, dates_list


async def detect_regime(
    conn: asyncpg.Connection,
    symbol: str,
    days: int = 500,
) -> RegimeResult:
    """Detect current market regime using Gaussian HMM."""
    if not HAS_HMM:
        return RegimeResult(
            symbol=symbol, regime="unknown", probability=0,
            success=False, message="hmmlearn not installed. pip install hmmlearn",
        )

    features, dates = await _get_features(conn, symbol, days)
    if len(features) < 60:
        return RegimeResult(
            symbol=symbol, regime="unknown", probability=0,
            success=False, message=f"Insufficient data ({len(features)} points, need 60+)",
        )

    # Check model cache
    cache_key = f"{symbol}_{days}"
    now = time.time()
    if cache_key in _model_cache:
        cached_time, cached_model, cached_labels = _model_cache[cache_key]
        if now - cached_time < PythiaConfig.REGIME_CACHE_TTL_SECONDS:
            model = cached_model
            state_labels = cached_labels
        else:
            model = None
            state_labels = None
    else:
        model = None
        state_labels = None

    # Fit model if not cached
    if model is None:
        n_states = min(PythiaConfig.REGIME_HMM_STATES, max(2, len(features) // 30))
        fitted = False
        for cov_type in ("full", "diag"):
            model = GaussianHMM(
                n_components=n_states,
                covariance_type=cov_type,
                n_iter=200,
                random_state=42,
                verbose=False,
            )
            try:
                model.fit(features)
                fitted = True
                break
            except Exception:
                continue
        if not fitted:
            return RegimeResult(
                symbol=symbol, regime="unknown", probability=0,
                success=False, message="HMM fit failed with both full and diag covariance",
            )

        state_labels = _label_regimes(model)
        _model_cache[cache_key] = (now, model, state_labels)

    # Predict current state
    try:
        hidden_states = model.predict(features)
        state_probs = model.predict_proba(features)
    except Exception as e:
        return RegimeResult(
            symbol=symbol, regime="unknown", probability=0,
            success=False, message=f"HMM predict failed: {e}",
        )

    current_state = int(hidden_states[-1])
    current_probs = state_probs[-1]
    current_regime = state_labels.get(current_state, "unknown")
    current_prob = float(current_probs[current_state])

    # Build all probabilities
    all_probs = {}
    for state_idx, label in state_labels.items():
        if state_idx < len(current_probs):
            all_probs[label] = round(float(current_probs[state_idx]), 4)

    # Trend strength from recent returns
    recent_returns = features[-20:, 0]
    trend_strength = float(np.mean(recent_returns) / (np.std(recent_returns) + 1e-8))
    trend_strength = max(-1.0, min(1.0, trend_strength))

    # Current volatility
    current_vol = float(features[-1, 1])

    # Store in DB
    try:
        await conn.execute(
            """INSERT INTO market_regimes (symbol, regime, probability, volatility, trend_strength, detected_at, model_params)
               VALUES ($1, $2, $3, $4, $5, $6, $7)""",
            symbol, current_regime, current_prob, current_vol, trend_strength,
            date.today(),
            json.dumps(all_probs),
        )
    except Exception:
        pass

    return RegimeResult(
        symbol=symbol,
        regime=current_regime,
        probability=round(current_prob, 4),
        all_probabilities=all_probs,
        volatility=round(current_vol, 4),
        trend_strength=round(trend_strength, 4),
        detected_at=str(date.today()),
    )


async def get_regime_history(
    conn: asyncpg.Connection,
    symbol: str,
    days: int = 365,
) -> list[RegimeHistoryPoint]:
    """Get regime classification for each day in the lookback period."""
    if not HAS_HMM:
        return []

    features, dates = await _get_features(conn, symbol, days)
    if len(features) < 60:
        return []

    n_states = min(PythiaConfig.REGIME_HMM_STATES, max(2, len(features) // 30))
    model = GaussianHMM(
        n_components=n_states,
        covariance_type="full",
        n_iter=200,
        random_state=42,
    )
    try:
        model.fit(features)
        hidden_states = model.predict(features)
        state_probs = model.predict_proba(features)
    except Exception:
        return []

    state_labels = _label_regimes(model)

    history = []
    for i in range(len(hidden_states)):
        state = int(hidden_states[i])
        history.append(RegimeHistoryPoint(
            date=str(dates[i]),
            regime=state_labels.get(state, "unknown"),
            probability=round(float(state_probs[i][state]), 4),
            volatility=round(float(features[i, 1]), 4),
        ))

    return history


async def get_market_state(conn: asyncpg.Connection) -> MarketStateResult:
    """Aggregate regime across major indices."""
    indices = [
        # (symbol, name, region)
        ("^SET.BK", "SET Index", "Asia-Pacific"),
        ("^N225", "Nikkei 225", "Asia-Pacific"),
        ("^HSI", "Hang Seng", "Asia-Pacific"),
        ("000001.SS", "Shanghai", "Asia-Pacific"),
        ("399001.SZ", "Shenzhen", "Asia-Pacific"),
        ("^KS11", "KOSPI", "Asia-Pacific"),
        ("^TWII", "Taiwan", "Asia-Pacific"),
        ("^AXJO", "ASX 200", "Asia-Pacific"),
        ("VNM", "Vietnam", "Asia-Pacific"),
        ("^STI", "Singapore", "Asia-Pacific"),
        ("^JKSE", "Jakarta", "Asia-Pacific"),
        ("^GSPC", "S&P 500", "Americas"),
        ("^DJI", "Dow Jones", "Americas"),
        ("^IXIC", "NASDAQ", "Americas"),
        ("^BVSP", "Brazil", "Americas"),
        ("^FTSE", "FTSE 100", "Europe"),
        ("^GDAXI", "DAX", "Europe"),
        ("^FCHI", "CAC 40", "Europe"),
        ("^VIX", "VIX", "Volatility"),
    ]

    components = []
    regimes = []

    for symbol, name, region in indices:
        result = await detect_regime(conn, symbol, days=PythiaConfig.REGIME_LOOKBACK_DAYS)
        components.append({
            "symbol": symbol,
            "name": name,
            "region": region,
            "regime": result.regime,
            "probability": result.probability,
            "volatility": result.volatility,
            "trend_strength": result.trend_strength,
        })
        if result.success:
            regimes.append(result.regime)

    # Determine overall regime (majority vote)
    if not regimes:
        overall = "unknown"
    else:
        from collections import Counter
        regime_counts = Counter(regimes)
        overall = regime_counts.most_common(1)[0][0]

    # Risk level based on regime composition
    crisis_count = regimes.count("crisis")
    bear_count = regimes.count("bear")
    if crisis_count >= 2:
        risk_level = "high"
    elif crisis_count >= 1 or bear_count >= 2:
        risk_level = "elevated"
    elif bear_count >= 1:
        risk_level = "normal"
    else:
        risk_level = "low"

    return MarketStateResult(
        overall_regime=overall,
        components=components,
        risk_level=risk_level,
    )
