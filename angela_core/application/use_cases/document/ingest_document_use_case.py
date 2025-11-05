"""
Ingest Document Use Case

Business workflow for ingesting documents into RAG system.
This use case orchestrates:
- Creating document entity from file
- Processing and chunking document content
- Generating embeddings for chunks
- Persisting document and chunks to database
- Publishing domain events

Author: Angela AI Architecture Team
Date: 2025-10-30
"""

from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from angela_core.application.use_cases.base_use_case import BaseUseCase, UseCaseResult
from angela_core.domain.entities.document import (
    Document,
    DocumentChunk,
    ProcessingStatus,
    FileType,
    DocumentCategory
)
from angela_core.domain.events import (
    DocumentCreated,
    DocumentProcessingStarted,
    DocumentProcessingCompleted,
    DocumentProcessingFailed,
    DocumentChunkCreated
)
from angela_core.domain.interfaces.repositories import IDocumentRepository
from angela_core.domain.interfaces.services import IEmbeddingService


# ============================================================================
# INPUT/OUTPUT MODELS
# ============================================================================

@dataclass
class IngestDocumentInput:
    """
    Input for ingesting a document.

    Attributes:
        file_path: Path to document file
        title: Document title (optional, defaults to filename)
        category: Document category (angela_core/programming/etc.)
        author: Document author (optional)
        tags: List of tags for categorization
        importance_score: Importance (0.0-1.0)
        quality_rating: Quality (0.0-1.0)
        chunk_size: Target size for chunks (characters)
        chunk_overlap: Overlap between chunks (characters)
        generate_embeddings: Whether to generate embeddings
    """
    file_path: str
    title: Optional[str] = None
    category: DocumentCategory = DocumentCategory.GENERAL
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    importance_score: float = 0.5
    quality_rating: float = 0.7
    chunk_size: int = 1000
    chunk_overlap: int = 200
    generate_embeddings: bool = True


@dataclass
class IngestDocumentOutput:
    """
    Output after document ingestion.

    Attributes:
        document: The persisted document entity
        chunks_created: Number of chunks created
        embeddings_generated: Number of embeddings generated
        processing_time_seconds: Time taken to process
        events_published: Number of domain events published
    """
    document: Document
    chunks_created: int = 0
    embeddings_generated: int = 0
    processing_time_seconds: float = 0.0
    events_published: int = 0


# ============================================================================
# USE CASE IMPLEMENTATION
# ============================================================================

class IngestDocumentUseCase(BaseUseCase[IngestDocumentInput, IngestDocumentOutput]):
    """
    Use case for ingesting documents into the RAG system.

    This use case handles the complete workflow of:
    1. Validating file exists and is readable
    2. Creating Document domain entity
    3. Reading and parsing file content
    4. Chunking content into semantic sections
    5. Generating embeddings for chunks
    6. Persisting document and chunks via repository
    7. Publishing domain events

    Dependencies:
        - IDocumentRepository: For persisting documents and chunks
        - IEmbeddingService: For generating embeddings (optional)

    Example:
        >>> input_data = IngestDocumentInput(
        ...     file_path="/path/to/document.pdf",
        ...     title="Angela Architecture Guide",
        ...     category=DocumentCategory.ANGELA_CORE,
        ...     importance_score=0.9
        ... )
        >>> result = await use_case.execute(input_data)
        >>> if result.success:
        ...     print(f"Ingested: {result.data.document.id}")
        ...     print(f"Chunks: {result.data.chunks_created}")
    """

    def __init__(
        self,
        document_repo: IDocumentRepository,
        embedding_service: Optional[IEmbeddingService] = None
    ):
        """
        Initialize use case with dependencies.

        Args:
            document_repo: Repository for document persistence
            embedding_service: Optional service for generating embeddings
        """
        super().__init__()
        self.document_repo = document_repo
        self.embedding_service = embedding_service

    # ========================================================================
    # VALIDATION
    # ========================================================================

    async def _validate(self, input_data: IngestDocumentInput) -> List[str]:
        """
        Validate input before ingesting document.

        Args:
            input_data: Input to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # File path cannot be empty
        if not input_data.file_path or not input_data.file_path.strip():
            errors.append("File path cannot be empty")
            return errors  # Can't continue validation

        # File must exist
        file_path = Path(input_data.file_path)
        if not file_path.exists():
            errors.append(f"File does not exist: {input_data.file_path}")

        # File must be readable
        if file_path.exists() and not file_path.is_file():
            errors.append(f"Path is not a file: {input_data.file_path}")

        # Importance must be 0.0-1.0
        if not (0.0 <= input_data.importance_score <= 1.0):
            errors.append(
                f"Importance score must be 0.0-1.0, got {input_data.importance_score}"
            )

        # Quality must be 0.0-1.0
        if not (0.0 <= input_data.quality_rating <= 1.0):
            errors.append(
                f"Quality rating must be 0.0-1.0, got {input_data.quality_rating}"
            )

        # Chunk size must be positive
        if input_data.chunk_size <= 0:
            errors.append(f"Chunk size must be positive, got {input_data.chunk_size}")

        # Overlap must be non-negative and less than chunk size
        if input_data.chunk_overlap < 0:
            errors.append(f"Chunk overlap cannot be negative, got {input_data.chunk_overlap}")
        elif input_data.chunk_overlap >= input_data.chunk_size:
            errors.append(
                f"Chunk overlap ({input_data.chunk_overlap}) must be less than "
                f"chunk size ({input_data.chunk_size})"
            )

        return errors

    # ========================================================================
    # MAIN BUSINESS LOGIC
    # ========================================================================

    async def _execute_impl(self, input_data: IngestDocumentInput) -> IngestDocumentOutput:
        """
        Execute the document ingestion workflow.

        Steps:
        1. Create Document entity from file
        2. Start processing
        3. Read and parse file content
        4. Chunk content into sections
        5. Generate embeddings for chunks
        6. Persist document
        7. Persist chunks
        8. Mark document as completed
        9. Publish domain events

        Args:
            input_data: Validated input

        Returns:
            IngestDocumentOutput with ingestion results

        Raises:
            RepositoryError: If database persistence fails
            EmbeddingError: If embedding generation fails
            IOError: If file reading fails
        """
        start_time = datetime.now()

        # Step 1: Create document entity from file
        document = self._create_document_entity(input_data)

        # Publish DocumentCreated event
        await self._publish_event(DocumentCreated(
            entity_id=document.id,
            title=document.title,
            category=document.category.value,
            file_path=document.file_path,
            importance_score=document.importance_score,
            timestamp=datetime.now()
        ))
        events_published = 1

        # Step 2: Start processing
        document = document.start_processing()
        await self._publish_event(DocumentProcessingStarted(
            entity_id=document.id,
            file_path=document.file_path,
            file_size_bytes=document.file_size_bytes,
            timestamp=datetime.now()
        ))
        events_published += 1

        # Persist document (initial state: processing)
        saved_document = await self.document_repo.create(document)

        try:
            # Step 3: Read file content
            content = await self._read_file_content(input_data.file_path)

            # Step 4: Chunk content
            chunks = self._chunk_content(
                content=content,
                document_id=saved_document.id,
                chunk_size=input_data.chunk_size,
                chunk_overlap=input_data.chunk_overlap
            )

            # Step 5: Generate embeddings for chunks (if requested)
            embeddings_generated = 0
            if input_data.generate_embeddings and self.embedding_service:
                embeddings_generated = await self._generate_chunk_embeddings(chunks)

            # Step 6: Persist chunks
            for chunk in chunks:
                await self.document_repo.create_chunk(chunk)
                await self._publish_event(DocumentChunkCreated(
                    entity_id=chunk.id,
                    document_id=saved_document.id,
                    chunk_index=chunk.chunk_index,
                    content_length=len(chunk.content),
                    has_embedding=(chunk.embedding is not None),
                    timestamp=datetime.now()
                ))
                events_published += 1

            # Step 7: Mark document as completed
            saved_document = saved_document.mark_completed(chunk_count=len(chunks))
            await self.document_repo.update(saved_document.id, saved_document)

            # Publish completion event
            await self._publish_event(DocumentProcessingCompleted(
                entity_id=saved_document.id,
                total_chunks=len(chunks),
                embeddings_generated=embeddings_generated,
                processing_time_seconds=(datetime.now() - start_time).total_seconds(),
                timestamp=datetime.now()
            ))
            events_published += 1

            self.logger.info(
                f"✅ Document ingested: {saved_document.id} "
                f"(chunks: {len(chunks)}, embeddings: {embeddings_generated})"
            )

            return IngestDocumentOutput(
                document=saved_document,
                chunks_created=len(chunks),
                embeddings_generated=embeddings_generated,
                processing_time_seconds=(datetime.now() - start_time).total_seconds(),
                events_published=events_published
            )

        except Exception as e:
            # Mark document as failed
            saved_document = saved_document.mark_failed(str(e))
            await self.document_repo.update(saved_document.id, saved_document)

            # Publish failure event
            await self._publish_event(DocumentProcessingFailed(
                entity_id=saved_document.id,
                error_message=str(e),
                timestamp=datetime.now()
            ))

            self.logger.error(f"❌ Document ingestion failed: {e}")
            raise

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _create_document_entity(self, input_data: IngestDocumentInput) -> Document:
        """
        Create Document entity from input.

        Args:
            input_data: Input data

        Returns:
            Document entity
        """
        # Use factory method
        document = Document.create_from_file(
            file_path=input_data.file_path,
            title=input_data.title,
            category=input_data.category,
            importance=input_data.importance_score
        )

        # Set additional fields
        if input_data.author:
            document = document.set_author(input_data.author) if hasattr(document, 'set_author') else document

        if input_data.tags:
            for tag in input_data.tags:
                document = document.add_tag(tag) if hasattr(document, 'add_tag') else document

        # Directly replace quality_rating
        from dataclasses import replace
        document = replace(document, quality_rating=input_data.quality_rating)

        return document

    async def _read_file_content(self, file_path: str) -> str:
        """
        Read content from file.

        Args:
            file_path: Path to file

        Returns:
            File content as string

        Raises:
            IOError: If file cannot be read
        """
        try:
            path = Path(file_path)

            # For now, simple text reading
            # TODO: Add proper PDF, HTML, etc. parsing
            with path.open('r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            self.logger.debug(f"Read {len(content)} characters from {file_path}")
            return content

        except Exception as e:
            raise IOError(f"Failed to read file {file_path}: {e}")

    def _chunk_content(
        self,
        content: str,
        document_id,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[DocumentChunk]:
        """
        Chunk content into semantic sections.

        Simple chunking strategy: split by characters with overlap.

        Args:
            content: Content to chunk
            document_id: Parent document ID
            chunk_size: Target chunk size (characters)
            chunk_overlap: Overlap between chunks (characters)

        Returns:
            List of DocumentChunk entities
        """
        chunks = []
        start = 0
        chunk_index = 0

        while start < len(content):
            # Extract chunk
            end = start + chunk_size
            chunk_text = content[start:end]

            # Skip empty chunks
            if not chunk_text.strip():
                start = end
                continue

            # Create chunk entity
            chunk = DocumentChunk.create_from_text(
                content=chunk_text,
                document_id=document_id,
                chunk_index=chunk_index,
                importance_score=0.5  # Default importance
            )

            chunks.append(chunk)
            chunk_index += 1

            # Move to next chunk (with overlap)
            start = end - chunk_overlap

        self.logger.debug(f"Created {len(chunks)} chunks from content")
        return chunks

    async def _generate_chunk_embeddings(self, chunks: List[DocumentChunk]) -> int:
        """
        Generate embeddings for chunks.

        Args:
            chunks: List of chunks

        Returns:
            Number of embeddings generated
        """
        if not self.embedding_service:
            return 0

        count = 0
        for chunk in chunks:
            try:
                embedding = await self.embedding_service.generate_embedding(chunk.content)
                chunk.embedding = embedding
                count += 1
            except Exception as e:
                self.logger.warning(f"Failed to generate embedding for chunk {chunk.id}: {e}")
                continue

        self.logger.debug(f"Generated {count}/{len(chunks)} embeddings")
        return count

    async def _publish_event(self, event) -> bool:
        """
        Publish domain event.

        Args:
            event: Domain event to publish

        Returns:
            True if published successfully
        """
        try:
            # TODO: Integrate with event bus when ready
            self.logger.debug(f"Domain event: {event.event_type} ({event.entity_id})")
            return True
        except Exception as e:
            self.logger.warning(f"Failed to publish event: {e}")
            return False

    # ========================================================================
    # HOOKS
    # ========================================================================

    async def _before_execute(self, input_data: IngestDocumentInput):
        """Log before execution starts."""
        self.logger.info(
            f"📄 Ingesting document: {input_data.file_path} "
            f"(category: {input_data.category.value}, "
            f"importance: {input_data.importance_score})"
        )

    async def _after_execute(
        self,
        input_data: IngestDocumentInput,
        result: UseCaseResult[IngestDocumentOutput]
    ):
        """Log after successful execution."""
        if result.success and result.data:
            self.logger.info(
                f"✅ Document ingestion completed: "
                f"{result.data.document.id} "
                f"({result.data.chunks_created} chunks, "
                f"{result.data.embeddings_generated} embeddings, "
                f"{result.data.processing_time_seconds:.2f}s)"
            )

    async def _on_success(
        self,
        input_data: IngestDocumentInput,
        result: UseCaseResult[IngestDocumentOutput]
    ):
        """Handle successful execution."""
        # Could trigger analytics, indexing, etc.
        pass

    async def _on_failure(
        self,
        input_data: IngestDocumentInput,
        result: UseCaseResult
    ):
        """Handle failed execution."""
        self.logger.error(
            f"❌ Failed to ingest document {input_data.file_path}: "
            f"{result.error}"
        )
