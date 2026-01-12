#!/usr/bin/env python3
"""
Document Repository - PostgreSQL Implementation

Handles all data access for Document and DocumentChunk entities.
Manages Angela's RAG document library with chunking and embeddings.
"""

import asyncpg
from typing import Optional, List, Dict, Any
from uuid import UUID

from angela_core.domain import Document, DocumentChunk, ProcessingStatus, FileType, DocumentCategory
from angela_core.domain.interfaces.repositories import IDocumentRepository
from angela_core.infrastructure.persistence.repositories.base_repository import BaseRepository
from angela_core.shared.utils import parse_enum, safe_list, validate_embedding


class DocumentRepository(BaseRepository[Document], IDocumentRepository):
    """
    PostgreSQL repository for Document entity.

    Tables:
    - document_library: Main documents table
    - document_chunks: Document chunks for RAG

    Document table columns:
    - document_id (UUID, PK)
    - title (VARCHAR)
    - file_path (TEXT)
    - content_type (VARCHAR)
    - category (VARCHAR)
    - tags (TEXT[])
    - summary_thai, summary_english (TEXT)
    - total_chunks (INTEGER)
    - processing_status (VARCHAR)
    - metadata (JSONB)
    - created_at, updated_at, last_accessed (TIMESTAMP)
    - access_count (INTEGER)

    Chunk table columns:
    - chunk_id (UUID, PK)
    - document_id (UUID, FK)
    - chunk_index (INTEGER)
    - content (TEXT)
    - embedding (VECTOR(768))
    - page_number (INTEGER)
    - section_title (VARCHAR)
    - importance_score (DOUBLE PRECISION)
    - metadata (JSONB)
    - created_at (TIMESTAMP)
    """

    def __init__(self, db):
        """Initialize repository."""
        super().__init__(
            db=db,
            table_name="document_library",
            primary_key_column="document_id"
        )
        self.chunks_table = "document_chunks"

    # ========================================================================
    # ROW TO ENTITY CONVERSION - DOCUMENT
    # ========================================================================

    def _row_to_entity(self, row: asyncpg.Record) -> Document:
        """Convert database row to Document entity."""
        # Parse file_type from content_type
        file_type = FileType.OTHER
        if row.get('content_type'):
            content_type = row['content_type'].lower()
            if 'pdf' in content_type:
                file_type = FileType.PDF
            elif 'markdown' in content_type or content_type == 'md':
                file_type = FileType.MARKDOWN
            elif 'text' in content_type or content_type == 'txt':
                file_type = FileType.TEXT
            elif 'json' in content_type:
                file_type = FileType.JSON
            elif 'html' in content_type:
                file_type = FileType.HTML

        # Parse enums with DRY utilities
        category = parse_enum(row.get('category'), DocumentCategory, DocumentCategory.OTHER)
        status = parse_enum(row.get('processing_status'), ProcessingStatus, ProcessingStatus.PENDING)

        # Parse tags with DRY utility
        tags = safe_list(row.get('tags'))

        # Get summaries
        summary = row.get('summary_english') or row.get('summary_thai') or "Document summary pending"
        short_summary = summary[:200] + "..." if len(summary) > 200 else summary

        return Document(
            title=row['title'],
            file_path=row.get('file_path', ''),
            id=row['document_id'],
            file_type=file_type,
            file_size_bytes=0,  # Not in DB
            category=category,
            tags=tags,
            author=row.get('uploaded_by'),
            summary=summary,
            short_summary=short_summary,
            key_topics=[],  # Not in DB
            total_chunks=row.get('total_chunks', 0),
            processing_status=status,
            processing_error=None,  # Not in DB
            last_accessed_at=row.get('last_accessed'),
            access_count=row.get('access_count', 0),
            importance_score=0.5,  # Not in DB
            quality_rating=0.7,  # Not in DB
            embedding=None,  # Not in DB
            metadata_json=dict(row.get('metadata', {})),
            created_at=row['created_at'],
            updated_at=row.get('updated_at', row['created_at'])
        )

    def _entity_to_dict(self, entity: Document) -> Dict[str, Any]:
        """
        Convert Document entity to database row dict.

        Args:
            entity: Document entity

        Returns:
            Dictionary for database insert/update
        """
        # Determine content_type from file_type
        content_type_map = {
            FileType.PDF: 'application/pdf',
            FileType.MARKDOWN: 'text/markdown',
            FileType.TEXT: 'text/plain',
            FileType.JSON: 'application/json',
            FileType.HTML: 'text/html',
            FileType.CODE: 'text/plain',
            FileType.OTHER: 'text/plain'
        }

        return {
            'document_id': entity.id,
            'title': entity.title,
            'file_path': entity.file_path,
            'content_type': content_type_map.get(entity.file_type, 'text/plain'),
            'category': entity.category.value,
            'tags': entity.tags,
            'summary_english': entity.summary,
            'total_chunks': entity.total_chunks,
            'processing_status': entity.processing_status.value,
            'metadata': entity.metadata_json,
            'uploaded_by': entity.author or 'Angela',
            'created_at': entity.created_at,
            'updated_at': entity.updated_at,
            'last_accessed': entity.last_accessed_at,
            'access_count': entity.access_count
        }

    # ========================================================================
    # ROW TO ENTITY CONVERSION - DOCUMENT CHUNK
    # ========================================================================

    def _chunk_row_to_entity(self, row: asyncpg.Record) -> DocumentChunk:
        """Convert database row to DocumentChunk entity."""
        # Parse embedding with DRY utility
        embedding = validate_embedding(row.get('embedding'))

        return DocumentChunk(
            content=row['content'],
            document_id=row['document_id'],
            id=row['chunk_id'],
            chunk_index=row.get('chunk_index', 0),
            page_number=row.get('page_number'),
            section_title=row.get('section_title'),
            token_count=row.get('english_word_count', 0) + row.get('thai_word_count', 0),
            importance_score=row.get('importance_score', 0.5),
            embedding=embedding,
            prev_chunk_id=None,  # Not in DB directly
            next_chunk_id=None,  # Not in DB directly
            metadata_json=dict(row.get('metadata', {})),
            created_at=row['created_at']
        )

    def _chunk_entity_to_dict(self, entity: DocumentChunk) -> Dict[str, Any]:
        """
        Convert DocumentChunk entity to database row dict.

        Args:
            entity: DocumentChunk entity

        Returns:
            Dictionary for database insert/update
        """
        return {
            'chunk_id': entity.id,
            'document_id': entity.document_id,
            'chunk_index': entity.chunk_index,
            'content': entity.content,
            'embedding': entity.embedding,
            'page_number': entity.page_number,
            'section_title': entity.section_title,
            'importance_score': entity.importance_score,
            'metadata': entity.metadata_json,
            'created_at': entity.created_at
        }

    # ========================================================================
    # DOCUMENT-SPECIFIC QUERIES
    # ========================================================================

    async def search_by_vector(
        self,
        embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[tuple[Document, float]]:
        """
        Vector similarity search (searches chunks, returns documents).

        Args:
            embedding: Query embedding vector (768 dimensions)
            top_k: Number of top results to return
            filters: Optional filters (category, status, etc.)

        Returns:
            List of (Document, similarity_score) tuples
        """
        # Search chunks first
        chunk_query = f"""
            SELECT document_id, (embedding <=> $1::vector) as distance
            FROM {self.chunks_table}
            WHERE embedding IS NOT NULL
            ORDER BY distance ASC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            chunk_rows = await conn.fetch(chunk_query, embedding, top_k * 2)

        # Get unique document IDs
        doc_ids = list(set([row['document_id'] for row in chunk_rows]))[:top_k]

        if not doc_ids:
            return []

        # Fetch documents
        doc_query = f"""
            SELECT * FROM {self.table_name}
            WHERE document_id = ANY($1::uuid[])
        """

        async with self.db.acquire() as conn:
            doc_rows = await conn.fetch(doc_query, doc_ids)

        # Convert to entities with scores
        results = []
        for doc_row in doc_rows:
            document = self._row_to_entity(doc_row)
            # Get best chunk score for this document
            doc_distance = min(
                [row['distance'] for row in chunk_rows if row['document_id'] == document.id],
                default=1.0
            )
            similarity = 1.0 - float(doc_distance)
            results.append((document, similarity))

        # Sort by similarity
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    async def get_by_category(
        self,
        category: str,
        limit: int = 100
    ) -> List[Document]:
        """Get documents by category."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE category = $1
            ORDER BY created_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, category, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_by_status(
        self,
        status: str,
        limit: int = 100
    ) -> List[Document]:
        """Get documents by processing status."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE processing_status = $1
            ORDER BY created_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, status, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_ready_for_rag(
        self,
        limit: int = 100
    ) -> List[Document]:
        """Get documents ready for RAG (status=completed with chunks)."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE processing_status = 'completed' AND total_chunks > 0
            ORDER BY created_at DESC
            LIMIT $1
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_important(
        self,
        threshold: float = 0.7,
        limit: int = 100
    ) -> List[Document]:
        """Get important documents (importance_score >= threshold)."""
        # Note: importance_score not in DB, so using category filter
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE category IN ('angela_core', 'angela_personality', 'david')
            ORDER BY total_chunks DESC, created_at DESC
            LIMIT $1
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_by_tags(
        self,
        tags: List[str],
        limit: int = 100
    ) -> List[Document]:
        """Get documents by tags (array overlap)."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE tags && $1::text[]
            ORDER BY created_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, tags, limit)

        return [self._row_to_entity(row) for row in rows]

    async def search_by_title(
        self,
        query: str,
        limit: int = 100
    ) -> List[Document]:
        """Search documents by title."""
        search_query = f"""
            SELECT * FROM {self.table_name}
            WHERE title ILIKE $1
            ORDER BY created_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(search_query, f"%{query}%", limit)

        return [self._row_to_entity(row) for row in rows]

    async def get_by_source(
        self,
        source: str,
        limit: int = 100
    ) -> List[Document]:
        """Get documents by source (file path)."""
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE file_path ILIKE $1
            ORDER BY created_at DESC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, f"%{source}%", limit)

        return [self._row_to_entity(row) for row in rows]

    async def batch_create(
        self,
        documents: List[Document]
    ) -> List[Document]:
        """
        Batch insert documents (optimized for imports).

        Args:
            documents: List of documents to insert

        Returns:
            List of created documents
        """
        if not documents:
            return []

        # Convert documents to dicts
        rows = [self._entity_to_dict(doc) for doc in documents]

        # Build bulk insert query
        columns = rows[0].keys()
        placeholders = []
        values = []

        for i, row in enumerate(rows):
            row_placeholders = []
            for j, col in enumerate(columns):
                param_num = i * len(columns) + j + 1
                row_placeholders.append(f"${param_num}")
                values.append(row[col])
            placeholders.append(f"({', '.join(row_placeholders)})")

        query = f"""
            INSERT INTO {self.table_name} ({', '.join(columns)})
            VALUES {', '.join(placeholders)}
            RETURNING *
        """

        async with self.db.acquire() as conn:
            created_rows = await conn.fetch(query, *values)

        return [self._row_to_entity(row) for row in created_rows]

    # ========================================================================
    # DOCUMENT CHUNK METHODS
    # ========================================================================

    async def get_chunk_by_id(self, id: UUID) -> Optional[DocumentChunk]:
        """Get document chunk by ID."""
        query = f"""
            SELECT * FROM {self.chunks_table}
            WHERE chunk_id = $1
        """

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(query, id)

        return self._chunk_row_to_entity(row) if row else None

    async def create_chunk(self, chunk: DocumentChunk) -> DocumentChunk:
        """Save new document chunk."""
        row_dict = self._chunk_entity_to_dict(chunk)

        columns = row_dict.keys()
        placeholders = [f"${i+1}" for i in range(len(columns))]
        values = list(row_dict.values())

        query = f"""
            INSERT INTO {self.chunks_table} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING *
        """

        async with self.db.acquire() as conn:
            created_row = await conn.fetchrow(query, *values)

        return self._chunk_row_to_entity(created_row)

    async def get_chunks_by_document(
        self,
        document_id: UUID,
        limit: int = 1000
    ) -> List[DocumentChunk]:
        """Get all chunks for a document."""
        query = f"""
            SELECT * FROM {self.chunks_table}
            WHERE document_id = $1
            ORDER BY chunk_index ASC
            LIMIT $2
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, document_id, limit)

        return [self._chunk_row_to_entity(row) for row in rows]

    async def get_important_chunks(
        self,
        document_id: UUID,
        threshold: float = 0.7,
        limit: int = 100
    ) -> List[DocumentChunk]:
        """Get important chunks from a document."""
        query = f"""
            SELECT * FROM {self.chunks_table}
            WHERE document_id = $1 AND importance_score >= $2
            ORDER BY importance_score DESC, chunk_index ASC
            LIMIT $3
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, document_id, threshold, limit)

        return [self._chunk_row_to_entity(row) for row in rows]

    async def count_by_status(self, status: str) -> int:
        """Count documents by processing status."""
        query = f"""
            SELECT COUNT(*) FROM {self.table_name}
            WHERE processing_status = $1
        """

        async with self.db.acquire() as conn:
            result = await conn.fetchval(query, status)

        return result or 0

    async def count_chunks(self, document_id: UUID) -> int:
        """Count chunks for a document."""
        query = f"""
            SELECT COUNT(*) FROM {self.chunks_table}
            WHERE document_id = $1
        """

        async with self.db.acquire() as conn:
            result = await conn.fetchval(query, document_id)

        return result or 0
