"""RAG router — Document upload, indexing, and query."""

import logging
import traceback
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from services.rag_service import add_document, search, list_documents, delete_document, WORKSPACE
from services.ollama_service import chat

router = APIRouter(tags=["rag"])
logger = logging.getLogger(__name__)

DOCS_DIR = WORKSPACE / "documents"
DOCS_DIR.mkdir(parents=True, exist_ok=True)


class QueryRequest(BaseModel):
    query: str
    model: str = "llama3.2:3b"
    top_k: int = 5
    system: Optional[str] = None


@router.post("/rag/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and index a document."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename")

    ext = Path(file.filename).suffix.lower()
    if ext not in (".txt", ".md", ".pdf", ".py", ".json", ".csv"):
        raise HTTPException(status_code=400, detail=f"Unsupported format: {ext}")

    try:
        dest = DOCS_DIR / file.filename
        content = await file.read()
        with open(dest, "wb") as f:
            f.write(content)

        doc = add_document(str(dest))

        # Save to Neon (await properly in async context)
        try:
            from services.rag_service import _documents, _chunks, _embeddings
            from services.db_service import save_rag_document, save_rag_chunks
            import numpy as np
            doc_obj = _documents.get(doc["id"])
            if doc_obj:
                from dataclasses import asdict
                await save_rag_document(asdict(doc_obj))
                doc_chunks = [c for c in _chunks if c.doc_id == doc["id"]]
                chunk_indices = [i for i, c in enumerate(_chunks) if c.doc_id == doc["id"]]
                if chunk_indices and _embeddings is not None:
                    doc_embs = _embeddings[chunk_indices]
                    chunks_data = [{"doc_id": c.doc_id, "index": c.index, "text": c.text} for c in doc_chunks]
                    await save_rag_chunks(doc["id"], chunks_data, doc_embs)
                    logger.info(f"Saved {len(doc_chunks)} chunks to Neon for {doc['id']}")
        except Exception as e:
            logger.warning(f"Neon save failed: {e}")

        return doc
    except Exception as e:
        logger.error(f"Upload document error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rag/documents")
async def get_documents():
    """List all indexed documents."""
    docs = list_documents()
    return {"documents": docs, "count": len(docs)}


@router.delete("/rag/documents/{doc_id}")
async def remove_document(doc_id: str):
    """Remove a document from the index."""
    success = delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
    # Delete from Neon
    try:
        from services.db_service import delete_rag_document as neon_delete
        await neon_delete(doc_id)
    except Exception as e:
        logger.warning(f"Neon delete failed: {e}")
    return {"deleted": doc_id}


@router.post("/rag/query")
async def query_rag(req: QueryRequest):
    """Query documents with RAG: retrieve chunks + generate answer."""
    try:
        chunks = search(req.query, top_k=req.top_k)

        if not chunks:
            return {
                "answer": "No documents indexed yet. Upload documents first.",
                "chunks": [],
                "model": req.model,
            }

        context = "\n\n---\n\n".join([
            f"[{c['doc_name']} chunk {c['chunk_index']}]\n{c['chunk_text']}"
            for c in chunks
        ])

        system_prompt = req.system or (
            "You are a helpful assistant. Answer the question based on the provided context. "
            "If the context doesn't contain relevant information, say so."
        )

        messages = [
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {req.query}"}
        ]

        result = await chat(
            model=req.model,
            messages=messages,
            system=system_prompt,
            temperature=0.3,
            max_tokens=2048,
        )
        return {
            "answer": result.get("content", ""),
            "chunks": chunks,
            "model": req.model,
            "tokens_per_second": result.get("tokens_per_second", 0),
        }
    except Exception as e:
        logger.error(f"RAG query error: {traceback.format_exc()}")
        return {
            "answer": f"Error generating answer: {e}",
            "chunks": chunks if 'chunks' in dir() else [],
            "model": req.model,
        }


class IndexFolderRequest(BaseModel):
    folder_path: str


@router.post("/rag/documents/index-folder")
async def index_folder(req: IndexFolderRequest):
    """Index all supported files in a folder."""
    from pathlib import Path as P
    folder = P(req.folder_path)
    if not folder.is_dir():
        raise HTTPException(status_code=400, detail=f"Not a valid directory: {req.folder_path}")

    supported = {".txt", ".md", ".pdf", ".py", ".json", ".csv"}
    indexed = []
    errors = []
    for f in sorted(folder.iterdir()):
        if not f.is_file() or f.suffix.lower() not in supported:
            continue
        try:
            doc = add_document(str(f))
            indexed.append({"filename": f.name, "chunks": doc.get("chunk_count", 0)})
            # Save to Neon
            try:
                from services.rag_service import _documents, _chunks, _embeddings
                from services.db_service import save_rag_document, save_rag_chunks
                from dataclasses import asdict
                import numpy as np
                doc_obj = _documents.get(doc["id"])
                if doc_obj:
                    await save_rag_document(asdict(doc_obj))
                    doc_ch = [c for c in _chunks if c.doc_id == doc["id"]]
                    ch_idx = [i for i, c in enumerate(_chunks) if c.doc_id == doc["id"]]
                    if ch_idx and _embeddings is not None:
                        await save_rag_chunks(doc["id"],
                            [{"doc_id": c.doc_id, "index": c.index, "text": c.text} for c in doc_ch],
                            _embeddings[ch_idx])
            except Exception as ne:
                logger.warning(f"Neon save for {f.name}: {ne}")
        except Exception as e:
            errors.append({"filename": f.name, "error": str(e)})
            logger.error(f"Failed to index {f.name}: {e}")

    return {
        "folder": req.folder_path,
        "indexed": indexed,
        "errors": errors,
        "total_indexed": len(indexed),
        "total_errors": len(errors),
    }


@router.post("/rag/sync-to-neon")
async def sync_to_neon():
    """Push all in-memory RAG data to Neon DB."""
    from services.rag_service import _documents, _chunks, _embeddings
    from services.db_service import save_rag_document, save_rag_chunks
    from dataclasses import asdict
    import numpy as np

    synced_docs = 0
    synced_chunks = 0
    errors = []

    for doc_id, doc in _documents.items():
        try:
            await save_rag_document(asdict(doc))
            # Collect chunks + embeddings for this doc
            doc_chunks = [c for c in _chunks if c.doc_id == doc_id]
            if doc_chunks and _embeddings is not None:
                # Find embedding indices for this doc's chunks
                chunk_indices = [i for i, c in enumerate(_chunks) if c.doc_id == doc_id]
                doc_embeddings = _embeddings[chunk_indices] if chunk_indices else np.array([])
                chunks_data = [{"doc_id": c.doc_id, "index": c.index, "text": c.text} for c in doc_chunks]
                await save_rag_chunks(doc_id, chunks_data, doc_embeddings)
                synced_chunks += len(doc_chunks)
            synced_docs += 1
        except Exception as e:
            errors.append({"doc_id": doc_id, "error": str(e)})
            logger.error(f"Sync doc {doc_id} failed: {e}")

    return {
        "synced_docs": synced_docs,
        "synced_chunks": synced_chunks,
        "errors": errors,
    }


@router.post("/rag/search")
async def search_chunks(req: QueryRequest):
    """Search documents without generating an answer (retrieval only)."""
    try:
        chunks = search(req.query, top_k=req.top_k)
        return {"chunks": chunks, "count": len(chunks)}
    except Exception as e:
        logger.error(f"RAG search error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
