"""
Angela's CogniFy RAG Service
============================
น้อง Angela สามารถค้นหาและตอบคำถามจาก CogniFy documents ได้

Features:
- Semantic search using pgvector + nomic-embed-text
- Keyword search fallback
- RAG with context from multiple chunks
- Support for Thai and English queries

Database: cognify (local PostgreSQL)
Embedding Model: nomic-embed-text (Ollama)

Created with love by Angela 💜
2026-01-03
"""

import asyncio
from typing import Optional
import httpx
import asyncpg


class CognifyRAGService:
    """Angela's RAG Service for CogniFy Documents"""

    def __init__(self):
        self.db_config = {
            "database": "cognify",
            "user": "davidsamanyaporn",
            "host": "localhost",
            "port": 5432
        }
        self.embedding_model = "nomic-embed-text"
        self.ollama_url = "http://localhost:11434"
        self.conn: Optional[asyncpg.Connection] = None

    async def connect(self) -> bool:
        """Connect to CogniFy database"""
        try:
            self.conn = await asyncpg.connect(**self.db_config)
            return True
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            return False

    async def disconnect(self):
        """Disconnect from database"""
        if self.conn:
            await self.conn.close()
            self.conn = None

    async def get_embedding(self, text: str) -> list[float]:
        """Get embedding vector from Ollama"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.ollama_url}/api/embeddings",
                json={"model": self.embedding_model, "prompt": text},
                timeout=30.0
            )
            return response.json()["embedding"]

    async def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        max_distance: float = 0.8
    ) -> list[dict]:
        """
        Semantic search using embeddings

        Args:
            query: Search query
            top_k: Number of results to return
            max_distance: Maximum cosine distance (lower = more similar)

        Returns:
            List of matching chunks with metadata
        """
        if not self.conn:
            await self.connect()

        # Get query embedding
        query_embedding = await self.get_embedding(query)
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        # Search using pgvector
        results = await self.conn.fetch("""
            SELECT
                dc.chunk_id,
                d.document_id,
                d.title,
                d.original_filename,
                dc.page_number,
                dc.content,
                dc.token_count,
                dc.embedding <=> $1::vector AS distance
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.document_id
            WHERE dc.embedding IS NOT NULL
              AND d.is_deleted = false
            ORDER BY dc.embedding <=> $1::vector
            LIMIT $2
        """, embedding_str, top_k)

        return [
            {
                "chunk_id": str(r["chunk_id"]),
                "document_id": str(r["document_id"]),
                "title": r["title"],
                "filename": r["original_filename"],
                "page": r["page_number"],
                "content": r["content"],
                "tokens": r["token_count"],
                "distance": float(r["distance"]),
                "relevance": 1 - float(r["distance"])  # Convert to similarity score
            }
            for r in results
            if float(r["distance"]) <= max_distance
        ]

    async def keyword_search(
        self,
        keyword: str,
        top_k: int = 10
    ) -> list[dict]:
        """
        Keyword search using ILIKE

        Args:
            keyword: Keyword to search
            top_k: Number of results

        Returns:
            List of matching chunks
        """
        if not self.conn:
            await self.connect()

        results = await self.conn.fetch("""
            SELECT
                dc.chunk_id,
                d.document_id,
                d.title,
                d.original_filename,
                dc.page_number,
                dc.content,
                dc.token_count
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.document_id
            WHERE dc.content ILIKE $1
              AND d.is_deleted = false
            ORDER BY dc.page_number
            LIMIT $2
        """, f"%{keyword}%", top_k)

        return [
            {
                "chunk_id": str(r["chunk_id"]),
                "document_id": str(r["document_id"]),
                "title": r["title"],
                "filename": r["original_filename"],
                "page": r["page_number"],
                "content": r["content"],
                "tokens": r["token_count"],
                "relevance": 1.0  # Exact match
            }
            for r in results
        ]

    async def hybrid_search(
        self,
        query: str,
        top_k: int = 5
    ) -> list[dict]:
        """
        Hybrid search combining semantic + keyword

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            Combined and deduplicated results
        """
        # Run both searches
        semantic_results = await self.semantic_search(query, top_k=top_k)
        keyword_results = await self.keyword_search(query, top_k=top_k)

        # Combine and deduplicate
        seen_chunks = set()
        combined = []

        # Prioritize semantic results
        for r in semantic_results:
            if r["chunk_id"] not in seen_chunks:
                seen_chunks.add(r["chunk_id"])
                combined.append(r)

        # Add keyword results not in semantic
        for r in keyword_results:
            if r["chunk_id"] not in seen_chunks:
                seen_chunks.add(r["chunk_id"])
                r["relevance"] = 0.8  # Slightly lower for keyword-only
                combined.append(r)

        # Sort by relevance and return top_k
        combined.sort(key=lambda x: x["relevance"], reverse=True)
        return combined[:top_k]

    async def get_context(
        self,
        query: str,
        max_tokens: int = 2000
    ) -> str:
        """
        Get relevant context for RAG

        Args:
            query: User's question
            max_tokens: Maximum tokens in context

        Returns:
            Formatted context string
        """
        results = await self.hybrid_search(query, top_k=10)

        context_parts = []
        total_tokens = 0

        for r in results:
            tokens = r.get("tokens", 100) or 100
            if total_tokens + tokens > max_tokens:
                break

            context_parts.append(
                f"[{r['title']} - Page {r['page']}]\n{r['content']}"
            )
            total_tokens += tokens

        return "\n\n---\n\n".join(context_parts)

    async def ask(
        self,
        question: str,
        use_llm: bool = True,
        llm_model: str = "llama3.1:8b"
    ) -> dict:
        """
        Ask a question and get RAG-powered answer

        Args:
            question: User's question
            use_llm: Whether to use LLM for answer generation
            llm_model: Ollama model for generation

        Returns:
            Dict with answer, sources, and context
        """
        # Get relevant context
        context = await self.get_context(question)
        sources = await self.hybrid_search(question, top_k=5)

        if not use_llm:
            return {
                "question": question,
                "answer": None,
                "context": context,
                "sources": sources
            }

        # Generate answer using LLM
        # Detect if question is in Thai (Thai Unicode range: U+0E00 to U+0E7F)
        is_thai = any('\u0e00' <= c <= '\u0e7f' for c in question)

        if is_thai:
            prompt = f"""คุณคือ Angela ผู้ช่วย AI ตอบคำถามจาก context ที่ให้มา
ถ้าไม่มีข้อมูลใน context ให้บอกตามตรง

**สำคัญมาก: ตอบเป็นภาษาไทยเท่านั้น ห้ามตอบเป็นภาษาจีน**

Context:
{context}

คำถาม: {question}

ตอบให้กระชับ ชัดเจน ใช้ภาษาไทย"""
        else:
            prompt = f"""You are Angela, a helpful AI assistant. Answer the question based on the provided context.
If the context doesn't contain relevant information, say so honestly.

Context:
{context}

Question: {question}

Answer in a clear, concise manner in English. If discussing technical concepts, provide examples when helpful."""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": llm_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120.0
            )
            answer = response.json().get("response", "")

        return {
            "question": question,
            "answer": answer,
            "context": context,
            "sources": [
                {"title": s["title"], "page": s["page"], "relevance": s["relevance"]}
                for s in sources
            ]
        }

    async def list_documents(self) -> list[dict]:
        """List all available documents"""
        if not self.conn:
            await self.connect()

        results = await self.conn.fetch("""
            SELECT
                document_id,
                title,
                original_filename,
                file_type,
                total_chunks,
                processing_status,
                created_at
            FROM documents
            WHERE is_deleted = false
            ORDER BY title
        """)

        return [
            {
                "id": str(r["document_id"]),
                "title": r["title"],
                "filename": r["original_filename"],
                "type": r["file_type"],
                "chunks": r["total_chunks"],
                "status": r["processing_status"],
                "created": r["created_at"].isoformat() if r["created_at"] else None
            }
            for r in results
        ]

    async def get_document_content(self, document_id: str) -> str:
        """Get full content of a document"""
        if not self.conn:
            await self.connect()

        chunks = await self.conn.fetch("""
            SELECT content, page_number
            FROM document_chunks
            WHERE document_id = $1
            ORDER BY chunk_index
        """, document_id)

        return "\n\n".join([c["content"] for c in chunks])


# Convenience functions for direct use
async def search(query: str, top_k: int = 5) -> list[dict]:
    """Quick semantic search"""
    service = CognifyRAGService()
    await service.connect()
    results = await service.semantic_search(query, top_k)
    await service.disconnect()
    return results


async def ask(question: str) -> dict:
    """Quick RAG query"""
    service = CognifyRAGService()
    await service.connect()
    result = await service.ask(question)
    await service.disconnect()
    return result


# CLI interface
if __name__ == "__main__":
    import sys

    async def main():
        service = CognifyRAGService()

        if not await service.connect():
            print("❌ Failed to connect to database")
            return

        print("💜 Angela's CogniFy RAG Service")
        print("=" * 50)

        # List documents
        docs = await service.list_documents()
        print(f"\n📚 Available Documents: {len(docs)}")
        for d in docs[:5]:
            print(f"   • {d['title']} ({d['chunks']} chunks)")

        # Interactive mode or single query
        if len(sys.argv) > 1:
            question = " ".join(sys.argv[1:])
            print(f"\n🔍 Query: {question}")
            print("-" * 50)

            result = await service.ask(question)

            print(f"\n💬 Answer:\n{result['answer']}")
            print(f"\n📖 Sources:")
            for s in result['sources']:
                print(f"   • {s['title']} (Page {s['page']}) - {s['relevance']:.0%}")
        else:
            print("\n💡 Usage: python cognify_rag_service.py 'your question here'")
            print("   Or import and use CognifyRAGService class")

        await service.disconnect()

    asyncio.run(main())
