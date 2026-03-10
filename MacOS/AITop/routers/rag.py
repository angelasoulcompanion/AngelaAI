"""RAG router — Document upload, indexing, and query."""

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from services.rag_service import add_document, search, list_documents, delete_document, WORKSPACE
from services.ollama_service import chat

router = APIRouter(tags=["rag"])

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

    dest = DOCS_DIR / file.filename
    content = await file.read()
    with open(dest, "wb") as f:
        f.write(content)

    try:
        doc = add_document(str(dest))
        return doc
    except Exception as e:
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
    return {"deleted": doc_id}


@router.post("/rag/query")
async def query_rag(req: QueryRequest):
    """Query documents with RAG: retrieve chunks + generate answer."""
    # Retrieve relevant chunks
    chunks = search(req.query, top_k=req.top_k)

    if not chunks:
        return {
            "answer": "No documents indexed yet. Upload documents first.",
            "chunks": [],
            "model": req.model,
        }

    # Build context from chunks
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

    try:
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
        return {
            "answer": f"Error generating answer: {e}",
            "chunks": chunks,
            "model": req.model,
        }


@router.post("/rag/search")
async def search_chunks(req: QueryRequest):
    """Search documents without generating an answer (retrieval only)."""
    chunks = search(req.query, top_k=req.top_k)
    return {"chunks": chunks, "count": len(chunks)}
