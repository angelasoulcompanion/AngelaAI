"""
Pythia — Correlation Monitor Service
Detects correlation regime shifts and risk-on/risk-off states.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

import asyncpg
import numpy as np

from config import PythiaConfig


@dataclass
class CorrelationShift:
    asset_1: str
    asset_2: str
    current_corr: float
    historical_corr: float
    shift: float
    significance: str  # normal, notable, significant


@dataclass
class CorrelationMonitorResult:
    portfolio_id: str
    correlation_regime: str  # normal, risk_on, risk_off
    avg_correlation: float = 0.0
    avg_historical: float = 0.0
    shifts: list[CorrelationShift] = field(default_factory=list)
    matrix_current: list[list[float]] = field(default_factory=list)
    symbols: list[str] = field(default_factory=list)
    success: bool = True
    message: str = ""


async def detect_correlation_shifts(
    conn: asyncpg.Connection,
    portfolio_id: UUID,
    window: int = 60,
    lookback: int = 252,
) -> CorrelationMonitorResult:
    """Detect correlation regime shifts in portfolio holdings."""
    from services.optimization_service import get_returns_matrix

    # Get portfolio holdings
    holdings = await conn.fetch(
        "SELECT asset_id FROM portfolio_holdings WHERE portfolio_id = $1",
        portfolio_id,
    )
    if len(holdings) < 2:
        return CorrelationMonitorResult(
            portfolio_id=str(portfolio_id),
            correlation_regime="unknown",
            success=False, message="Need at least 2 holdings",
        )

    asset_ids = [h["asset_id"] for h in holdings]
    start_date = date.today() - timedelta(days=lookback + 50)
    returns_matrix, symbols = await get_returns_matrix(conn, asset_ids, start_date)

    if returns_matrix.size == 0 or returns_matrix.shape[0] < window + 30:
        return CorrelationMonitorResult(
            portfolio_id=str(portfolio_id),
            correlation_regime="unknown",
            success=False, message="Insufficient data for correlation analysis",
        )

    n_assets = returns_matrix.shape[1]

    # Current correlation (recent window)
    recent = returns_matrix[-window:]
    current_corr = np.corrcoef(recent.T)

    # Historical correlation (full lookback)
    hist_corr = np.corrcoef(returns_matrix.T)

    # Detect shifts
    shifts = []
    for i in range(n_assets):
        for j in range(i + 1, n_assets):
            curr = float(current_corr[i, j])
            hist = float(hist_corr[i, j])
            shift = curr - hist

            if abs(shift) > 0.3:
                sig = "significant"
            elif abs(shift) > 0.15:
                sig = "notable"
            else:
                sig = "normal"

            if sig != "normal":
                shifts.append(CorrelationShift(
                    asset_1=symbols[i] if i < len(symbols) else str(asset_ids[i]),
                    asset_2=symbols[j] if j < len(symbols) else str(asset_ids[j]),
                    current_corr=round(curr, 4),
                    historical_corr=round(hist, 4),
                    shift=round(shift, 4),
                    significance=sig,
                ))

    # Sort by absolute shift
    shifts.sort(key=lambda x: abs(x.shift), reverse=True)

    # Average correlation levels
    upper_tri = np.triu_indices(n_assets, k=1)
    avg_current = float(np.mean(current_corr[upper_tri]))
    avg_hist = float(np.mean(hist_corr[upper_tri]))

    # Classify regime
    if avg_current > 0.6:
        regime = "risk_on"  # correlations converging → risk-on herding
    elif avg_current < 0.1:
        regime = "risk_off"  # correlations diverging → dispersion
    else:
        regime = "normal"

    # Format matrix for frontend
    matrix = [[round(float(current_corr[i, j]), 3) for j in range(n_assets)] for i in range(n_assets)]

    return CorrelationMonitorResult(
        portfolio_id=str(portfolio_id),
        correlation_regime=regime,
        avg_correlation=round(avg_current, 4),
        avg_historical=round(avg_hist, 4),
        shifts=shifts,
        matrix_current=matrix,
        symbols=symbols,
    )
