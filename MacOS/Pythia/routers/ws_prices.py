"""
Pythia — WebSocket endpoint for live price streaming.
Client connects → subscribes to watchlist → receives 30s price updates.
"""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from services.price_stream_service import price_stream

router = APIRouter(tags=["websocket"])
logger = logging.getLogger("pythia.ws_prices")


@router.websocket("/ws/prices")
async def prices_websocket(
    ws: WebSocket,
    watchlist_id: str = Query(None, description="Watchlist ID to subscribe to"),
):
    """
    Live price stream.
    - Connect with optional ?watchlist_id=uuid
    - Receive price_update messages every 30s
    - Send {"action":"subscribe","watchlist_id":"uuid"} to change subscription
    """
    await price_stream.connect(ws, watchlist_id)
    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
                if msg.get("action") == "subscribe":
                    new_wl = msg.get("watchlist_id")
                    price_stream.update_subscription(ws, new_wl)
                    await ws.send_text(json.dumps({
                        "type": "ack",
                        "data": {"watchlist_id": new_wl},
                    }))
            except (json.JSONDecodeError, KeyError):
                pass
    except WebSocketDisconnect:
        pass
    finally:
        price_stream.disconnect(ws)
