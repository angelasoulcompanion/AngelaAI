"""
Angela Integrations Package
Native macOS app integrations

Updated: 2026-01-05 - Made EventKit import optional (requires Foundation framework)
"""

__all__ = []

# EventKit requires Foundation framework (macOS Python with PyObjC)
# Import lazily to avoid errors in environments without it
try:
    from .eventkit_integration import EventKitIntegration, ReminderData, eventkit
    __all__.extend(['EventKitIntegration', 'ReminderData', 'eventkit'])
except ImportError:
    EventKitIntegration = None
    ReminderData = None
    eventkit = None
