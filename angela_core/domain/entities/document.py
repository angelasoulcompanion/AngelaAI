#!/usr/bin/env python3
"""
Document Entity - Angela's RAG Document System
Represents documents and their chunks for Retrieval-Augmented Generation.

This system manages Angela's knowledge documents:
- Documents: Files ingested for knowledge (PDFs, markdown, code, etc.)
- Chunks: Semantic sections for retrieval with embeddings
- Processing: Status tracking for document processing pipeline
"""

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from enum import Enum
from pathlib import Path

from angela_core.shared.exceptions import (
    BusinessRuleViolationError,
    InvalidInputError,
    ValueOutOfRangeError
)


# ============================================================================
# ENUMS & VALUE OBJECTS
# ============================================================================

class ProcessingStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"           # Queued for processing
    PROCESSING = "processing"     # Currently being processed
    COMPLETED = "completed"       # Successfully processed
    FAILED = "failed"            # Processing failed
    ARCHIVED = "archived"        # Archived/deprecated


class FileType(str, Enum):
    """Supported file types."""
    PDF = "pdf"
    MARKDOWN = "markdown"
    TEXT = "text"
    CODE = "code"
    JSON = "json"
    HTML = "html"
    OTHER = "other"

    @classmethod
    def from_extension(cls, extension: str) -> 'FileType':
        """Get file type from extension."""
        ext_map = {
            '.pdf': cls.PDF,
            '.md': cls.MARKDOWN,
            '.txt': cls.TEXT,
            '.py': cls.CODE,
            '.js': cls.CODE,
            '.ts': cls.CODE,
            '.json': cls.JSON,
            '.html': cls.HTML,
            '.htm': cls.HTML,
        }
        return ext_map.get(extension.lower(), cls.OTHER)


class DocumentCategory(str, Enum):
    """Document categories."""
    # Angela's core knowledge
    ANGELA_CORE = "angela_core"
    ANGELA_PERSONALITY = "angela_personality"
    ANGELA_MEMORIES = "angela_memories"

    # Technical knowledge
    PROGRAMMING = "programming"
    DATABASE = "database"
    AI_ML = "ai_ml"
    SYSTEM_DESIGN = "system_design"

    # Documentation
    PROJECT_DOCS = "project_docs"
    API_DOCS = "api_docs"
    USER_GUIDE = "user_guide"

    # Personal
    DAVID = "david"
    CONVERSATIONS = "conversations"

    # General
    GENERAL = "general"
    OTHER = "other"


# ============================================================================
# DOCUMENT ENTITY
# ============================================================================

@dataclass(frozen=False)
class Document:
    """
    Document entity - represents a document in Angela's knowledge library.

    Documents are files ingested into the RAG system, chunked into
    semantic sections, and indexed with embeddings for retrieval.

    Invariants:
    - title must not be empty
    - file_path must be valid
    - importance_score must be 0.0-1.0
    - quality_rating must be 0.0-1.0
    - embedding must be 384 dimensions if provided

    Business Rules:
    - Documents about David have high importance
    - Angela's core documents have high quality rating
    - Processing status follows: pending → processing → completed/failed
    - Documents can be archived but not deleted (knowledge preservation)
    """

    # Core attributes (required, no defaults)
    title: str
    file_path: str

    # Identity (with defaults)
    id: UUID = field(default_factory=uuid4)

    # File metadata
    file_type: FileType = FileType.OTHER
    file_size_bytes: int = 0

    # Categorization
    category: DocumentCategory = DocumentCategory.GENERAL
    tags: List[str] = field(default_factory=list)
    author: Optional[str] = None

    # Content summaries
    summary: str = "Document summary pending"
    short_summary: str = "Summary pending"
    key_topics: List[str] = field(default_factory=list)

    # Chunking info
    total_chunks: int = 0

    # Processing
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    processing_error: Optional[str] = None

    # Usage tracking
    last_accessed_at: Optional[datetime] = None
    access_count: int = 0

    # Quality metrics
    importance_score: float = 0.5  # 0.0-1.0 scale
    quality_rating: float = 0.7    # 0.0-1.0 scale

    # Embedding for document-level search
    embedding: Optional[List[float]] = None

    # Metadata
    metadata_json: Dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Domain Events
    _events: List[Any] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        """Validate entity invariants."""
        self._validate()

    # ========================================================================
    # VALIDATION
    # ========================================================================

    def _validate(self):
        """
        Validate all business rules and invariants.

        Raises:
            InvalidInputError: If input is invalid
            ValueOutOfRangeError: If value is out of range
            BusinessRuleViolationError: If business rule is violated
        """
        # Title cannot be empty
        if not self.title or not self.title.strip():
            raise InvalidInputError(
                "title",
                self.title,
                "Document title cannot be empty"
            )

        # File path cannot be empty
        if not self.file_path or not self.file_path.strip():
            raise InvalidInputError(
                "file_path",
                self.file_path,
                "File path cannot be empty"
            )

        # Importance score must be 0.0-1.0
        if not 0.0 <= self.importance_score <= 1.0:
            raise ValueOutOfRangeError(
                "importance_score",
                self.importance_score,
                min_value=0.0,
                max_value=1.0
            )

        # Quality rating must be 0.0-1.0
        if not 0.0 <= self.quality_rating <= 1.0:
            raise ValueOutOfRangeError(
                "quality_rating",
                self.quality_rating,
                min_value=0.0,
                max_value=1.0
            )

        # Total chunks must be non-negative
        if self.total_chunks < 0:
            raise ValueOutOfRangeError(
                "total_chunks",
                self.total_chunks,
                min_value=0
            )

        # Embedding must be 384 dimensions
        if self.embedding is not None:
            if len(self.embedding) != 384:
                raise BusinessRuleViolationError(
                    "Embedding dimension must be 384",
                    details=f"Got {len(self.embedding)} dimensions"
                )

    # ========================================================================
    # FACTORY METHODS
    # ========================================================================

    @classmethod
    def create_from_file(
        cls,
        file_path: str,
        title: Optional[str] = None,
        category: DocumentCategory = DocumentCategory.GENERAL,
        importance: float = 0.5
    ) -> 'Document':
        """
        Factory: Create document from file path.

        Args:
            file_path: Path to file
            title: Document title (defaults to filename)
            category: Document category
            importance: Importance score (0.0-1.0)

        Returns:
            New document entity
        """
        path = Path(file_path)

        # Default title from filename
        if title is None:
            title = path.stem

        # Detect file type from extension
        file_type = FileType.from_extension(path.suffix)

        # Get file size if exists
        file_size = path.stat().st_size if path.exists() else 0

        return cls(
            title=title,
            file_path=str(path),
            file_type=file_type,
            file_size_bytes=file_size,
            category=category,
            importance_score=importance,
            processing_status=ProcessingStatus.PENDING
        )

    @classmethod
    def create_angela_document(
        cls,
        title: str,
        file_path: str,
        category: DocumentCategory = DocumentCategory.ANGELA_CORE
    ) -> 'Document':
        """
        Factory: Create Angela core document (high importance).

        Args:
            title: Document title
            file_path: Path to file
            category: Angela-related category

        Returns:
            New Angela document with high importance
        """
        return cls(
            title=title,
            file_path=file_path,
            category=category,
            importance_score=0.9,  # High importance for Angela's core knowledge
            quality_rating=0.9,
            tags=["angela", "core"],
            author="David"
        )

    @classmethod
    def create_david_document(
        cls,
        title: str,
        file_path: str
    ) -> 'Document':
        """
        Factory: Create document about David (highest importance).

        Args:
            title: Document title
            file_path: Path to file

        Returns:
            New document about David
        """
        return cls(
            title=title,
            file_path=file_path,
            category=DocumentCategory.DAVID,
            importance_score=1.0,  # Maximum importance for David
            quality_rating=1.0,
            tags=["david", "personal"],
            author="David"
        )

    # ========================================================================
    # PROCESSING STATUS MANAGEMENT
    # ========================================================================

    def start_processing(self) -> 'Document':
        """
        Mark document as processing.

        Returns:
            Updated document

        Raises:
            BusinessRuleViolationError: If not in pending state
        """
        if self.processing_status != ProcessingStatus.PENDING:
            raise BusinessRuleViolationError(
                "Cannot start processing",
                details=f"Document is in {self.processing_status.value} state"
            )

        return replace(
            self,
            processing_status=ProcessingStatus.PROCESSING,
            processing_error=None,
            updated_at=datetime.now()
        )

    def mark_completed(self, chunk_count: int) -> 'Document':
        """
        Mark document processing as completed.

        Args:
            chunk_count: Number of chunks created

        Returns:
            Updated document
        """
        return replace(
            self,
            processing_status=ProcessingStatus.COMPLETED,
            total_chunks=chunk_count,
            processing_error=None,
            updated_at=datetime.now()
        )

    def mark_failed(self, error: str) -> 'Document':
        """
        Mark document processing as failed.

        Args:
            error: Error message

        Returns:
            Updated document
        """
        return replace(
            self,
            processing_status=ProcessingStatus.FAILED,
            processing_error=error,
            updated_at=datetime.now()
        )

    def archive(self) -> 'Document':
        """
        Archive document (soft delete).

        Returns:
            Updated document
        """
        return replace(
            self,
            processing_status=ProcessingStatus.ARCHIVED,
            updated_at=datetime.now()
        )

    def retry_processing(self) -> 'Document':
        """
        Reset to pending for retry.

        Returns:
            Updated document
        """
        return replace(
            self,
            processing_status=ProcessingStatus.PENDING,
            processing_error=None,
            updated_at=datetime.now()
        )

    # ========================================================================
    # BUSINESS LOGIC
    # ========================================================================

    def add_embedding(self, embedding: List[float]) -> 'Document':
        """
        Add vector embedding to document.

        Args:
            embedding: 384-dim vector

        Returns:
            Updated document
        """
        if len(embedding) != 384:
            raise BusinessRuleViolationError(
                "Embedding dimension must be 384",
                details=f"Got {len(embedding)} dimensions"
            )

        return replace(self, embedding=embedding)

    def add_tag(self, tag: str) -> 'Document':
        """
        Add tag to document.

        Args:
            tag: Tag to add

        Returns:
            Updated document
        """
        if tag not in self.tags:
            new_tags = self.tags.copy()
            new_tags.append(tag)
            return replace(self, tags=new_tags, updated_at=datetime.now())
        return self

    def remove_tag(self, tag: str) -> 'Document':
        """
        Remove tag from document.

        Args:
            tag: Tag to remove

        Returns:
            Updated document
        """
        if tag in self.tags:
            new_tags = [t for t in self.tags if t != tag]
            return replace(self, tags=new_tags, updated_at=datetime.now())
        return self

    def update_summary(
        self,
        summary: str,
        short_summary: Optional[str] = None,
        key_topics: Optional[List[str]] = None
    ) -> 'Document':
        """
        Update document summaries.

        Args:
            summary: Full summary
            short_summary: Short summary (optional)
            key_topics: Key topics (optional)

        Returns:
            Updated document
        """
        return replace(
            self,
            summary=summary,
            short_summary=short_summary or summary[:100] + "...",
            key_topics=key_topics or self.key_topics,
            updated_at=datetime.now()
        )

    def mark_accessed(self) -> 'Document':
        """
        Mark document as accessed (for usage tracking).

        Returns:
            Updated document
        """
        return replace(
            self,
            last_accessed_at=datetime.now(),
            access_count=self.access_count + 1
        )

    def set_importance(self, importance: float) -> 'Document':
        """
        Set importance score.

        Args:
            importance: Importance score (0.0-1.0)

        Returns:
            Updated document
        """
        if not 0.0 <= importance <= 1.0:
            raise ValueOutOfRangeError(
                "importance_score",
                importance,
                min_value=0.0,
                max_value=1.0
            )

        return replace(
            self,
            importance_score=importance,
            updated_at=datetime.now()
        )

    def set_quality_rating(self, rating: float) -> 'Document':
        """
        Set quality rating.

        Args:
            rating: Quality rating (0.0-1.0)

        Returns:
            Updated document
        """
        if not 0.0 <= rating <= 1.0:
            raise ValueOutOfRangeError(
                "quality_rating",
                rating,
                min_value=0.0,
                max_value=1.0
            )

        return replace(
            self,
            quality_rating=rating,
            updated_at=datetime.now()
        )

    def add_metadata(self, key: str, value: Any) -> 'Document':
        """
        Add metadata to document.

        Args:
            key: Metadata key
            value: Metadata value

        Returns:
            Updated document
        """
        new_metadata = self.metadata_json.copy()
        new_metadata[key] = value

        return replace(
            self,
            metadata_json=new_metadata,
            updated_at=datetime.now()
        )

    # ========================================================================
    # QUERY METHODS
    # ========================================================================

    def is_processed(self) -> bool:
        """Check if document is successfully processed."""
        return self.processing_status == ProcessingStatus.COMPLETED

    def is_processing(self) -> bool:
        """Check if document is currently processing."""
        return self.processing_status == ProcessingStatus.PROCESSING

    def is_failed(self) -> bool:
        """Check if document processing failed."""
        return self.processing_status == ProcessingStatus.FAILED

    def is_archived(self) -> bool:
        """Check if document is archived."""
        return self.processing_status == ProcessingStatus.ARCHIVED

    def is_ready_for_rag(self) -> bool:
        """Check if document is ready for RAG retrieval."""
        return (
            self.processing_status == ProcessingStatus.COMPLETED
            and self.total_chunks > 0
        )

    def is_important(self, threshold: float = 0.7) -> bool:
        """Check if document is important."""
        return self.importance_score >= threshold

    def is_high_quality(self, threshold: float = 0.7) -> bool:
        """Check if document is high quality."""
        return self.quality_rating >= threshold

    def is_about_david(self) -> bool:
        """Check if document is about David."""
        return self.category == DocumentCategory.DAVID

    def is_angela_core(self) -> bool:
        """Check if document is Angela's core knowledge."""
        return self.category in (
            DocumentCategory.ANGELA_CORE,
            DocumentCategory.ANGELA_PERSONALITY,
            DocumentCategory.ANGELA_MEMORIES
        )

    def has_embedding(self) -> bool:
        """Check if document has embedding."""
        return self.embedding is not None and len(self.embedding) == 384

    def has_been_accessed(self) -> bool:
        """Check if document has been accessed at least once."""
        return self.access_count > 0

    def days_since_accessed(self) -> Optional[int]:
        """Calculate days since last access."""
        if self.last_accessed_at is None:
            return None
        return (datetime.now() - self.last_accessed_at).days

    def get_file_size_mb(self) -> float:
        """Get file size in megabytes."""
        return self.file_size_bytes / (1024 * 1024)

    # ========================================================================
    # DOMAIN EVENTS
    # ========================================================================

    def raise_event(self, event: Any):
        """Raise domain event."""
        self._events.append(event)

    def get_events(self) -> List[Any]:
        """Get and clear domain events."""
        events = self._events.copy()
        self._events.clear()
        return events

    # ========================================================================
    # REPRESENTATION
    # ========================================================================

    def __str__(self) -> str:
        """String representation."""
        return f"Document({self.title}, {self.processing_status.value}, chunks={self.total_chunks})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "title": self.title,
            "file_path": self.file_path,
            "file_type": self.file_type.value,
            "file_size_mb": self.get_file_size_mb(),
            "category": self.category.value,
            "tags": self.tags,
            "author": self.author,
            "summary": self.summary,
            "short_summary": self.short_summary,
            "key_topics": self.key_topics,
            "total_chunks": self.total_chunks,
            "processing_status": self.processing_status.value,
            "processing_error": self.processing_error,
            "access_count": self.access_count,
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            "days_since_accessed": self.days_since_accessed(),
            "importance_score": self.importance_score,
            "quality_rating": self.quality_rating,
            "has_embedding": self.has_embedding(),
            "is_ready_for_rag": self.is_ready_for_rag(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


# ============================================================================
# DOCUMENT CHUNK ENTITY
# ============================================================================

@dataclass(frozen=False)
class DocumentChunk:
    """
    Document chunk entity - represents a semantic chunk for RAG retrieval.

    Documents are split into chunks for:
    - Efficient embedding and indexing
    - Semantic retrieval with vector similarity
    - Context-aware chunk selection
    - Navigation between related chunks

    Invariants:
    - content must not be empty
    - token_count must be positive
    - importance_score must be 0.0-1.0
    - embedding must be 384 dimensions if provided
    - chunk_index must be non-negative

    Business Rules:
    - Chunks maintain order via chunk_index
    - Chunks link to previous/next for context
    - Important chunks (high importance_score) prioritized in retrieval
    - Section titles help with context understanding
    """

    # Core content (required, no defaults)
    content: str
    document_id: UUID

    # Identity (with defaults)
    id: UUID = field(default_factory=uuid4)

    # Position in document
    chunk_index: int = 0
    page_number: Optional[int] = None
    section_title: Optional[str] = None

    # Content metrics
    token_count: int = 0
    importance_score: float = 0.5  # 0.0-1.0 scale

    # Embedding for semantic search
    embedding: Optional[List[float]] = None

    # Navigation links
    prev_chunk_id: Optional[UUID] = None
    next_chunk_id: Optional[UUID] = None

    # Metadata
    metadata_json: Dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)

    # Domain Events
    _events: List[Any] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        """Validate entity invariants."""
        self._validate()

    # ========================================================================
    # VALIDATION
    # ========================================================================

    def _validate(self):
        """
        Validate all business rules and invariants.

        Raises:
            InvalidInputError: If input is invalid
            ValueOutOfRangeError: If value is out of range
            BusinessRuleViolationError: If business rule is violated
        """
        # Content cannot be empty
        if not self.content or not self.content.strip():
            raise InvalidInputError(
                "content",
                self.content,
                "Chunk content cannot be empty"
            )

        # Token count must be positive
        if self.token_count < 0:
            raise ValueOutOfRangeError(
                "token_count",
                self.token_count,
                min_value=0
            )

        # Importance score must be 0.0-1.0
        if not 0.0 <= self.importance_score <= 1.0:
            raise ValueOutOfRangeError(
                "importance_score",
                self.importance_score,
                min_value=0.0,
                max_value=1.0
            )

        # Chunk index must be non-negative
        if self.chunk_index < 0:
            raise ValueOutOfRangeError(
                "chunk_index",
                self.chunk_index,
                min_value=0
            )

        # Embedding must be 384 dimensions
        if self.embedding is not None:
            if len(self.embedding) != 384:
                raise BusinessRuleViolationError(
                    "Embedding dimension must be 384",
                    details=f"Got {len(self.embedding)} dimensions"
                )

    # ========================================================================
    # FACTORY METHODS
    # ========================================================================

    @classmethod
    def create_from_text(
        cls,
        content: str,
        document_id: UUID,
        chunk_index: int,
        section_title: Optional[str] = None,
        page_number: Optional[int] = None
    ) -> 'DocumentChunk':
        """
        Factory: Create chunk from text content.

        Args:
            content: Chunk content
            document_id: Parent document ID
            chunk_index: Position in document
            section_title: Section title (optional)
            page_number: Page number (optional)

        Returns:
            New document chunk
        """
        # Estimate token count (rough approximation)
        token_count = len(content.split())

        return cls(
            content=content,
            document_id=document_id,
            chunk_index=chunk_index,
            section_title=section_title,
            page_number=page_number,
            token_count=token_count
        )

    # ========================================================================
    # BUSINESS LOGIC
    # ========================================================================

    def add_embedding(self, embedding: List[float]) -> 'DocumentChunk':
        """
        Add vector embedding to chunk.

        Args:
            embedding: 384-dim vector

        Returns:
            Updated chunk
        """
        if len(embedding) != 384:
            raise BusinessRuleViolationError(
                "Embedding dimension must be 384",
                details=f"Got {len(embedding)} dimensions"
            )

        return replace(self, embedding=embedding)

    def set_importance(self, importance: float) -> 'DocumentChunk':
        """
        Set importance score.

        Args:
            importance: Importance score (0.0-1.0)

        Returns:
            Updated chunk
        """
        if not 0.0 <= importance <= 1.0:
            raise ValueOutOfRangeError(
                "importance_score",
                importance,
                min_value=0.0,
                max_value=1.0
            )

        return replace(self, importance_score=importance)

    def link_prev(self, prev_id: UUID) -> 'DocumentChunk':
        """
        Link to previous chunk.

        Args:
            prev_id: Previous chunk ID

        Returns:
            Updated chunk
        """
        return replace(self, prev_chunk_id=prev_id)

    def link_next(self, next_id: UUID) -> 'DocumentChunk':
        """
        Link to next chunk.

        Args:
            next_id: Next chunk ID

        Returns:
            Updated chunk
        """
        return replace(self, next_chunk_id=next_id)

    def add_metadata(self, key: str, value: Any) -> 'DocumentChunk':
        """
        Add metadata to chunk.

        Args:
            key: Metadata key
            value: Metadata value

        Returns:
            Updated chunk
        """
        new_metadata = self.metadata_json.copy()
        new_metadata[key] = value

        return replace(self, metadata_json=new_metadata)

    # ========================================================================
    # QUERY METHODS
    # ========================================================================

    def has_embedding(self) -> bool:
        """Check if chunk has embedding."""
        return self.embedding is not None and len(self.embedding) == 384

    def is_important(self, threshold: float = 0.7) -> bool:
        """Check if chunk is important."""
        return self.importance_score >= threshold

    def has_prev_chunk(self) -> bool:
        """Check if chunk has previous chunk."""
        return self.prev_chunk_id is not None

    def has_next_chunk(self) -> bool:
        """Check if chunk has next chunk."""
        return self.next_chunk_id is not None

    def get_content_preview(self, length: int = 100) -> str:
        """
        Get preview of content.

        Args:
            length: Preview length (default: 100)

        Returns:
            Content preview with ellipsis if truncated
        """
        if len(self.content) <= length:
            return self.content

        return self.content[:length-3] + "..."

    # ========================================================================
    # DOMAIN EVENTS
    # ========================================================================

    def raise_event(self, event: Any):
        """Raise domain event."""
        self._events.append(event)

    def get_events(self) -> List[Any]:
        """Get and clear domain events."""
        events = self._events.copy()
        self._events.clear()
        return events

    # ========================================================================
    # REPRESENTATION
    # ========================================================================

    def __str__(self) -> str:
        """String representation."""
        preview = self.get_content_preview(50)
        return f"DocumentChunk(index={self.chunk_index}, tokens={self.token_count}, {preview})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "document_id": str(self.document_id),
            "content": self.content,
            "content_preview": self.get_content_preview(100),
            "chunk_index": self.chunk_index,
            "page_number": self.page_number,
            "section_title": self.section_title,
            "token_count": self.token_count,
            "importance_score": self.importance_score,
            "has_embedding": self.has_embedding(),
            "prev_chunk_id": str(self.prev_chunk_id) if self.prev_chunk_id else None,
            "next_chunk_id": str(self.next_chunk_id) if self.next_chunk_id else None,
            "created_at": self.created_at.isoformat()
        }
