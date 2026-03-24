"""
AI TOP — Local AI Training & Inference Studio
FastAPI backend for hardware monitoring, model management, fine-tuning, chat, and RAG.
Port: 8767
"""

import argparse
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add AngelaAI root to sys.path for angela_core imports
_angela_root = str(Path(__file__).resolve().parents[2])
if _angela_root not in sys.path:
    sys.path.insert(0, _angela_root)

from routers import dashboard, models, finetune, chat, rag, angela_brain, model_hub
from services.db_service import init_pool, close_pool, MACHINE_TAG

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"AI TOP backend starting... (machine={MACHINE_TAG})")
    try:
        await init_pool()
        print("Supabase pool connected")
        # Sync data from Supabase
        from services.finetune_service import sync_from_cloud as sync_ft
        from services.rag_service import sync_from_cloud as sync_rag
        await sync_ft()
        await sync_rag()
        print("Supabase sync complete")
    except Exception as e:
        print(f"WARNING: Supabase DB not available ({e}) — running in local-only mode")
    yield
    await close_pool()
    print("AI TOP backend shutting down...")


app = FastAPI(title="AI TOP", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(dashboard.router, prefix="/api")
app.include_router(models.router, prefix="/api")
app.include_router(finetune.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(rag.router, prefix="/api")
app.include_router(angela_brain.router, prefix="/api")
app.include_router(model_hub.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "AI TOP", "machine": MACHINE_TAG}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8767)
    args = parser.parse_args()
    uvicorn.run(app, host="0.0.0.0", port=args.port)
