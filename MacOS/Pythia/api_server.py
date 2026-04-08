"""
Pythia — Quantitative Finance + AI Analysis Platform
FastAPI backend for SwiftUI macOS app

Architecture:
  SwiftUI App -> localhost:8766 -> FastAPI -> Neon Cloud (Singapore)

Created: 2026-03-01
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import db
from routers import (
    # Phase 1: Foundation
    assets,
    dashboard,
    market,
    portfolios,
    rates,
    settings,
    watchlist,
    # Phase 2: Quantitative Analysis
    mpt,
    risk,
    metrics,
    # Phase 3: Advanced Finance
    options,
    backtest,
    monte_carlo,
    statistics,
    technical,
    # Phase 4: AI Features
    ai_advisor,
    ai_sentiment,
    ai_forecast,
    ai_research,
    # Phase 5: Market Breadth
    market_breadth,
    # Phase 6: Global Monitor
    global_monitor,
    # Phase 7: Quantitative Trading Engine
    regime,
    signals,
    factors,
    position_sizing,
    strategies,
    # Phase 8: AI Trading Intelligence
    patterns,
    screener,
    trade_plans,
    narrative,
    correlation_monitor,
    events,
    alerts,
    rebalance,
    ws_prices,
    earnings_calendar,
    # Phase 9: Alpha Ideas
    alpha_ideas,
)

app = FastAPI(
    title="Pythia API",
    description="Quantitative Finance + AI Analysis Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lifecycle events
app.add_event_handler("startup", db.startup)
app.add_event_handler("shutdown", db.shutdown)


# Health check (kept in main file for visibility)
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        pool = db.get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
            return {"status": "healthy", "database": "connected", "app": "Pythia", "region": "Singapore"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


# ── Phase 1: Foundation ──────────────────────────────────
app.include_router(portfolios.router)
app.include_router(assets.router)
app.include_router(market.router)
app.include_router(watchlist.router)
app.include_router(watchlist.angles_router)
app.include_router(rates.router)
app.include_router(dashboard.router)
app.include_router(settings.router)

# ── Phase 2: Quantitative Analysis ──────────────────────
app.include_router(mpt.router)
app.include_router(risk.router)
app.include_router(metrics.router)

# ── Phase 3: Advanced Finance ───────────────────────────
app.include_router(options.router)
app.include_router(backtest.router)
app.include_router(monte_carlo.router)
app.include_router(statistics.router)
app.include_router(technical.router)

# ── Phase 4: AI Features ───────────────────────────────
app.include_router(ai_advisor.router)
app.include_router(ai_sentiment.router)
app.include_router(ai_forecast.router)
app.include_router(ai_research.router)

# ── Phase 5: Market Breadth ───────────────────────────────
app.include_router(market_breadth.router)

# ── Phase 6: Global Monitor ──────────────────────────────
app.include_router(global_monitor.router)

# ── Phase 7: Quantitative Trading Engine ─────────────────
app.include_router(regime.router)
app.include_router(signals.router)
app.include_router(factors.router)
app.include_router(position_sizing.router)
app.include_router(strategies.router)

# ── Phase 8: AI Trading Intelligence ────────────────────
app.include_router(patterns.router)
app.include_router(screener.router)
app.include_router(trade_plans.router)
app.include_router(narrative.router)
app.include_router(correlation_monitor.router)
app.include_router(events.router)
app.include_router(alerts.router)

# ── Phase 7+8: Final (Alpha, Rebalance, Risk Budget) ────
app.include_router(rebalance.router)

# ── WebSocket: Live Price Stream ──────────────────────────
app.include_router(ws_prices.router)

# ── Earnings Calendar & Economic Events ──────────────────
app.include_router(earnings_calendar.router)

# ── Phase 9: Alpha Ideas (Factor Research) ──────────────
app.include_router(alpha_ideas.router)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()

    print("🏛️  Starting Pythia — Quantitative Finance + AI Analysis Platform")
    print("📍 Connecting to Neon Cloud (Singapore)")
    print(f"🔗 API will be available at http://127.0.0.1:{args.port}")
    uvicorn.run(app, host="127.0.0.1", port=args.port)
