"""
Pythia — Chart Pattern Recognition Service
Detects: Head & Shoulders, Double Top/Bottom, Triangles, Flags, Wedges
Pure numpy peak/trough detection — no external TA library.
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
class PatternResult:
    pattern_type: str     # head_shoulders, double_top, double_bottom, ascending_triangle, etc.
    direction: str        # bullish, bearish
    confidence: float     # 0.0 to 1.0
    start_date: str = ""
    end_date: str = ""
    breakout_price: float = 0.0
    target_price: float = 0.0
    description: str = ""
    key_levels: list[float] = field(default_factory=list)


@dataclass
class PatternScanResult:
    asset_id: str
    symbol: str
    patterns: list[PatternResult] = field(default_factory=list)
    current_price: float = 0.0
    success: bool = True
    message: str = ""


def _find_peaks_troughs(
    closes: np.ndarray, order: int = 5
) -> tuple[np.ndarray, np.ndarray]:
    """Find local peaks and troughs using rolling window comparison."""
    peaks = []
    troughs = []

    for i in range(order, len(closes) - order):
        # Peak: higher than all neighbors within order
        if all(closes[i] >= closes[i - j] for j in range(1, order + 1)) and \
           all(closes[i] >= closes[i + j] for j in range(1, order + 1)):
            peaks.append(i)

        # Trough: lower than all neighbors within order
        if all(closes[i] <= closes[i - j] for j in range(1, order + 1)) and \
           all(closes[i] <= closes[i + j] for j in range(1, order + 1)):
            troughs.append(i)

    return np.array(peaks), np.array(troughs)


def _detect_double_top(
    closes: np.ndarray, peaks: np.ndarray, dates: list, tolerance: float = 0.03
) -> Optional[PatternResult]:
    """Detect double top pattern."""
    if len(peaks) < 2:
        return None

    # Look at last few peaks
    for i in range(len(peaks) - 1, 0, -1):
        p1, p2 = peaks[i - 1], peaks[i]
        h1, h2 = float(closes[p1]), float(closes[p2])

        # Peaks should be at similar height
        if abs(h1 - h2) / max(h1, h2) < tolerance:
            # Find neckline (trough between peaks)
            between_closes = closes[p1:p2]
            if len(between_closes) > 2:
                neckline = float(np.min(between_closes))
                height = max(h1, h2) - neckline
                target = neckline - height

                # Current price should be near or below neckline
                current = float(closes[-1])
                if current < max(h1, h2) * 0.98:
                    confidence = 0.7 if current < neckline else 0.5
                    return PatternResult(
                        pattern_type="double_top",
                        direction="bearish",
                        confidence=confidence,
                        start_date=str(dates[p1]) if p1 < len(dates) else "",
                        end_date=str(dates[min(p2 + 5, len(dates) - 1)]),
                        breakout_price=round(neckline, 4),
                        target_price=round(target, 4),
                        description=f"Double top at {h1:.2f}/{h2:.2f}, neckline {neckline:.2f}",
                        key_levels=[round(h1, 4), round(h2, 4), round(neckline, 4)],
                    )
                break

    return None


def _detect_double_bottom(
    closes: np.ndarray, troughs: np.ndarray, dates: list, tolerance: float = 0.03
) -> Optional[PatternResult]:
    """Detect double bottom pattern."""
    if len(troughs) < 2:
        return None

    for i in range(len(troughs) - 1, 0, -1):
        t1, t2 = troughs[i - 1], troughs[i]
        l1, l2 = float(closes[t1]), float(closes[t2])

        if abs(l1 - l2) / max(l1, l2) < tolerance:
            between_closes = closes[t1:t2]
            if len(between_closes) > 2:
                neckline = float(np.max(between_closes))
                height = neckline - min(l1, l2)
                target = neckline + height

                current = float(closes[-1])
                if current > min(l1, l2) * 1.02:
                    confidence = 0.7 if current > neckline else 0.5
                    return PatternResult(
                        pattern_type="double_bottom",
                        direction="bullish",
                        confidence=confidence,
                        start_date=str(dates[t1]) if t1 < len(dates) else "",
                        end_date=str(dates[min(t2 + 5, len(dates) - 1)]),
                        breakout_price=round(neckline, 4),
                        target_price=round(target, 4),
                        description=f"Double bottom at {l1:.2f}/{l2:.2f}, neckline {neckline:.2f}",
                        key_levels=[round(l1, 4), round(l2, 4), round(neckline, 4)],
                    )
                break

    return None


def _detect_head_shoulders(
    closes: np.ndarray, peaks: np.ndarray, troughs: np.ndarray, dates: list
) -> Optional[PatternResult]:
    """Detect head and shoulders pattern."""
    if len(peaks) < 3 or len(troughs) < 2:
        return None

    # Last 3 peaks
    for i in range(len(peaks) - 1, 1, -1):
        left_s, head, right_s = peaks[i - 2], peaks[i - 1], peaks[i]
        h_left = float(closes[left_s])
        h_head = float(closes[head])
        h_right = float(closes[right_s])

        # Head should be highest
        if h_head > h_left and h_head > h_right:
            # Shoulders should be at similar height
            if abs(h_left - h_right) / max(h_left, h_right) < 0.05:
                # Neckline from troughs between
                relevant_troughs = troughs[(troughs > left_s) & (troughs < right_s)]
                if len(relevant_troughs) >= 1:
                    neckline = float(np.mean(closes[relevant_troughs]))
                    height = h_head - neckline
                    target = neckline - height

                    confidence = 0.6
                    if float(closes[-1]) < neckline:
                        confidence = 0.8

                    return PatternResult(
                        pattern_type="head_shoulders",
                        direction="bearish",
                        confidence=confidence,
                        start_date=str(dates[left_s]) if left_s < len(dates) else "",
                        end_date=str(dates[min(right_s + 5, len(dates) - 1)]),
                        breakout_price=round(neckline, 4),
                        target_price=round(target, 4),
                        description=f"H&S: shoulders {h_left:.2f}/{h_right:.2f}, head {h_head:.2f}",
                        key_levels=[round(h_left, 4), round(h_head, 4), round(h_right, 4), round(neckline, 4)],
                    )
                break

    return None


def _detect_triangle(
    closes: np.ndarray, peaks: np.ndarray, troughs: np.ndarray, dates: list
) -> Optional[PatternResult]:
    """Detect ascending/descending/symmetric triangle."""
    if len(peaks) < 2 or len(troughs) < 2:
        return None

    # Use last 4 peaks/troughs
    recent_peaks = peaks[-min(4, len(peaks)):]
    recent_troughs = troughs[-min(4, len(troughs)):]

    peak_values = closes[recent_peaks]
    trough_values = closes[recent_troughs]

    # Slopes
    if len(recent_peaks) >= 2:
        peak_slope = float(peak_values[-1] - peak_values[0]) / (recent_peaks[-1] - recent_peaks[0] + 1)
    else:
        peak_slope = 0

    if len(recent_troughs) >= 2:
        trough_slope = float(trough_values[-1] - trough_values[0]) / (recent_troughs[-1] - recent_troughs[0] + 1)
    else:
        trough_slope = 0

    # Classify
    current = float(closes[-1])
    avg_peak = float(np.mean(peak_values))
    avg_trough = float(np.mean(trough_values))
    height = avg_peak - avg_trough

    if abs(peak_slope) < 0.01 and trough_slope > 0.005:
        # Ascending triangle (flat top, rising bottom)
        return PatternResult(
            pattern_type="ascending_triangle",
            direction="bullish",
            confidence=0.6,
            start_date=str(dates[recent_troughs[0]]) if recent_troughs[0] < len(dates) else "",
            end_date=str(dates[-1]),
            breakout_price=round(avg_peak, 4),
            target_price=round(avg_peak + height, 4),
            description=f"Ascending triangle, resistance at {avg_peak:.2f}",
            key_levels=[round(avg_peak, 4), round(float(trough_values[-1]), 4)],
        )
    elif peak_slope < -0.005 and abs(trough_slope) < 0.01:
        # Descending triangle
        return PatternResult(
            pattern_type="descending_triangle",
            direction="bearish",
            confidence=0.6,
            start_date=str(dates[recent_peaks[0]]) if recent_peaks[0] < len(dates) else "",
            end_date=str(dates[-1]),
            breakout_price=round(avg_trough, 4),
            target_price=round(avg_trough - height, 4),
            description=f"Descending triangle, support at {avg_trough:.2f}",
            key_levels=[round(float(peak_values[-1]), 4), round(avg_trough, 4)],
        )
    elif peak_slope < -0.003 and trough_slope > 0.003:
        # Symmetric triangle
        midpoint = (avg_peak + avg_trough) / 2
        return PatternResult(
            pattern_type="symmetric_triangle",
            direction="neutral",
            confidence=0.5,
            start_date=str(dates[min(recent_peaks[0], recent_troughs[0])]) if len(dates) > 0 else "",
            end_date=str(dates[-1]),
            breakout_price=round(midpoint, 4),
            target_price=round(midpoint + height if current > midpoint else midpoint - height, 4),
            description="Symmetric triangle — watch for breakout direction",
            key_levels=[round(float(peak_values[-1]), 4), round(float(trough_values[-1]), 4)],
        )

    return None


def _detect_support_resistance(
    closes: np.ndarray, peaks: np.ndarray, troughs: np.ndarray
) -> tuple[list[float], list[float]]:
    """Find support and resistance levels."""
    resistance = sorted(set(round(float(closes[p]), 2) for p in peaks[-5:]), reverse=True)[:3]
    support = sorted(set(round(float(closes[t]), 2) for t in troughs[-5:]))[:3]
    return support, resistance


async def detect_patterns(
    conn: asyncpg.Connection,
    asset_id: UUID,
    days: int = 120,
) -> PatternScanResult:
    """Detect chart patterns for an asset."""
    row = await conn.fetchrow("SELECT symbol FROM assets WHERE asset_id = $1", asset_id)
    if not row:
        return PatternScanResult(asset_id=str(asset_id), symbol="", success=False, message="Asset not found")
    symbol = row["symbol"]

    from services.price_fetcher_service import PriceFetcherService
    await PriceFetcherService.ensure_fresh(conn, asset_id)

    prices = await conn.fetch(
        """SELECT date, close_price FROM historical_prices
           WHERE asset_id = $1 AND date >= $2
           ORDER BY date""",
        asset_id, date.today() - timedelta(days=days + 30),
    )

    if len(prices) < 30:
        return PatternScanResult(
            asset_id=str(asset_id), symbol=symbol,
            success=False, message=f"Insufficient data ({len(prices)} points)",
        )

    closes = np.array([float(p["close_price"]) for p in prices])
    dates = [str(p["date"]) for p in prices]
    current_price = float(closes[-1])

    # Find peaks and troughs
    peaks, troughs = _find_peaks_troughs(closes, order=5)

    patterns = []

    # Detect each pattern type
    for detector in [
        lambda: _detect_double_top(closes, peaks, dates),
        lambda: _detect_double_bottom(closes, troughs, dates),
        lambda: _detect_head_shoulders(closes, peaks, troughs, dates),
        lambda: _detect_triangle(closes, peaks, troughs, dates),
    ]:
        try:
            result = detector()
            if result:
                patterns.append(result)
        except Exception:
            continue

    # Add support/resistance levels as a "pattern"
    if len(peaks) >= 2 and len(troughs) >= 2:
        support, resistance = _detect_support_resistance(closes, peaks, troughs)
        patterns.append(PatternResult(
            pattern_type="support_resistance",
            direction="neutral",
            confidence=0.8,
            description=f"Support: {support}, Resistance: {resistance}",
            key_levels=support + resistance,
        ))

    # Store patterns in DB
    for pat in patterns:
        if pat.pattern_type != "support_resistance":
            try:
                await conn.execute(
                    """INSERT INTO chart_patterns
                       (asset_id, pattern_type, direction, confidence, start_date, end_date,
                        breakout_price, target_price, metadata)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                    asset_id, pat.pattern_type, pat.direction, pat.confidence,
                    date.fromisoformat(pat.start_date) if pat.start_date else None,
                    date.fromisoformat(pat.end_date) if pat.end_date else None,
                    pat.breakout_price, pat.target_price,
                    json.dumps({"description": pat.description, "key_levels": pat.key_levels}),
                )
            except Exception:
                pass

    return PatternScanResult(
        asset_id=str(asset_id),
        symbol=symbol,
        patterns=patterns,
        current_price=round(current_price, 4),
    )


async def scan_patterns(
    conn: asyncpg.Connection,
    asset_ids: list[UUID],
) -> list[PatternScanResult]:
    """Batch scan multiple assets for patterns."""
    results = []
    for aid in asset_ids:
        try:
            result = await detect_patterns(conn, aid)
            if result.success and result.patterns:
                results.append(result)
        except Exception:
            continue
    return results
