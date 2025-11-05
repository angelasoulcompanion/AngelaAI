"""
Infrastructure Adapters

Adapters that bridge legacy services with new Clean Architecture.

Author: Angela AI Architecture Team
Date: 2025-10-30
"""

from angela_core.infrastructure.adapters.base_adapter import BaseServiceAdapter
from angela_core.infrastructure.adapters.conversation_adapter import ConversationAdapter
from angela_core.infrastructure.adapters.emotion_adapter import EmotionAdapter
from angela_core.infrastructure.adapters.memory_adapter import MemoryAdapter
from angela_core.infrastructure.adapters.document_adapter import DocumentAdapter

__all__ = [
    "BaseServiceAdapter",
    "ConversationAdapter",
    "EmotionAdapter",
    "MemoryAdapter",
    "DocumentAdapter",
]

# Unified adapter (recommended entry point)
from angela_core.infrastructure.adapters.legacy_service_adapter import (
    LegacyServiceAdapter,
    get_adapter
)

__all__.extend([
    "LegacyServiceAdapter",
    "get_adapter",
])
