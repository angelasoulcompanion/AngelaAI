"""
Document Use Cases

Use cases related to document ingestion and RAG system.
"""

from angela_core.application.use_cases.document.ingest_document_use_case import (
    IngestDocumentUseCase,
    IngestDocumentInput,
    IngestDocumentOutput
)

__all__ = [
    'IngestDocumentUseCase',
    'IngestDocumentInput',
    'IngestDocumentOutput',
]
