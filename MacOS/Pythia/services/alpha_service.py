"""
Pythia — Alpha Generation Service (ML)
GradientBoosting walk-forward prediction of 5-day return direction.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta
from uuid import UUID

import asyncpg
import numpy as np

try:
    from sklearn.ensemble import HistGradientBoostingClassifier
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


@dataclass
class AlphaResult:
    asset_id: str
    symbol: str
    predicted_direction: str  # up, down, flat
    probability: float = 0.0
    feature_importance: list[dict] = field(default_factory=list)
    model_accuracy: float = 0.0
    training_samples: int = 0
    success: bool = True
    message: str = ""


FEATURE_NAMES = [
    "ret_5d", "ret_10d", "ret_20d",
    "vol_20d", "vol_ratio",
    "rsi", "macd_hist",
    "volume_zscore", "price_vs_sma50",
]


def _engineer_features(closes: np.ndarray, volumes: np.ndarray) -> np.ndarray:
    """Create feature matrix from price/volume data."""
    n = len(closes)
    returns = np.diff(np.log(closes))

    features = np.full((n, len(FEATURE_NAMES)), np.nan)

    for i in range(50, n):
        r = returns[:i]
        # Rolling returns
        features[i, 0] = np.sum(r[-5:])
        features[i, 1] = np.sum(r[-10:])
        features[i, 2] = np.sum(r[-20:])
        # Volatility
        features[i, 3] = np.std(r[-20:]) * np.sqrt(252)
        hist_vol = np.std(r[-60:]) * np.sqrt(252) if len(r) >= 60 else features[i, 3]
        features[i, 4] = features[i, 3] / (hist_vol + 1e-10)
        # RSI
        gains = np.where(r[-14:] > 0, r[-14:], 0)
        losses = np.where(r[-14:] < 0, -r[-14:], 0)
        rs = np.mean(gains) / (np.mean(losses) + 1e-10)
        features[i, 5] = 100 - 100 / (1 + rs)
        # MACD histogram approx
        ema12 = np.mean(closes[i-12:i])
        ema26 = np.mean(closes[i-26:i]) if i >= 26 else ema12
        features[i, 6] = (ema12 - ema26) / closes[i]
        # Volume z-score
        if np.std(volumes[i-20:i]) > 0:
            features[i, 7] = (volumes[i] - np.mean(volumes[i-20:i])) / np.std(volumes[i-20:i])
        else:
            features[i, 7] = 0
        # Price vs SMA50
        sma50 = np.mean(closes[i-50:i])
        features[i, 8] = (closes[i] - sma50) / sma50

    return features


async def generate_alpha_signals(
    conn: asyncpg.Connection,
    asset_id: UUID,
    days: int = 500,
) -> AlphaResult:
    """Generate ML-based alpha signals using walk-forward prediction."""
    if not HAS_SKLEARN:
        return AlphaResult(
            asset_id=str(asset_id), symbol="",
            predicted_direction="flat",
            success=False, message="scikit-learn not installed",
        )

    row = await conn.fetchrow("SELECT symbol FROM assets WHERE asset_id = $1", asset_id)
    if not row:
        return AlphaResult(asset_id=str(asset_id), symbol="", predicted_direction="flat",
                           success=False, message="Asset not found")
    symbol = row["symbol"]

    from services.price_fetcher_service import PriceFetcherService
    await PriceFetcherService.ensure_fresh(conn, asset_id)

    prices = await conn.fetch(
        """SELECT close_price, volume FROM historical_prices
           WHERE asset_id = $1 AND date >= $2
           ORDER BY date""",
        asset_id, date.today() - timedelta(days=days + 50),
    )

    if len(prices) < 120:
        return AlphaResult(asset_id=str(asset_id), symbol=symbol, predicted_direction="flat",
                           success=False, message=f"Insufficient data ({len(prices)} points, need 120+)")

    closes = np.array([float(p["close_price"]) for p in prices])
    volumes = np.array([float(p["volume"] or 0) for p in prices])

    # Engineer features
    features = _engineer_features(closes, volumes)

    # Create target: 5-day forward return direction
    returns = np.diff(np.log(closes))
    target = np.full(len(closes), np.nan)
    for i in range(len(closes) - 5):
        fwd_ret = np.sum(returns[i:i+5]) if i + 5 <= len(returns) else 0
        target[i] = 1 if fwd_ret > 0.005 else (0 if fwd_ret < -0.005 else 2)  # up/down/flat

    # Valid rows (no NaN)
    valid = ~(np.isnan(features).any(axis=1) | np.isnan(target))
    X = features[valid]
    y = target[valid].astype(int)

    if len(X) < 60:
        return AlphaResult(asset_id=str(asset_id), symbol=symbol, predicted_direction="flat",
                           success=False, message="Not enough valid samples for ML")

    # Walk-forward: train on [0:T-30], predict last 30 days
    split = max(len(X) - 30, int(len(X) * 0.8))
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    try:
        model = HistGradientBoostingClassifier(
            max_iter=100, max_depth=4, learning_rate=0.1, random_state=42,
        )
        model.fit(X_train, y_train)
    except Exception as e:
        return AlphaResult(asset_id=str(asset_id), symbol=symbol, predicted_direction="flat",
                           success=False, message=f"Model training failed: {e}")

    # Predict current (last row)
    last_features = X[-1:].copy()
    pred = model.predict(last_features)[0]
    proba = model.predict_proba(last_features)[0]

    direction = "up" if pred == 1 else ("down" if pred == 0 else "flat")
    probability = float(np.max(proba))

    # Test accuracy
    accuracy = float(np.mean(model.predict(X_test) == y_test)) if len(X_test) > 0 else 0

    # Feature importance
    importances = model.feature_importances_ if hasattr(model, 'feature_importances_') else np.zeros(len(FEATURE_NAMES))
    fi = sorted(
        [{"feature": FEATURE_NAMES[i], "importance": round(float(importances[i]), 4)}
         for i in range(min(len(FEATURE_NAMES), len(importances)))],
        key=lambda x: x["importance"], reverse=True,
    )

    return AlphaResult(
        asset_id=str(asset_id),
        symbol=symbol,
        predicted_direction=direction,
        probability=round(probability, 4),
        feature_importance=fi,
        model_accuracy=round(accuracy, 4),
        training_samples=len(X_train),
    )
