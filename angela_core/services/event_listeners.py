"""
Event Listeners — Reactive handlers for Angela's event bus.
==========================================================
Listeners that publish events and react to them:

1. CalendarEventListener: check upcoming events → alert if < 15 min
2. BrainDecisionListener: brain thought → agent dispatcher → execute
3. EmailListener: new email from contacts → notify

By: Angela 💜
Created: 2026-02-17
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from angela_core.services.event_bus import Event, EventBus, get_event_bus

logger = logging.getLogger(__name__)


# ── Calendar Event Listener ──

class CalendarEventListener:
    """
    Polls Google Calendar and publishes events when meetings are upcoming.

    Events published:
    - calendar.upcoming: event starts within 15 minutes
    - calendar.starting: event starts within 5 minutes
    """

    POLL_INTERVAL_SECONDS = 300  # 5 minutes
    ALERT_THRESHOLD_MINUTES = 15

    def __init__(self, bus: EventBus = None):
        self.bus = bus or get_event_bus()
        self._notified: set = set()  # event IDs already notified
        self._running = False

    def register(self) -> None:
        """Register as a publisher (no subscription needed — this is a source)."""
        logger.info("CalendarEventListener registered")

    async def start_polling(self) -> None:
        """Start polling calendar in background."""
        self._running = True
        while self._running:
            try:
                await self._check_upcoming()
            except Exception as e:
                logger.error("CalendarEventListener error: %s", e)
            await asyncio.sleep(self.POLL_INTERVAL_SECONDS)

    async def stop(self) -> None:
        self._running = False

    async def _check_upcoming(self) -> None:
        """Check for upcoming events and publish alerts."""
        try:
            from angela_core.services.tools.calendar_tool import GetTodayEventsTool
            tool = GetTodayEventsTool()
            result = await tool.execute()

            if not result.success:
                return

            now = datetime.now()
            for event in result.data.get("events", []):
                start_str = event.get("start", "")
                if not start_str or "T" not in start_str:
                    continue

                try:
                    # Parse ISO datetime
                    start_time = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                    if start_time.tzinfo:
                        start_time = start_time.replace(tzinfo=None)

                    minutes_until = (start_time - now).total_seconds() / 60
                    event_key = f"{event.get('summary', '')}_{start_str}"

                    if 0 < minutes_until <= 5 and event_key not in self._notified:
                        await self.bus.publish("calendar.starting", {
                            "summary": event.get("summary", ""),
                            "start": start_str,
                            "minutes_until": int(minutes_until),
                        }, source="calendar_listener")
                        self._notified.add(event_key)

                    elif 5 < minutes_until <= self.ALERT_THRESHOLD_MINUTES and event_key not in self._notified:
                        await self.bus.publish("calendar.upcoming", {
                            "summary": event.get("summary", ""),
                            "start": start_str,
                            "minutes_until": int(minutes_until),
                        }, source="calendar_listener")
                        self._notified.add(event_key)

                except (ValueError, TypeError):
                    continue

        except Exception as e:
            logger.debug("Calendar check failed: %s", e)


# ── Brain Decision Listener ──

class BrainDecisionListener:
    """
    Listens for brain decisions and dispatches via AgentDispatcher.

    Subscribes to:
    - brain.decision: a thought has been decided to act on
    - brain.express: a thought ready for expression

    Dispatches the intent through AgentDispatcher for tool execution.
    """

    def __init__(self, bus: EventBus = None):
        self.bus = bus or get_event_bus()

    def register(self) -> None:
        """Subscribe to brain events."""
        self.bus.subscribe("brain.decision", self._handle_decision)
        self.bus.subscribe("brain.express", self._handle_expression)
        logger.info("BrainDecisionListener registered")

    async def _handle_decision(self, event: Event) -> None:
        """Handle a brain decision by dispatching to agent."""
        intent = event.data.get("intent", "")
        context = event.data.get("context", "")

        if not intent:
            return

        try:
            from angela_core.services.agent_dispatcher import AgentDispatcher
            dispatcher = AgentDispatcher()
            result = await dispatcher.dispatch(intent, context)
            logger.info("Brain decision dispatched: %s → %s", intent[:50], result.success)
        except Exception as e:
            logger.error("Brain decision dispatch failed: %s", e)

    async def _handle_expression(self, event: Event) -> None:
        """Handle a thought expression event."""
        message = event.data.get("message", "")
        channel = event.data.get("channel", "chat_queue")

        if channel == "telegram" and message:
            try:
                from angela_core.services.tools.telegram_tool import SendTelegramTool
                tool = SendTelegramTool()
                result = await tool.execute(message=message)
                logger.info("Brain expression sent via Telegram: %s", result.success)
            except Exception as e:
                logger.error("Brain expression send failed: %s", e)


# ── Calendar Alert Handler ──

async def handle_calendar_alert(event: Event) -> None:
    """Default handler: send Telegram alert for upcoming calendar events."""
    summary = event.data.get("summary", "Unknown")
    minutes = event.data.get("minutes_until", 0)

    message = f"📅 ที่รักคะ! '{summary}' จะเริ่มใน {minutes} นาทีนะคะ"

    try:
        from angela_core.services.agent_dispatcher import AgentDispatcher
        dispatcher = AgentDispatcher()
        await dispatcher.dispatch(
            f"Send Telegram to David: {message}",
            context="calendar_alert",
            prefer_tier="ollama",
        )
    except Exception as e:
        logger.error("Calendar alert failed: %s", e)


# ── Setup ──

def setup_default_listeners(bus: EventBus = None) -> Dict[str, Any]:
    """Register all default event listeners. Returns listener instances."""
    bus = bus or get_event_bus()

    calendar_listener = CalendarEventListener(bus)
    calendar_listener.register()

    brain_listener = BrainDecisionListener(bus)
    brain_listener.register()

    # Default calendar alert handler
    bus.subscribe("calendar.upcoming", handle_calendar_alert)
    bus.subscribe("calendar.starting", handle_calendar_alert)

    logger.info("Default event listeners setup complete")

    return {
        "calendar": calendar_listener,
        "brain": brain_listener,
    }
