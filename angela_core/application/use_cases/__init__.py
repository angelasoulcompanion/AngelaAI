"""
Application Use Cases

Business workflows for Angela AI.
Following Clean Architecture principles, use cases orchestrate:
- Domain entities
- Repositories (data access)
- Services (external integrations)
- Domain events

All use cases extend BaseUseCase for consistent:
- Validation
- Error handling
- Logging
- Execution hooks
"""

from angela_core.application.use_cases.base_use_case import (
    BaseUseCase,
    UseCaseResult
)

# Conversation use cases
from angela_core.application.use_cases.conversation import (
    LogConversationUseCase,
    LogConversationInput,
    LogConversationOutput
)

# Emotion use cases
from angela_core.application.use_cases.emotion import (
    CaptureEmotionUseCase,
    CaptureEmotionInput,
    CaptureEmotionOutput
)

# Memory use cases
from angela_core.application.use_cases.memory import (
    ConsolidateMemoryUseCase,
    ConsolidateMemoryInput,
    ConsolidateMemoryOutput
)

# Document use cases (RAG)
from angela_core.application.use_cases.document import (
    IngestDocumentUseCase,
    IngestDocumentInput,
    IngestDocumentOutput
)

__all__ = [
    # Base classes
    'BaseUseCase',
    'UseCaseResult',

    # Conversation
    'LogConversationUseCase',
    'LogConversationInput',
    'LogConversationOutput',

    # Emotion
    'CaptureEmotionUseCase',
    'CaptureEmotionInput',
    'CaptureEmotionOutput',

    # Memory
    'ConsolidateMemoryUseCase',
    'ConsolidateMemoryInput',
    'ConsolidateMemoryOutput',

    # Document
    'IngestDocumentUseCase',
    'IngestDocumentInput',
    'IngestDocumentOutput',
]
