"""
Event Bus — Async pub/sub for reactive events.
===============================================
Provides a reactive event system alongside the existing 5-min daemon loop.

Architecture:
    Existing 5-min loop (scheduled) ← STAYS
        +
    EventBus (reactive) ← NEW
        ├── CalendarListener: event in 15 min → alert David
        ├── BrainDecisionListener: thought → dispatcher → execute
        └── Future: file watcher, email listener, IoT

Usage:
    bus = EventBus()

    # Subscribe
    bus.subscribe("calendar.upcoming", handler_func)

    # Publish
    await bus.publish("calendar.upcoming", {"event": "Meeting", "in_minutes": 15})

Events are processed asynchronously via asyncio.Queue.

By: Angela 💜
Created: 2026-02-17
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """An event published to the bus."""
    topic: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "unknown"

    def __str__(self):
        return f"Event({self.topic}, source={self.source})"


# Type for async event handlers
EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class EventBus:
    """
    Async event bus with topic-based pub/sub.

    Thread-safe, supports wildcards (e.g. "calendar.*").
    """

    def __init__(self, max_queue_size: int = 100):
        self._subscribers: Dict[str, List[EventHandler]] = {}
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None
        self._processed_count = 0
        self._error_count = 0

    # ── Pub/Sub ──

    def subscribe(self, topic: str, handler: EventHandler) -> None:
        """Subscribe a handler to a topic. Supports wildcard '*'."""
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(handler)
        logger.debug("EventBus: subscribed to '%s'", topic)

    def unsubscribe(self, topic: str, handler: EventHandler) -> None:
        """Unsubscribe a handler from a topic."""
        if topic in self._subscribers:
            self._subscribers[topic] = [h for h in self._subscribers[topic] if h != handler]

    async def publish(self, topic: str, data: Dict[str, Any] = None,
                      source: str = "unknown") -> None:
        """Publish an event to the bus."""
        event = Event(topic=topic, data=data or {}, source=source)

        try:
            self._queue.put_nowait(event)
            logger.debug("EventBus: published %s", event)
        except asyncio.QueueFull:
            logger.warning("EventBus: queue full, dropping event %s", event)

    # ── Processing ──

    async def start(self) -> None:
        """Start the event processor loop."""
        if self._running:
            return

        self._running = True
        self._processor_task = asyncio.create_task(self._process_loop())
        logger.info("EventBus: started")

    async def stop(self) -> None:
        """Stop the event processor."""
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        logger.info("EventBus: stopped (processed=%d, errors=%d)",
                     self._processed_count, self._error_count)

    async def _process_loop(self) -> None:
        """Main event processing loop."""
        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._dispatch(event)
                self._processed_count += 1
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("EventBus: processor error: %s", e)
                self._error_count += 1

    async def _dispatch(self, event: Event) -> None:
        """Dispatch event to matching subscribers."""
        handlers = self._find_handlers(event.topic)

        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error("EventBus: handler error for %s: %s", event.topic, e)
                self._error_count += 1

    def _find_handlers(self, topic: str) -> List[EventHandler]:
        """Find all handlers matching a topic (exact + wildcard)."""
        handlers = list(self._subscribers.get(topic, []))

        # Wildcard matching: "calendar.*" matches "calendar.upcoming"
        for pattern, subs in self._subscribers.items():
            if pattern.endswith(".*"):
                prefix = pattern[:-2]
                if topic.startswith(prefix + ".") and pattern != topic:
                    handlers.extend(subs)
            elif pattern == "*":
                handlers.extend(subs)

        return handlers

    # ── Summary ──

    def summary(self) -> Dict[str, Any]:
        """Get bus status summary."""
        return {
            "running": self._running,
            "queue_size": self._queue.qsize(),
            "topics": list(self._subscribers.keys()),
            "total_handlers": sum(len(h) for h in self._subscribers.values()),
            "processed": self._processed_count,
            "errors": self._error_count,
        }


# ── Global Singleton ──

_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get or create the global event bus."""
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus
