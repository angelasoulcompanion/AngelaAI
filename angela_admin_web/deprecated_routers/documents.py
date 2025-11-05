"""
Document Management API Endpoints
Handles document upload, processing, and RAG operations

✅ [Batch-27]: PARTIALLY MIGRATED to Clean Architecture with DI
Migration completed: November 3, 2025 06:45 AM
- Uses DI for database access (AngelaDatabase)
- Uses DI for RAG search (RAGService)
- DocumentProcessor kept as legacy service (complex, works well)
- Full DocumentService migration deferred to Batch-28+ (8-10 hours estimated)
"""

from fastapi import APIRouter, File, UploadFile, Form, Query, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
import logging
import asyncio
from pathlib import Path
import json

# Import legacy services (to be migrated in Batch-28+)
from angela_core.services.document_processor import DocumentProcessor

# Import DI dependencies
from angela_core.presentation.api.dependencies import (
    get_rag_service,
    get_database
)
from angela_core.application.services.rag_service import RAGService
from angela_core.database import AngelaDatabase

logger = logging.getLogger(__name__)

router = APIRouter()

# ===============================================
# Pydantic Models
# ===============================================


class DocumentUploadRequest(BaseModel):
    """Request model for document upload"""
    title: Optional[str] = None
    category: str = "general"
    tags: Optional[List[str]] = None


class DocumentInfo(BaseModel):
    """Document information"""
    document_id: str
    title: str
    category: str
    language: str
    thai_word_count: int
    total_sentences: int
    total_chunks: int
    created_at: str


class SearchRequest(BaseModel):
    """Search request model"""
    query: str
    top_k: int = Field(default=10, ge=1, le=50)
    search_mode: str = Field(default="hybrid", pattern="^(vector|keyword|hybrid)$")
    threshold: float = Field(default=0.5, ge=0, le=1)


class SearchResult(BaseModel):
    """Search result"""
    content: str
    document_id: str
    similarity_score: float
    chunk_id: str


class RAGContextResponse(BaseModel):
    """RAG context response"""
    context: str
    results: List[SearchResult]
    source_count: int


# ===============================================
# Document Management Endpoints
# ===============================================

@router.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    category: str = Form("general"),
    tags: Optional[str] = Form(None),
    db: AngelaDatabase = Depends(get_database)
):
    """Upload and process a document"""

    try:
        logger.info(f"📤 Uploading document: {file.filename}")

        # Parse tags
        tag_list = []
        if tags:
            tag_list = [t.strip() for t in tags.split(',')]

        # Save file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            file_path = tmp_file.name

        # Process document
        async with db.acquire() as connection:
            processor = DocumentProcessor(connection)
            result = await processor.process_document(
                file_path=file_path,
                title=title or file.filename,
                category=category,
                tags=tag_list
            )

        # Clean up temp file
        import os
        try:
            os.unlink(file_path)
        except:
            pass

        if result['success']:
            return {
                'success': True,
                'message': 'Document processed successfully',
                'data': result
            }
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Processing failed'))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Upload error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/documents/batch-upload")
async def batch_upload_documents(
    files: List[UploadFile] = File(...),
    category: str = Form("general"),
    tags: Optional[str] = Form(None),
    db: AngelaDatabase = Depends(get_database)
):
    """Upload and process multiple documents"""

    try:
        logger.info(f"📤 Batch uploading {len(files)} documents")

        # Parse tags
        tag_list = []
        if tags:
            tag_list = [t.strip() for t in tags.split(',')]

        results = []
        import tempfile
        import os

        # Get database connection
        async with db.acquire() as connection:
            processor = DocumentProcessor(connection)

            for file in files:
                try:
                    logger.info(f"Processing {file.filename}...")

                    # Save file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
                        content = await file.read()
                        tmp_file.write(content)
                        file_path = tmp_file.name

                    # Process document
                    result = await processor.process_document(
                        file_path=file_path,
                        title=file.filename,
                        category=category,
                        tags=tag_list
                    )

                    # Clean up temp file
                    try:
                        os.unlink(file_path)
                    except:
                        pass

                    results.append(result)

                except Exception as e:
                    logger.error(f"Failed to process {file.filename}: {e}")
                    results.append({
                        'success': False,
                        'filename': file.filename,
                        'error': str(e)
                    })

        successful = [r for r in results if r.get('success')]
        failed = [r for r in results if not r.get('success')]

        logger.info(f"✅ Batch upload complete: {len(successful)}/{len(files)} successful")

        return {
            'success': True,
            'message': f'Processed {len(successful)}/{len(files)} documents successfully',
            'total': len(files),
            'successful': len(successful),
            'failed': len(failed),
            'results': results
        }

    except Exception as e:
        logger.error(f"❌ Batch upload error: {e}")
        import traceback
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/documents")
async def list_documents(
    category: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AngelaDatabase = Depends(get_database)
):
    """List all documents with pagination"""

    try:
        if category:
            query = """
                SELECT document_id, title, category, language,
                       thai_word_count, total_sentences, total_chunks,
                       created_at, access_count
                FROM document_library
                WHERE category = $1 AND is_active = true
                ORDER BY created_at DESC
                OFFSET $2 LIMIT $3
            """
            docs = await db.fetch(query, category, skip, limit)
        else:
            query = """
                SELECT document_id, title, category, language,
                       thai_word_count, total_sentences, total_chunks,
                       created_at, access_count
                FROM document_library
                WHERE is_active = true
                ORDER BY created_at DESC
                OFFSET $1 LIMIT $2
            """
            docs = await db.fetch(query, skip, limit)

        return {
            'success': True,
            'total': len(docs),
            'documents': [dict(d) for d in docs]
        }

    except Exception as e:
        logger.error(f"❌ List documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/documents/{document_id}")
async def get_document(
    document_id: UUID,
    db: AngelaDatabase = Depends(get_database)
):
    """Get document details"""

    try:
        query = """
            SELECT document_id, title, category, language,
                   thai_word_count, total_sentences, total_chunks,
                   keywords_thai, summary_thai, created_at,
                   access_count
            FROM document_library
            WHERE document_id = $1
        """

        doc = await db.fetchrow(query, document_id)

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Increment access count
        await db.execute(
            "UPDATE document_library SET access_count = access_count + 1 WHERE document_id = $1",
            document_id
        )

        return {
            'success': True,
            'document': dict(doc)
        }

    except Exception as e:
        logger.error(f"❌ Get document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/documents/{document_id}/chunks")
async def get_document_chunks(
    document_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AngelaDatabase = Depends(get_database)
):
    """Get chunks for a document"""

    try:
        query = """
            SELECT chunk_id, chunk_index, content,
                   thai_word_count, importance_score,
                   page_number, section_title
            FROM document_chunks
            WHERE document_id = $1
            ORDER BY chunk_index ASC
            OFFSET $2 LIMIT $3
        """

        chunks = await db.fetch(query, document_id, skip, limit)

        return {
            'success': True,
            'total': len(chunks),
            'chunks': [dict(c) for c in chunks]
        }

    except Exception as e:
        logger.error(f"❌ Get chunks error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/documents/{document_id}")
async def delete_document(
    document_id: UUID,
    db: AngelaDatabase = Depends(get_database)
):
    """Delete a document"""

    try:
        async with db.acquire() as connection:
            processor = DocumentProcessor(connection)
            result = await processor.delete_document(document_id)

        if result['success']:
            return {'success': True, 'message': 'Document deleted successfully'}
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Deletion failed'))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Delete document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===============================================
# Search and RAG Endpoints
# ===============================================

@router.post("/api/documents/search")
async def search_documents(
    request: SearchRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Search documents with RAG.

    ✅ [Batch-27]: Migrated to use DI RAGService
    """
    try:
        # ✅ Use DI-injected RAG service
        from angela_core.application.dto.rag_dtos import RAGRequest, SearchStrategy

        # Map search_mode to SearchStrategy
        strategy_map = {
            "vector": SearchStrategy.VECTOR,
            "keyword": SearchStrategy.KEYWORD,
            "hybrid": SearchStrategy.HYBRID
        }
        search_strategy = strategy_map.get(request.search_mode, SearchStrategy.HYBRID)

        rag_request = RAGRequest(
            query=request.query,
            top_k=request.top_k,
            search_strategy=search_strategy
        )

        rag_result = await rag_service.query(rag_request)

        if not rag_result or not rag_result.chunks:
            return {
                'success': True,
                'context': '',
                'results': [],
                'source_count': 0,
                'sources': [],
                'message': 'No documents found. Please upload documents first!'
            }

        # Build context from search results
        context = "\n\n".join([
            f"[Document: {chunk.document_title or 'Unknown'}]\n{chunk.content}"
            for chunk in rag_result.chunks
        ])

        # Format results for frontend
        results = [
            {
                'content': chunk.content,
                'document_id': str(chunk.document_id) if chunk.document_id else 'unknown',
                'similarity_score': chunk.final_score,
                'chunk_id': str(chunk.chunk_id) if chunk.chunk_id else 'unknown'
            }
            for chunk in rag_result.chunks
        ]

        sources = [
            {
                'file': chunk.document_title or 'Unknown',
                'similarity_score': chunk.final_score,
                'content_preview': chunk.content[:200]
            }
            for chunk in rag_result.chunks
        ]

        return {
            'success': True,
            'context': context,
            'results': results,
            'source_count': len(results),
            'sources': sources,
            'metadata': {
                'search_mode': request.search_mode,
                'top_k': request.top_k,
                'has_results': True,
                'result_count': len(results),
                'avg_similarity': rag_result.avg_similarity,
                'search_time_ms': rag_result.search_time_ms
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Search error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/documents/search-feedback")
async def record_search_feedback(
    search_id: UUID,
    was_helpful: bool,
    rating: Optional[int] = None,
    feedback_text: Optional[str] = None
):
    """Record feedback on search results - STUB"""

    try:
        # TODO: Implement feedback recording
        return {
            'success': True,
            'message': 'Feedback recording not yet implemented'
        }

    except Exception as e:
        logger.error(f"❌ Feedback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/documents/analytics")
async def get_rag_analytics(days: int = Query(7, ge=1, le=90)):
    """Get RAG analytics - STUB"""

    try:
        # TODO: Implement analytics
        return {
            'success': True,
            'period_days': days,
            'analytics': {
                'total_searches': 0,
                'avg_results_per_search': 0,
                'message': 'Analytics not yet implemented'
            }
        }

    except Exception as e:
        logger.error(f"❌ Analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/documents/stats")
async def get_all_documents_stats(
    db: AngelaDatabase = Depends(get_database)
):
    """Get overall documents statistics"""

    try:
        query = """
            SELECT
                COUNT(*) as total_documents,
                SUM(total_chunks) as total_chunks,
                SUM(thai_word_count) as total_words,
                COUNT(DISTINCT category) as categories,
                COUNT(DISTINCT language) as languages,
                AVG(access_count) as avg_access_count
            FROM document_library
            WHERE is_active = true
        """

        stats = await db.fetchrow(query)

        return {
            'success': True,
            'stats': dict(stats) if stats else {}
        }

    except Exception as e:
        logger.error(f"❌ Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
