"""
AI TOP — Local AI Training & Inference Studio
FastAPI backend for hardware monitoring, model management, fine-tuning, chat, and RAG.
Port: 8767
"""

import argparse
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import dashboard, models, finetune, chat, rag


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("AI TOP backend starting...")
    yield
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


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "AI TOP"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8767)
    args = parser.parse_args()
    uvicorn.run(app, host="0.0.0.0", port=args.port)
