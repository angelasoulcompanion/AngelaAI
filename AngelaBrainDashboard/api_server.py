"""
Angela Brain Dashboard API - Connect to Neon Cloud
FastAPI backend for SwiftUI Dashboard

Architecture:
  SwiftUI Dashboard -> localhost:8765 -> FastAPI -> Neon Cloud (Singapore)

Created: 2026-01-08
Refactored: 2026-01-30  (split into routers/, helpers/, db.py, schemas.py)
"""
import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

import db
from routers import (
    chat,
    conversations,
    dashboard,
    diary,
    emotions,
    experiences,
    goals,
    guidelines,
    human_mind,
    knowledge,
    learning,
    meetings,
    news,
    preferences,
    projects,
    scheduled_tasks,
    scripts,
    skills,
    subconsciousness,
    tasks,
    worker,
)

app = FastAPI(
    title="Angela Brain Dashboard API",
    description="REST API for Angela Brain Dashboard - connects to Neon Cloud",
    version="2.0.0"
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
            return {"status": "healthy", "database": "connected", "region": "Singapore"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


# Register all routers
app.include_router(chat.router)
app.include_router(dashboard.router)
app.include_router(emotions.router)
app.include_router(conversations.router)
app.include_router(goals.router)
app.include_router(preferences.router)
app.include_router(experiences.router)
app.include_router(knowledge.router)
app.include_router(learning.router)
app.include_router(tasks.router)
app.include_router(skills.router)
app.include_router(projects.router)
app.include_router(worker.router)
app.include_router(diary.router)
app.include_router(human_mind.router)
app.include_router(guidelines.router)
app.include_router(news.router)
app.include_router(subconsciousness.router)
app.include_router(meetings.router)
app.include_router(scheduled_tasks.router)
app.include_router(scripts.router)


# Legacy endpoint path (original: /api/subconscious/patterns)
@app.get("/api/subconscious/patterns")
async def get_subconscious_patterns(limit: int = Query(10, ge=1, le=50)):
    """Fetch subconscious patterns"""
    pool = db.get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT subconscious_id::text, pattern_type, pattern_category, pattern_key,
                   pattern_description, instinctive_response,
                   confidence_score, activation_strength, reinforcement_count,
                   last_reinforced_at, created_at
            FROM angela_subconscious
            ORDER BY activation_strength DESC, confidence_score DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


if __name__ == "__main__":
    print("🚀 Starting Angela Brain Dashboard API...")
    print("📍 Connecting to Neon Cloud (Singapore)")
    print("🔗 API will be available at http://127.0.0.1:8765")
    uvicorn.run(app, host="127.0.0.1", port=8765)
