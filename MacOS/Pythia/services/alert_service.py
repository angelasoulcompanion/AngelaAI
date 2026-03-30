"""
Pythia — Alert System Service
Configurable alerts for signals, risk thresholds, regime changes.
"""
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import asyncpg


@dataclass
class Alert:
    alert_id: str
    alert_type: str
    title: str
    message: str
    severity: str
    asset_id: Optional[str] = None
    portfolio_id: Optional[str] = None
    is_read: bool = False
    triggered_at: Optional[str] = None
    created_at: str = ""


async def get_alerts(
    conn: asyncpg.Connection,
    unread_only: bool = False,
    limit: int = 50,
) -> list[Alert]:
    """Get alerts, optionally filtered to unread only."""
    if unread_only:
        rows = await conn.fetch(
            """SELECT alert_id, alert_type, title, message, severity,
                      asset_id, portfolio_id, is_read, triggered_at, created_at
               FROM alerts WHERE is_read = false
               ORDER BY created_at DESC LIMIT $1""",
            limit,
        )
    else:
        rows = await conn.fetch(
            """SELECT alert_id, alert_type, title, message, severity,
                      asset_id, portfolio_id, is_read, triggered_at, created_at
               FROM alerts ORDER BY created_at DESC LIMIT $1""",
            limit,
        )

    return [
        Alert(
            alert_id=str(r["alert_id"]),
            alert_type=r["alert_type"],
            title=r["title"],
            message=r["message"] or "",
            severity=r["severity"] or "info",
            asset_id=str(r["asset_id"]) if r["asset_id"] else None,
            portfolio_id=str(r["portfolio_id"]) if r["portfolio_id"] else None,
            is_read=r["is_read"],
            triggered_at=str(r["triggered_at"]) if r["triggered_at"] else None,
            created_at=str(r["created_at"]),
        )
        for r in rows
    ]


async def create_alert(
    conn: asyncpg.Connection,
    alert_type: str,
    title: str,
    message: str = "",
    severity: str = "info",
    asset_id: Optional[UUID] = None,
    portfolio_id: Optional[UUID] = None,
    condition: Optional[dict] = None,
) -> str:
    """Create a new alert."""
    row = await conn.fetchrow(
        """INSERT INTO alerts (alert_type, title, message, severity, asset_id, portfolio_id, condition, triggered_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
           RETURNING alert_id""",
        alert_type, title, message, severity,
        asset_id, portfolio_id,
        json.dumps(condition) if condition else None,
    )
    return str(row["alert_id"])


async def mark_read(conn: asyncpg.Connection, alert_id: UUID) -> bool:
    result = await conn.execute(
        "UPDATE alerts SET is_read = true WHERE alert_id = $1", alert_id
    )
    return "UPDATE 1" in result


async def mark_all_read(conn: asyncpg.Connection) -> int:
    result = await conn.execute("UPDATE alerts SET is_read = true WHERE is_read = false")
    count = int(result.split(" ")[-1]) if result else 0
    return count


async def delete_alert(conn: asyncpg.Connection, alert_id: UUID) -> bool:
    result = await conn.execute("DELETE FROM alerts WHERE alert_id = $1", alert_id)
    return "DELETE 1" in result


async def get_unread_count(conn: asyncpg.Connection) -> int:
    return await conn.fetchval("SELECT COUNT(*) FROM alerts WHERE is_read = false") or 0


async def check_and_generate_alerts(conn: asyncpg.Connection) -> list[str]:
    """Check conditions and auto-generate alerts. Called on-demand or periodically."""
    generated = []

    # 1. Check for regime changes
    try:
        from services.regime_service import detect_regime
        for symbol, name in [("^SET.BK", "SET"), ("^GSPC", "S&P 500")]:
            result = await detect_regime(conn, symbol, days=200)
            if result.success and result.regime in ("crisis", "bear"):
                # Check if we already alerted today
                existing = await conn.fetchval(
                    """SELECT COUNT(*) FROM alerts
                       WHERE alert_type = 'regime' AND title LIKE $1
                       AND created_at >= CURRENT_DATE""",
                    f"%{name}%",
                )
                if not existing:
                    aid = await create_alert(
                        conn,
                        alert_type="regime",
                        title=f"{name} in {result.regime.upper()} regime",
                        message=f"{name} detected as {result.regime} with {result.probability*100:.0f}% confidence. Vol: {result.volatility*100:.1f}%",
                        severity="warning" if result.regime == "bear" else "critical",
                    )
                    generated.append(aid)
    except Exception:
        pass

    # 2. Check for high-strength signals
    try:
        strong_signals = await conn.fetch(
            """SELECT DISTINCT a.symbol, ts.direction, ts.strength
               FROM trading_signals ts
               JOIN assets a ON a.asset_id = ts.asset_id
               WHERE ts.created_at >= NOW() - INTERVAL '1 hour'
               AND ts.strength > 0.8
               ORDER BY ts.strength DESC LIMIT 5"""
        )
        for s in strong_signals:
            existing = await conn.fetchval(
                """SELECT COUNT(*) FROM alerts
                   WHERE alert_type = 'signal' AND title LIKE $1
                   AND created_at >= CURRENT_DATE""",
                f"%{s['symbol']}%",
            )
            if not existing:
                aid = await create_alert(
                    conn,
                    alert_type="signal",
                    title=f"Strong {s['direction']} signal: {s['symbol']}",
                    message=f"Signal strength: {s['strength']:.2f}",
                    severity="info",
                )
                generated.append(aid)
    except Exception:
        pass

    return generated
