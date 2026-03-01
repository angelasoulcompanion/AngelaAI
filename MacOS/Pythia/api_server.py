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
    # Phase 4: AI Features
    ai_advisor,
    ai_sentiment,
    ai_forecast,
    ai_research,
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

# ── Phase 4: AI Features ───────────────────────────────
app.include_router(ai_advisor.router)
app.include_router(ai_sentiment.router)
app.include_router(ai_forecast.router)
app.include_router(ai_research.router)


if __name__ == "__main__":
    print("🏛️  Starting Pythia — Quantitative Finance + AI Analysis Platform")
    print("📍 Connecting to Neon Cloud (Singapore)")
    print("🔗 API will be available at http://127.0.0.1:8766")
    print("📊 Phase 1: Foundation (Portfolios, Assets, Market)")
    print("📈 Phase 2: Quantitative Analysis (MPT, VaR, Stress Tests)")
    print("🧮 Phase 3: Advanced Finance (Options, Backtest, Monte Carlo)")
    print("🤖 Phase 4: AI Features (Advisor, Sentiment, Forecast, Research)")
    uvicorn.run(app, host="127.0.0.1", port=8766)
