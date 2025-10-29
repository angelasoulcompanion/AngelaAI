"""
Document Management API Endpoints
Handles document upload, processing, and RAG operations
"""

from fastapi import APIRouter, File, UploadFile, Form, Query, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
import logging
import asyncio
from pathlib import Path
import json

# Import services
from angela_core.services.document_processor import DocumentProcessor
from angela_core.services.rag_retrieval_service import RAGRetrievalService
from angela_core.database import db

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
# Endpoint Helpers
# ===============================================

async def get_db_connection():
    """Get database connection pool"""
    try:
        return db
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")


# ===============================================
# Document Management Endpoints
# ===============================================

@router.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    category: str = Form("general"),
    tags: Optional[str] = Form(None)
):
    """Upload and process a document"""

    try:
        logger.info(f"📤 Uploading document: {file.filename}")

        # Parse tags
        tag_list = []
        if tags:
            tag_list = [t.strip() for t in tags.split(',')]

        # Save file temporarily
        file_path = f"/tmp/{file.filename}"
        content = await file.read()

        with open(file_path, 'wb') as f:
            f.write(content)

        # Get database connection
        db_conn = await get_db_connection()

        # Process document
        processor = DocumentProcessor(db_conn)
        result = await processor.process_document(
            file_path=file_path,
            title=title or file.filename,
            category=category,
            tags=tag_list
        )

        if result['success']:
            return {
                'success': True,
                'message': 'Document processed successfully',
                'data': result
            }
        else:
            raise HTTPException(status_code=400, detail=result['error'])

    except Exception as e:
        logger.error(f"❌ Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/documents/batch-upload")
async def batch_upload_documents(
    files: List[UploadFile] = File(...),
    category: str = Form("general"),
    tags: Optional[str] = Form(None)
):
    """Upload and process multiple documents"""

    try:
        logger.info(f"📤 Batch uploading {len(files)} documents")
        logger.info(f"📁 Files: {[f.filename for f in files]}")
        logger.info(f"📂 Category: {category}")
        logger.info(f"🏷️  Tags: {tags}")

        # Parse tags
        tag_list = []
        if tags:
            tag_list = [t.strip() for t in tags.split(',')]

        # Save files temporarily
        file_paths = []
        for file in files:
            file_path = f"/tmp/{file.filename}"
            logger.info(f"💾 Saving {file.filename} to {file_path}")
            content = await file.read()
            logger.info(f"📏 File size: {len(content)} bytes")
            with open(file_path, 'wb') as f:
                f.write(content)
            file_paths.append((file_path, file.filename))

        # Get database connection
        logger.info("🔌 Connecting to database...")
        db_conn = await get_db_connection()

        # Batch process documents
        logger.info("⚙️  Creating DocumentProcessor...")
        processor = DocumentProcessor(db_conn)
        results = []

        for file_path, filename in file_paths:
            logger.info(f"🔄 Processing {filename}...")
            result = await processor.process_document(
                file_path=file_path,
                title=filename,
                category=category,
                tags=tag_list
            )
            logger.info(f"📊 Result for {filename}: {result}")
            results.append(result)

        successful = [r for r in results if r.get('success')]
        failed = [r for r in results if not r.get('success')]

        logger.info(f"✅ Batch upload complete: {len(successful)} successful, {len(failed)} failed")

        response = {
            'success': True,
            'total': len(files),
            'successful': len(successful),
            'failed': len(failed),
            'results': results
        }
        logger.info(f"📤 Returning response: {response}")
        return response

    except Exception as e:
        logger.error(f"❌ Batch upload error: {e}")
        import traceback
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/documents")
async def list_documents(
    category: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
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
async def get_document(document_id: UUID):
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
    limit: int = Query(20, ge=1, le=100)
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
async def delete_document(document_id: UUID):
    """Delete a document"""

    try:
        db_conn = await get_db_connection()

        processor = DocumentProcessor(db_conn)
        result = await processor.delete_document(document_id)

        if result['success']:
            return {'success': True, 'message': 'Document deleted'}
        else:
            raise HTTPException(status_code=400, detail=result['error'])

    except Exception as e:
        logger.error(f"❌ Delete document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===============================================
# Search and RAG Endpoints
# ===============================================

@router.post("/api/documents/search")
async def search_documents(request: SearchRequest):
    """Search documents with RAG"""

    try:
        rag_service = RAGRetrievalService(db)
        context = await rag_service.get_rag_context(
            query=request.query,
            top_k=request.top_k,
            search_mode=request.search_mode
        )

        if 'error' in context:
            raise HTTPException(status_code=400, detail=context['error'])

        return {
            'success': True,
            'context': context['context'],
            'results': context['results'],
            'source_count': context['source_count'],
            'sources': context['sources']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/documents/search-feedback")
async def record_search_feedback(
    search_id: UUID,
    was_helpful: bool,
    rating: Optional[int] = None,
    feedback_text: Optional[str] = None
):
    """Record feedback on search results"""

    try:
        rag_service = RAGRetrievalService(db)
        result = await rag_service.record_search_feedback(
            search_id=search_id,
            was_helpful=was_helpful,
            rating=rating,
            feedback_text=feedback_text
        )

        return result

    except Exception as e:
        logger.error(f"❌ Feedback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/documents/analytics")
async def get_rag_analytics(days: int = Query(7, ge=1, le=90)):
    """Get RAG analytics"""

    try:
        rag_service = RAGRetrievalService(db)
        analytics = await rag_service.get_analytics(days=days)

        return {
            'success': True,
            'period_days': days,
            'analytics': analytics
        }

    except Exception as e:
        logger.error(f"❌ Analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/documents/stats")
async def get_all_documents_stats():
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
