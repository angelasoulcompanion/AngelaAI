"""
RAG Service — Document chunking + vector search using sentence-transformers.
Persists to Neon (angela_aitop schema with pgvector) + local file fallback.
"""

import asyncio
import json
import logging
import os
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

WORKSPACE = Path.home() / ".aitop" / "rag"
WORKSPACE.mkdir(parents=True, exist_ok=True)

INDEX_FILE = WORKSPACE / "index.json"
EMBEDDINGS_FILE = WORKSPACE / "embeddings.npy"

# In-memory document store
_documents: dict[str, "Document"] = {}
_chunks: list["Chunk"] = []
_embeddings: Optional[np.ndarray] = None
_model = None


@dataclass
class Document:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    filename: str = ""
    content: str = ""
    chunk_count: int = 0
    char_count: int = 0
    indexed: bool = False


@dataclass
class Chunk:
    doc_id: str = ""
    index: int = 0
    text: str = ""
    embedding: Optional[np.ndarray] = None


# ============================================================
# Persistence — Neon primary, local file fallback
# ============================================================

def _save_index():
    """Persist to local files (fallback)."""
    try:
        data = {
            "documents": {
                doc_id: {
                    "id": d.id, "filename": d.filename, "content": d.content,
                    "chunk_count": d.chunk_count, "char_count": d.char_count, "indexed": d.indexed,
                }
                for doc_id, d in _documents.items()
            },
            "chunks": [
                {"doc_id": c.doc_id, "index": c.index, "text": c.text}
                for c in _chunks
            ],
        }
        INDEX_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        if _embeddings is not None and len(_embeddings) > 0:
            np.save(str(EMBEDDINGS_FILE), _embeddings)
        elif EMBEDDINGS_FILE.exists():
            EMBEDDINGS_FILE.unlink()
    except Exception as e:
        logger.error(f"Failed to save local index: {e}")


async def _save_doc_to_neon(doc: Document, chunk_objects: list, embeddings_array: np.ndarray):
    """Save document + chunks + embeddings to Neon."""
    try:
        from services.db_service import save_rag_document, save_rag_chunks
        await save_rag_document(asdict(doc))
        chunks_data = [{"doc_id": c.doc_id, "index": c.index, "text": c.text} for c in chunk_objects]
        await save_rag_chunks(doc.id, chunks_data, embeddings_array)
        logger.info(f"Saved doc {doc.id} ({doc.filename}) to Neon: {len(chunks_data)} chunks")
    except Exception as e:
        logger.warning(f"Neon save failed (doc {doc.id}): {e}")


async def _delete_doc_from_neon(doc_id: str):
    """Delete document from Neon."""
    try:
        from services.db_service import delete_rag_document
        await delete_rag_document(doc_id)
    except Exception as e:
        logger.warning(f"Neon delete failed (doc {doc_id}): {e}")


def _load_index():
    """Load from local files on startup."""
    global _embeddings
    if not INDEX_FILE.exists():
        return
    try:
        data = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
        for doc_id, d in data.get("documents", {}).items():
            _documents[doc_id] = Document(**d)
        for c in data.get("chunks", []):
            _chunks.append(Chunk(doc_id=c["doc_id"], index=c["index"], text=c["text"]))
        if EMBEDDINGS_FILE.exists():
            _embeddings = np.load(str(EMBEDDINGS_FILE))
        logger.info(f"Loaded local index: {len(_documents)} docs, {len(_chunks)} chunks")
    except Exception as e:
        logger.error(f"Failed to load local index: {e}")


async def sync_from_cloud():
    """Sync documents + chunks from Supabase on startup (merge with local)."""
    global _embeddings
    try:
        from services.db_service import load_rag_documents, load_rag_chunks
        cloud_docs = await load_rag_documents()
        for d in cloud_docs:
            did = d["id"]
            if did not in _documents:
                _documents[did] = Document(
                    id=did, filename=d["filename"], content=d.get("content", ""),
                    chunk_count=d["chunk_count"], char_count=d["char_count"], indexed=d["indexed"],
                )

        cloud_chunks, cloud_embeddings = await load_rag_chunks()
        if cloud_chunks:
            existing_doc_ids = {c.doc_id for c in _chunks}
            new_chunks = [c for c in cloud_chunks if c["doc_id"] not in existing_doc_ids]
            if new_chunks:
                start_idx = len(_chunks)
                for c in new_chunks:
                    _chunks.append(Chunk(doc_id=c["doc_id"], index=c["index"], text=c["text"]))
                # Merge embeddings
                if cloud_embeddings is not None:
                    cloud_doc_ids = [c["doc_id"] for c in cloud_chunks]
                    new_emb_indices = [
                        i for i, c in enumerate(cloud_chunks) if c["doc_id"] not in existing_doc_ids
                    ]
                    if new_emb_indices:
                        new_embs = cloud_embeddings[new_emb_indices]
                        if _embeddings is not None and len(_embeddings) > 0:
                            _embeddings = np.vstack([_embeddings, new_embs])
                        else:
                            _embeddings = new_embs

        logger.info(f"Synced from Supabase: {len(cloud_docs)} docs, {len(cloud_chunks)} chunks")
    except Exception as e:
        logger.warning(f"Supabase RAG sync failed: {e}")


# Load local index on module init
_load_index()


# ============================================================
# Core functions
# ============================================================

def _get_model():
    """Lazy-load sentence-transformers model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("all-MiniLM-L6-v2")
        except ImportError:
            raise RuntimeError(
                "sentence-transformers not installed. "
                "Run: pip install sentence-transformers"
            )
    return _model


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if end < len(text):
            last_period = chunk.rfind(".")
            last_newline = chunk.rfind("\n")
            break_at = max(last_period, last_newline)
            if break_at > chunk_size // 2:
                chunk = chunk[:break_at + 1]
                end = start + break_at + 1
        chunks.append(chunk.strip())
        start = end - overlap
    return [c for c in chunks if c]


def _read_file(filepath: str) -> str:
    """Read document content based on file type."""
    path = Path(filepath)
    ext = path.suffix.lower()

    if ext in (".txt", ".md", ".py", ".json", ".csv"):
        return path.read_text(encoding="utf-8", errors="ignore")
    elif ext == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            raise RuntimeError("pypdf not installed. Run: pip install pypdf")
    else:
        return path.read_text(encoding="utf-8", errors="ignore")


def add_document(filepath: str) -> dict:
    """Add and index a document."""
    global _embeddings

    content = _read_file(filepath)
    text_chunks = _chunk_text(content)

    doc = Document(
        filename=os.path.basename(filepath),
        content=content[:500],
        chunk_count=len(text_chunks),
        char_count=len(content),
    )

    # Embed chunks
    model = _get_model()
    chunk_objects = []
    embeddings_list = []
    for i, text in enumerate(text_chunks):
        emb = model.encode(text)
        chunk = Chunk(doc_id=doc.id, index=i, text=text, embedding=emb)
        chunk_objects.append(chunk)
        embeddings_list.append(emb)

    # Store in memory
    _documents[doc.id] = doc
    _chunks.extend(chunk_objects)
    doc.indexed = True

    # Rebuild embedding matrix
    new_embs = np.array(embeddings_list)
    if _embeddings is not None and len(_embeddings) > 0:
        _embeddings = np.vstack([_embeddings, new_embs])
    else:
        _embeddings = new_embs

    _save_index()
    return asdict(doc)


def search(query: str, top_k: int = 5) -> list[dict]:
    """Search documents using cosine similarity (in-memory)."""
    global _embeddings
    if _embeddings is None or len(_chunks) == 0:
        return []

    model = _get_model()
    query_emb = model.encode(query)

    # Cosine similarity
    norms = np.linalg.norm(_embeddings, axis=1) * np.linalg.norm(query_emb)
    norms = np.maximum(norms, 1e-8)
    similarities = np.dot(_embeddings, query_emb) / norms

    top_indices = np.argsort(similarities)[-top_k:][::-1]

    results = []
    for idx in top_indices:
        chunk = _chunks[idx]
        doc = _documents.get(chunk.doc_id)
        results.append({
            "chunk_text": chunk.text,
            "score": float(similarities[idx]),
            "doc_id": chunk.doc_id,
            "doc_name": doc.filename if doc else "unknown",
            "chunk_index": chunk.index,
        })
    return results


def list_documents() -> list[dict]:
    """List all indexed documents."""
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "chunk_count": d.chunk_count,
            "char_count": d.char_count,
            "indexed": d.indexed,
        }
        for d in _documents.values()
    ]


def delete_document(doc_id: str) -> bool:
    """Remove a document and its chunks."""
    global _embeddings, _chunks

    if doc_id not in _documents:
        return False

    del _documents[doc_id]

    # Remove chunks and rebuild embeddings
    remaining_chunks = [c for c in _chunks if c.doc_id != doc_id]
    _chunks.clear()
    _chunks.extend(remaining_chunks)

    if _chunks:
        _embeddings = np.array([c.embedding for c in _chunks])
    else:
        _embeddings = None

    _save_index()
    return True
