"""
RAG Service — Document chunking + vector search using sentence-transformers.
Stores embeddings in-memory with numpy for simplicity (no external DB needed).
"""

import hashlib
import os
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import numpy as np

WORKSPACE = Path.home() / ".aitop" / "rag"
WORKSPACE.mkdir(parents=True, exist_ok=True)

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
        # Try to break at sentence boundary
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
        content=content[:500],  # preview only
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

    # Store
    _documents[doc.id] = doc
    _chunks.extend(chunk_objects)
    doc.indexed = True

    # Rebuild embedding matrix
    if _embeddings is not None and len(_embeddings) > 0:
        _embeddings = np.vstack([_embeddings, np.array(embeddings_list)])
    else:
        _embeddings = np.array(embeddings_list)

    return asdict(doc)


def search(query: str, top_k: int = 5) -> list[dict]:
    """Search documents using cosine similarity."""
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

    return True
