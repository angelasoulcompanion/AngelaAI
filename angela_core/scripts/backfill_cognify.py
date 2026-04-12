#!/usr/bin/env python3
"""
Backfill CogniFy project tables from deep codebase analysis.

Covers: tech_stack, patterns, learnings, schemas, flows,
        technical_decisions, entity_relations

Usage:
    python3 angela_core/scripts/backfill_cognify.py
    python3 angela_core/scripts/backfill_cognify.py --dry-run
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

CODE = "COGNIFY"

# ============================================================
# TECH STACK (exact versions from requirements.txt + package.json)
# ============================================================
TECH_STACK = [
    # Backend
    ("framework", "FastAPI", ">=0.109.0", "Backend API"),
    ("language", "Python", "3.11+", "Backend"),
    ("library", "asyncpg", ">=0.29.0", "Async PostgreSQL driver"),
    ("library", "Pydantic", ">=2.5.0", "Validation + Settings"),
    ("library", "pgvector", ">=0.2.0", "Vector extension for PostgreSQL"),
    ("library", "PyMuPDF", ">=1.23.0", "PDF text extraction"),
    ("library", "pymupdf4llm", ">=0.0.5", "PDF→Markdown conversion"),
    ("library", "python-docx", ">=1.1.0", "DOCX processing"),
    ("library", "openpyxl", ">=3.1.2", "XLSX processing"),
    ("library", "tiktoken", ">=0.5.0", "Token counting"),
    ("library", "pythainlp", ">=4.0.0", "Thai NLP (word segmentation)"),
    ("library", "tenacity", ">=8.2.0", "Retry logic"),
    ("library", "slowapi", ">=0.1.9", "Rate limiting"),
    ("library", "loguru", ">=0.7.2", "Structured logging"),
    ("auth", "python-jose", ">=3.3.0", "JWT (access 30min + refresh 7d)"),
    ("auth", "passlib+bcrypt", None, "Password hashing"),
    ("database", "PostgreSQL", "16", "Main DB + pgvector extension"),
    # Frontend
    ("frontend", "React", "18.2.0", "UI framework"),
    ("language", "TypeScript", "5.2.0", "Frontend type safety"),
    ("tool", "Vite", "7.3.0", "Build tool"),
    ("library", "TanStack Query", "5.17.0", "Server state management"),
    ("library", "Zustand", "4.4.0", "Client state management"),
    ("styling", "Tailwind CSS", "3.4.0", "Utility-first CSS"),
    ("library", "Axios", "1.6.0", "HTTP client"),
    ("library", "Lucide React", "0.303.0", "Icons"),
    ("library", "react-hot-toast", "2.4.1", "Notifications"),
    ("library", "react-markdown", "9.0.1", "Markdown rendering"),
    ("library", "react-router-dom", "6.21.0", "Routing"),
    ("library", "streamdown", "1.6.10", "Streaming markdown"),
    ("library", "react-syntax-highlighter", "16.1.0", "Code display"),
    # AI/ML
    ("ai", "Ollama (Typhoon 4B)", None, "Primary LLM: scb10x/typhoon2.5-qwen3-4b"),
    ("ai", "OpenAI (fallback)", None, "Fallback LLM: gpt-4o"),
    ("embedding", "bge-m3", None, "Primary: 1024 dims, 8192 context, 100+ languages"),
    ("embedding", "mxbai-embed-large", None, "Ollama fallback"),
    ("embedding", "text-embedding-3-small", None, "OpenAI fallback"),
    ("ocr", "Typhoon OCR", None, "scb10x/typhoon-ocr1.5-3b bilingual vision"),
    # Infrastructure
    ("tool", "Docker", None, "docker-compose with pgvector/pgvector:pg16"),
]

# ============================================================
# PATTERNS
# ============================================================
PATTERNS = [
    {
        "name": "RAGSettings SSOT",
        "type": "architecture",
        "description": "Centralized RAGSettings dataclass for all search methods (vector, BM25, hybrid). Parameters: similarity_threshold, max_chunks, search_method, vector_weight(0.6), bm25_weight(0.4), rrf_k(60). All RAG operations respect identical settings.",
        "file_path": "backend/app/services/rag_service.py",
    },
    {
        "name": "Hybrid Search with RRF Fusion",
        "type": "algorithm",
        "description": "Vector + BM25 parallel execution → RRF (Reciprocal Rank Fusion). Formula: score = vector_weight * (1/(k + vector_rank)) + bm25_weight * (1/(k + bm25_rank)). Default: vector=0.6, bm25=0.4, k=60. Fetch top_n=20, re-rank, return top_k=5.",
        "file_path": "backend/app/services/rag_service.py",
    },
    {
        "name": "HyDE (Hypothetical Document Embedding)",
        "type": "algorithm",
        "description": "Generate synthetic answer via LLM before embedding query. Query → LLM generates hypothetical answer → embed enriched text → search. Improves semantic matching by contextualizing queries. HYDE_ENABLED=true.",
        "file_path": "backend/app/services/rag_service.py",
    },
    {
        "name": "Re-ranking Pipeline",
        "type": "algorithm",
        "description": "Fetch RERANK_TOP_N=20 results, pass to LLM re-ranker with original query, re-rank by semantic relevance, return RERANK_RETURN_K=5. Same model as chat LLM.",
        "file_path": "backend/app/services/rag_service.py",
    },
    {
        "name": "Embedding Cache (2-Tier)",
        "type": "performance",
        "description": "In-memory cache (current session speed) + database cache (embedding_cache table, TTL 1h). Key: MD5(text) + model_name. Prevents redundant embedding API calls.",
        "file_path": "backend/app/services/embedding_service.py",
    },
    {
        "name": "Chunking with Overlap",
        "type": "algorithm",
        "description": "500-token chunks with 100-token overlap (20% ratio). Section boundaries respected over fixed token counts. Thai: pythainlp word segmentation + character-based estimation.",
        "file_path": "backend/app/services/chunking_service.py",
    },
    {
        "name": "Prompt Templates Database",
        "type": "architecture",
        "description": "7 default templates in prompt_templates table (RAG Thai/English, Financial Analyst, Summarization, etc.). All chat completions reference template by ID. Variables JSONB with {name, type, required, default}. Prevents prompt drift.",
    },
    {
        "name": "Token Rotation (Family ID)",
        "type": "security",
        "description": "Access token (sessionStorage, 30min) + Refresh token (HttpOnly cookie, 7d). family_id UUID tracks token chain. Proactive 5-min buffer refresh. is_used + is_revoked flags. /logout-all revokes entire family.",
        "file_path": "backend/app/core/security.py",
    },
    {
        "name": "Connector Password Encryption",
        "type": "security",
        "description": "Database connector passwords encrypted with Fernet symmetric encryption at rest. Key from ENCRYPTION_KEY env var. 32 bytes base64. Decrypt on sync, never expose plaintext.",
        "file_path": "backend/app/services/connector_service.py",
    },
    {
        "name": "Status Color Map SSOT",
        "type": "design",
        "description": "statusColorMap in statusColors.ts. Success/Active: green-500/20 + green-400. Warning/Pending: yellow. Info/Processing: blue. Error/Failed: red. Score colors: >=0.7 green, >=0.5 yellow, <0.5 gray.",
        "file_path": "frontend/src/lib/statusColors.ts",
    },
    {
        "name": "Angela Purple Dark Theme",
        "type": "design",
        "description": "Primary: #a855f7(500), #9333ea(600), #7c3aed(700). Secondary: #1e293b(800), #0f172a(900), #020617(950). Font: Inter (sans), JetBrains Mono (code).",
        "file_path": "frontend/tailwind.config.js",
    },
    {
        "name": "Structured JSON RAG Response",
        "type": "architecture",
        "description": "{title, sections[{heading, items[{type: text|fact|list_item, text/label/value}]}], sources_used}. Frontend StructuredResponseRenderer auto-detects JSON vs markdown. Progress: 🔍 ค้นหา → ✨ สร้างคำตอบ → 📊 Result.",
        "file_path": "backend/app/services/chat_service.py",
    },
    {
        "name": "SSE Streaming with Native Fetch",
        "type": "integration",
        "description": "Backend: StreamingResponse(media_type='text/plain'). Frontend: Native fetch (NOT Axios) + ReadableStream + TextDecoder. Separate onChunk/onDone callbacks. Axios doesn't support streaming properly.",
    },
    {
        "name": "Document Factory Method",
        "type": "architecture",
        "description": "Document.create_from_upload(filename, file_type, uploaded_by) — domain entity creates itself with defaults (status=pending, uuid auto). Eliminates manual construction with 15+ fields.",
        "file_path": "backend/app/domain/entities/document.py",
    },
    {
        "name": "API Client Singleton + Interceptors",
        "type": "frontend",
        "description": "Single axios instance with auth interceptor (adds JWT from sessionStorage). 401 response → queue request, auto refresh, retry. Concurrent 401s use lock to prevent multiple refresh calls.",
        "file_path": "frontend/src/services/api.ts",
    },
    {
        "name": "Config with lru_cache",
        "type": "architecture",
        "description": "Settings class loaded once via get_settings() with @lru_cache(). Global settings instance. All config from env vars. DATABASE_POOL_SIZE=10, DATABASE_MAX_OVERFLOW=20.",
        "file_path": "backend/app/core/config.py",
    },
]

# ============================================================
# SCHEMAS
# ============================================================
SCHEMAS = [
    {
        "table_name": "users",
        "schema_type": "table",
        "columns": json.dumps([
            {"name": "user_id", "type": "UUID", "pk": True},
            {"name": "email", "type": "VARCHAR(255)", "unique": True},
            {"name": "password_hash", "type": "VARCHAR(255)"},
            {"name": "full_name", "type": "VARCHAR(255)"},
            {"name": "role", "type": "VARCHAR(50)", "default": "user", "note": "admin, editor, user"},
            {"name": "is_active", "type": "BOOLEAN", "default": True},
            {"name": "last_login_at", "type": "TIMESTAMPTZ"},
            {"name": "created_at", "type": "TIMESTAMPTZ"},
            {"name": "updated_at", "type": "TIMESTAMPTZ"},
        ]),
        "purpose": "User accounts with role-based access (admin/editor/user).",
    },
    {
        "table_name": "documents",
        "schema_type": "table",
        "columns": json.dumps([
            {"name": "document_id", "type": "UUID", "pk": True},
            {"name": "uploaded_by", "type": "UUID", "fk": "users.user_id"},
            {"name": "filename", "type": "VARCHAR(500)"},
            {"name": "original_filename", "type": "VARCHAR(500)"},
            {"name": "file_type", "type": "VARCHAR(50)", "note": "pdf, docx, txt, xlsx, png, jpg"},
            {"name": "file_size_bytes", "type": "BIGINT"},
            {"name": "title", "type": "VARCHAR(500)"},
            {"name": "description", "type": "TEXT"},
            {"name": "page_count", "type": "INTEGER"},
            {"name": "language", "type": "VARCHAR(20)", "default": "en"},
            {"name": "tags", "type": "TEXT[]"},
            {"name": "processing_status", "type": "VARCHAR(50)", "note": "pending→processing→completed→failed"},
            {"name": "processing_step", "type": "VARCHAR(50)", "note": "extracting→chunking→embedding→storing→completed"},
            {"name": "processing_progress", "type": "FLOAT"},
            {"name": "total_chunks", "type": "INTEGER", "default": 0},
            {"name": "is_deleted", "type": "BOOLEAN", "default": False, "note": "Soft delete"},
        ]),
        "purpose": "Uploaded documents with processing pipeline status tracking.",
        "gotchas": "Soft delete via is_deleted flag. processing_step tracks exact pipeline stage.",
    },
    {
        "table_name": "document_chunks",
        "schema_type": "table",
        "columns": json.dumps([
            {"name": "chunk_id", "type": "UUID", "pk": True},
            {"name": "document_id", "type": "UUID", "fk": "documents.document_id ON DELETE CASCADE"},
            {"name": "chunk_index", "type": "INTEGER"},
            {"name": "content", "type": "TEXT"},
            {"name": "page_number", "type": "INTEGER"},
            {"name": "section_title", "type": "VARCHAR(500)"},
            {"name": "token_count", "type": "INTEGER"},
            {"name": "embedding", "type": "VECTOR(768)", "note": "IVFFlat index, lists=100"},
            {"name": "embedding_model", "type": "VARCHAR(100)", "default": "nomic-embed-text"},
        ]),
        "purpose": "Document chunks with vector embeddings for similarity search.",
        "gotchas": "VECTOR(768) indexed with IVFFlat (lists=100, ~90% accuracy for ~1M vectors). Embedding must be string format for pgvector. UNIQUE(document_id, chunk_index).",
    },
    {
        "table_name": "conversations",
        "schema_type": "table",
        "columns": json.dumps([
            {"name": "conversation_id", "type": "UUID", "pk": True},
            {"name": "user_id", "type": "UUID", "fk": "users.user_id"},
            {"name": "session_id", "type": "VARCHAR(255)"},
            {"name": "title", "type": "VARCHAR(500)"},
            {"name": "model_provider", "type": "VARCHAR(50)", "note": "ollama, anthropic, openai"},
            {"name": "model_name", "type": "VARCHAR(255)"},
            {"name": "temperature", "type": "FLOAT", "default": 0.7},
            {"name": "rag_enabled", "type": "BOOLEAN", "default": True},
            {"name": "rag_settings", "type": "JSONB", "note": "Serialized RAGSettings"},
            {"name": "message_count", "type": "INTEGER", "default": 0},
            {"name": "interface", "type": "VARCHAR(100)"},
            {"name": "model_used", "type": "VARCHAR(255)"},
        ]),
        "purpose": "Chat conversations with RAG settings and model tracking.",
    },
    {
        "table_name": "messages",
        "schema_type": "table",
        "columns": json.dumps([
            {"name": "message_id", "type": "UUID", "pk": True},
            {"name": "conversation_id", "type": "UUID", "fk": "conversations.conversation_id ON DELETE CASCADE"},
            {"name": "message_type", "type": "VARCHAR(50)", "note": "user, assistant, system"},
            {"name": "content", "type": "TEXT"},
            {"name": "sources_used", "type": "JSONB", "note": "[{document_id, document_name, page, score}]"},
            {"name": "response_time_ms", "type": "INTEGER"},
        ]),
        "purpose": "Chat messages with source attribution for RAG responses.",
    },
    {
        "table_name": "database_connections",
        "schema_type": "table",
        "columns": json.dumps([
            {"name": "connection_id", "type": "UUID", "pk": True},
            {"name": "created_by", "type": "UUID", "fk": "users.user_id"},
            {"name": "name", "type": "VARCHAR(255)"},
            {"name": "db_type", "type": "VARCHAR(50)", "note": "postgresql, mysql, sqlserver"},
            {"name": "host", "type": "VARCHAR(255)"},
            {"name": "port", "type": "INTEGER"},
            {"name": "database_name", "type": "VARCHAR(255)"},
            {"name": "username", "type": "VARCHAR(255)"},
            {"name": "password_encrypted", "type": "VARCHAR(500)", "note": "Fernet encrypted"},
            {"name": "sync_enabled", "type": "BOOLEAN"},
            {"name": "sync_config", "type": "JSONB", "note": "Table selection, frequency"},
            {"name": "last_sync_status", "type": "VARCHAR(50)", "note": "pending, syncing, completed, failed"},
            {"name": "total_chunks_synced", "type": "INTEGER", "default": 0},
        ]),
        "purpose": "External database connectors with encrypted credentials and sync tracking.",
        "gotchas": "Password Fernet encrypted. Decrypt only at sync time. Never expose plaintext.",
    },
    {
        "table_name": "embedding_cache",
        "schema_type": "table",
        "columns": json.dumps([
            {"name": "cache_id", "type": "UUID", "pk": True},
            {"name": "text_hash", "type": "VARCHAR(32)", "note": "MD5 hash of text"},
            {"name": "embedding", "type": "VECTOR(768)"},
            {"name": "model_name", "type": "VARCHAR(100)"},
            {"name": "expires_at", "type": "TIMESTAMPTZ", "note": "1 hour TTL"},
        ]),
        "purpose": "Embedding cache to prevent redundant API calls. UNIQUE(text_hash, model_name).",
        "gotchas": "TTL 1 hour. Cleanup via expires_at index. Two-tier: in-memory + DB.",
    },
    {
        "table_name": "prompt_templates",
        "schema_type": "table",
        "columns": json.dumps([
            {"name": "template_id", "type": "UUID", "pk": True},
            {"name": "created_by", "type": "UUID", "fk": "users.user_id", "nullable": True},
            {"name": "name", "type": "VARCHAR(255)"},
            {"name": "category", "type": "VARCHAR(50)", "note": "rag, system, summarization, analysis, custom"},
            {"name": "expert_role", "type": "VARCHAR(100)", "note": "financial, legal, technical, data, business"},
            {"name": "template_content", "type": "TEXT"},
            {"name": "variables", "type": "JSONB", "note": "[{name, type, required, default}]"},
            {"name": "language", "type": "VARCHAR(20)", "default": "th"},
            {"name": "is_default", "type": "BOOLEAN", "note": "7 system defaults"},
            {"name": "usage_count", "type": "INTEGER", "default": 0},
            {"name": "version", "type": "INTEGER", "default": 1},
        ]),
        "purpose": "Prompt templates for RAG chat. 7 system defaults. Prevents prompt drift.",
    },
    {
        "table_name": "refresh_tokens",
        "schema_type": "table",
        "columns": json.dumps([
            {"name": "token_id", "type": "UUID", "pk": True},
            {"name": "user_id", "type": "UUID", "fk": "users.user_id ON DELETE CASCADE"},
            {"name": "token_hash", "type": "VARCHAR(255)", "unique": True},
            {"name": "family_id", "type": "UUID", "note": "Rotation chain tracking"},
            {"name": "is_revoked", "type": "BOOLEAN", "default": False},
            {"name": "is_used", "type": "BOOLEAN", "default": False},
            {"name": "expires_at", "type": "TIMESTAMPTZ"},
            {"name": "user_agent", "type": "VARCHAR(500)"},
            {"name": "ip_address", "type": "INET"},
        ]),
        "purpose": "JWT refresh tokens with rotation tracking (family_id) and security flags.",
        "gotchas": "Check is_used BEFORE accepting token. Mark used immediately. family_id links rotation chain. /logout-all revokes entire family.",
    },
    {
        "table_name": "announcements",
        "schema_type": "table",
        "columns": json.dumps([
            {"name": "announcement_id", "type": "UUID", "pk": True},
            {"name": "title", "type": "VARCHAR(500)"},
            {"name": "content", "type": "TEXT", "note": "Markdown format"},
            {"name": "cover_image_url", "type": "VARCHAR(500)"},
            {"name": "category", "type": "VARCHAR(50)", "note": "general, important, update, event"},
            {"name": "is_pinned", "type": "BOOLEAN"},
            {"name": "is_published", "type": "BOOLEAN"},
            {"name": "published_at", "type": "TIMESTAMPTZ"},
        ]),
        "purpose": "System announcements with pin/publish workflow. Content in Markdown.",
    },
]

# ============================================================
# ENTITY RELATIONS
# ============================================================
RELATIONS = [
    ("users", "documents", "1:N", "users.user_id = documents.uploaded_by", "User uploads documents"),
    ("users", "conversations", "1:N", "users.user_id = conversations.user_id", "User owns conversations"),
    ("users", "database_connections", "1:N", "users.user_id = database_connections.created_by", "User creates connectors"),
    ("users", "refresh_tokens", "1:N", "users.user_id = refresh_tokens.user_id ON DELETE CASCADE", "User has refresh tokens"),
    ("users", "prompt_templates", "1:N", "users.user_id = prompt_templates.created_by", "User creates templates (nullable for defaults)"),
    ("users", "announcements", "1:N", "users.user_id = announcements.created_by", "User creates announcements"),
    ("documents", "document_chunks", "1:N", "documents.document_id = document_chunks.document_id ON DELETE CASCADE", "Document has chunks (cascade delete)"),
    ("conversations", "messages", "1:N", "conversations.conversation_id = messages.conversation_id ON DELETE CASCADE", "Conversation has messages (cascade delete)"),
]

# ============================================================
# LEARNINGS
# ============================================================
LEARNINGS = [
    {
        "type": "gotcha", "category": "pgvector",
        "title": "IVFFlat lists parameter affects accuracy vs speed",
        "insight": "lists=100 provides ~90% accuracy for ~1M vectors. Too few=poor accuracy, too many=slow building. Scale with data size.",
    },
    {
        "type": "gotcha", "category": "embedding",
        "title": "Embedding model dimension mismatch crashes index",
        "insight": "DB VECTOR(768) but bge-m3 outputs 1024 dims. Must verify embedding_dimension matches model output before index creation. Dimension mismatch = silent corruption or crash.",
    },
    {
        "type": "gotcha", "category": "auth",
        "title": "Refresh token reuse bypass via race condition",
        "insight": "Check is_used flag BEFORE accepting token, mark used immediately. family_id rotation not enforced before comparison can allow replay.",
    },
    {
        "type": "gotcha", "category": "auth",
        "title": "sessionStorage XSS vulnerability mitigated by short TTL",
        "insight": "Access token in sessionStorage is XSS-vulnerable. Mitigation: refresh token in HttpOnly cookie + 30min access TTL + 5-min proactive refresh buffer.",
    },
    {
        "type": "gotcha", "category": "rag",
        "title": "RRF score=0 when single method returns no results",
        "insight": "Hybrid search RRF formula needs default rank (999999) when vector_rank or bm25_rank is missing. Without fallback, score=0 for valid results.",
    },
    {
        "type": "gotcha", "category": "nlp",
        "title": "Thai token counting requires pythainlp",
        "insight": "Word-based token estimation fails for Thai (no space delimiters). Use pythainlp word segmentation + len(words) + len(thai_chars) // 2.",
    },
    {
        "type": "gotcha", "category": "database",
        "title": "Partial vector inserts leave orphan chunks",
        "insight": "Chunking succeeds but embedding fails mid-transaction → chunks without embeddings. Use two-phase commits or retry logic with idempotency keys.",
    },
    {
        "type": "gotcha", "category": "docker",
        "title": "pgvector extension race condition on first run",
        "insight": "CREATE EXTENSION IF NOT EXISTS vector must run BEFORE migrations. Docker entrypoint handles this. Use pgvector/pgvector:pg16 official image.",
    },
    {
        "type": "technical", "category": "performance",
        "title": "CogniFy asyncpg pool sizing",
        "insight": "pool_size=10, max_overflow=20. Long-running embedding queries can exhaust pool. Monitor active connections, use context managers for cleanup.",
    },
    {
        "type": "technical", "category": "search",
        "title": "Hybrid search weight tuning",
        "insight": "Vector=0.6, BM25=0.4, RRF k=60 is optimal default. Higher vector weight for semantic queries, higher BM25 for exact keyword matches. Re-rank top 20 → return 5.",
    },
]

# ============================================================
# TECHNICAL DECISIONS
# ============================================================
DECISIONS = [
    {
        "title": "Hybrid Search (Vector + BM25 + RRF) over Pure Vector",
        "category": "architecture",
        "context": "Pure vector search misses exact keyword matches, pure BM25 misses semantic meaning",
        "decision_made": "Parallel vector + BM25 execution with RRF fusion (vector_weight=0.6, bm25=0.4, k=60)",
        "reasoning": "Best of both worlds. RRF is rank-based (not score-based) so it handles different score scales naturally.",
    },
    {
        "title": "HyDE for Query Enrichment",
        "category": "architecture",
        "context": "Short user queries produce poor embeddings for similarity search",
        "decision_made": "Generate hypothetical answer via LLM before embedding, use enriched text for search",
        "reasoning": "Hypothetical document is closer to actual documents in embedding space than raw query.",
    },
    {
        "title": "LLM Re-ranking Pipeline",
        "category": "architecture",
        "context": "Top search results not always most relevant for user intent",
        "decision_made": "Fetch top_n=20 with broad search, re-rank with LLM by semantic relevance, return top_k=5",
        "reasoning": "Balances recall (fetch many) with precision (re-rank few). LLM understands intent better than cosine similarity.",
    },
    {
        "title": "Access Token in sessionStorage + Refresh in HttpOnly Cookie",
        "category": "security",
        "context": "Need balance between API convenience and XSS protection",
        "decision_made": "Access token (30min, sessionStorage) + Refresh token (7d, HttpOnly cookie) with family-based rotation",
        "reasoning": "Short-lived access = low XSS impact. HttpOnly refresh = no JS access. Family rotation detects token theft.",
    },
    {
        "title": "2-Tier Embedding Cache (Memory + DB)",
        "category": "performance",
        "context": "Embedding API calls are expensive (time + cost for OpenAI fallback)",
        "decision_made": "In-memory cache for session speed + database embedding_cache table (1h TTL) for persistence",
        "reasoning": "Prevents redundant calls. MD5(text)+model_name as cache key. ~90% hit rate for repeated queries.",
    },
    {
        "title": "Prompt Templates in Database (not Code)",
        "category": "architecture",
        "context": "Prompt engineering requires iteration without code deploys",
        "decision_made": "7 default templates stored in prompt_templates table with variables JSONB and versioning",
        "reasoning": "Admin can edit prompts via UI without developer intervention. Version tracking prevents regression.",
    },
    {
        "title": "500-token Chunks with 20% Overlap",
        "category": "architecture",
        "context": "Need optimal chunk size for RAG retrieval quality",
        "decision_made": "500 tokens per chunk, 100 tokens overlap, respect section boundaries",
        "reasoning": "500 tokens balances context completeness with retrieval precision. 20% overlap ensures context continuity across boundaries.",
    },
    {
        "title": "Angela Purple as Brand Theme",
        "category": "design",
        "context": "CogniFy is part of Angela ecosystem, needs consistent branding",
        "decision_made": "Dark mode with purple accents (#a855f7 primary). Angela Purple identity across all apps.",
        "reasoning": "Brand consistency with Angela AI. Dark mode preferred for data-heavy interfaces.",
    },
]

# ============================================================
# FLOWS
# ============================================================
FLOWS = [
    {
        "flow_name": "Document Upload & Processing",
        "flow_type": "data",
        "description": "End-to-end document processing from upload to searchable chunks",
        "steps": json.dumps([
            {"step": 1, "action": "Upload", "detail": "POST /api/documents/upload with FormData. Validate file type + size."},
            {"step": 2, "action": "Save & Record", "detail": "Save file to UPLOAD_DIR, create Document record (status=pending)"},
            {"step": 3, "action": "Extract Text", "detail": "PyMuPDF (PDF), python-docx (DOCX), or file-specific parser. Step=extracting"},
            {"step": 4, "action": "Chunk", "detail": "ChunkingService: 500 tokens, 100 overlap, section-aware. Step=chunking"},
            {"step": 5, "action": "Embed", "detail": "EmbeddingService batch embed. Check cache (memory→DB). bge-m3 → mxbai → OpenAI fallback. Step=embedding"},
            {"step": 6, "action": "Store", "detail": "INSERT chunks with embeddings to document_chunks. Step=storing"},
            {"step": 7, "action": "Complete", "detail": "Update status=completed, total_chunks=count"},
        ]),
        "critical_notes": "Embedding must be string format for pgvector. Test embedding service availability before accepting upload.",
    },
    {
        "flow_name": "Hybrid Search Pipeline",
        "flow_type": "data",
        "description": "Query → Vector+BM25 parallel → RRF fusion → Re-rank → Results",
        "steps": json.dumps([
            {"step": 1, "action": "Query Input", "detail": "SearchRequest with RAGSettings"},
            {"step": 2, "action": "HyDE (optional)", "detail": "LLM generates hypothetical answer → embed enriched text"},
            {"step": 3, "action": "Parallel Search", "detail": "Vector: embed → pgvector cosine. BM25: ts_rank_cd. Run in parallel"},
            {"step": 4, "action": "RRF Fusion", "detail": "score = 0.6*(1/(60+vec_rank)) + 0.4*(1/(60+bm25_rank))"},
            {"step": 5, "action": "Filter", "detail": "Apply similarity_threshold"},
            {"step": 6, "action": "Re-rank", "detail": "If enabled: LLM re-ranks top 20 → return top 5"},
            {"step": 7, "action": "Augment", "detail": "Add source metadata (doc name, page, section)"},
        ]),
        "critical_notes": "RRF needs default rank 999999 for missing results. Re-ranker uses same model as chat LLM.",
    },
    {
        "flow_name": "Token Refresh Flow",
        "flow_type": "auth",
        "description": "JWT access/refresh token lifecycle with rotation",
        "steps": json.dumps([
            {"step": 1, "action": "Check Expiry", "detail": "Frontend checks access token expiry (5-min buffer)"},
            {"step": 2, "action": "Refresh", "detail": "POST /api/auth/refresh with HttpOnly cookie"},
            {"step": 3, "action": "Validate", "detail": "Hash token, lookup in DB, check: not revoked, not used, not expired"},
            {"step": 4, "action": "Rotate", "detail": "Create new pair, new family_id, mark old is_used=true"},
            {"step": 5, "action": "Set Cookie", "detail": "New refresh in HttpOnly cookie, return access token"},
            {"step": 6, "action": "Queue Retry", "detail": "On 401: queue request, refresh, retry with new token"},
        ]),
        "critical_notes": "Concurrent 401s use queue lock. /logout-all revokes entire family.",
    },
    {
        "flow_name": "Database Connector Sync",
        "flow_type": "data",
        "description": "External database sync to RAG-searchable chunks",
        "steps": json.dumps([
            {"step": 1, "action": "Create Connection", "detail": "POST /api/connectors with credentials (Fernet encrypt password)"},
            {"step": 2, "action": "Initiate Sync", "detail": "POST /api/connectors/{id}/sync"},
            {"step": 3, "action": "Decrypt & Connect", "detail": "Decrypt password, connect to external DB"},
            {"step": 4, "action": "Extract", "detail": "Query tables in sync_config, paginate for large datasets"},
            {"step": 5, "action": "Format", "detail": "Format rows as text: '{table}: {col}={val}, ...'"},
            {"step": 6, "action": "Chunk & Embed", "detail": "Reuse ChunkingService + EmbeddingService"},
            {"step": 7, "action": "Store", "detail": "Insert document_chunks with source metadata"},
            {"step": 8, "action": "Update Status", "detail": "last_sync_status=completed, total_chunks_synced=count"},
        ]),
    },
]


async def main(dry_run: bool = False) -> None:
    from angela_core.database import AngelaDatabase

    db = AngelaDatabase()
    await db.connect()

    try:
        pid = await db.fetchval(
            "SELECT project_id FROM angela_projects WHERE project_code = $1", CODE
        )
        if not pid:
            print(f"❌ Project {CODE} not found!")
            return
        print(f"📁 {CODE}: {str(pid)[:8]}...\n")

        # 1. Tech Stack
        print("=== 1. project_tech_stack ===")
        for t_type, t_name, ver, purpose in TECH_STACK:
            if not dry_run:
                await db.execute("""
                    INSERT INTO project_tech_stack (project_id, tech_type, tech_name, version, purpose)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (project_id, tech_type, tech_name) DO UPDATE SET version = $4, purpose = $5
                """, pid, t_type, t_name, ver, purpose)
        c = await db.fetchval("SELECT COUNT(*) FROM project_tech_stack WHERE project_id = $1", pid)
        print(f"  CogniFy tech_stack: {c} rows")

        # 2. Patterns
        print("\n=== 2. project_patterns ===")
        for p in PATTERNS:
            if not dry_run:
                await db.execute("""
                    INSERT INTO project_patterns (project_id, pattern_name, pattern_type, description, file_path)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (project_id, pattern_name) DO UPDATE SET description = $4, file_path = $5
                """, pid, p['name'], p['type'], p['description'], p.get('file_path'))
            print(f"  ✅ {p['name']}")
        c = await db.fetchval("SELECT COUNT(*) FROM project_patterns WHERE project_id = $1", pid)
        print(f"  CogniFy patterns: {c} rows")

        # 3. Schemas
        print("\n=== 3. project_schemas ===")
        for s in SCHEMAS:
            if not dry_run:
                await db.execute("""
                    INSERT INTO project_schemas (project_id, table_name, schema_type, columns, purpose, gotchas)
                    VALUES ($1, $2, $3, $4::jsonb, $5, $6)
                    ON CONFLICT (project_id, table_name) DO UPDATE SET columns = $4::jsonb, purpose = $5, gotchas = $6
                """, pid, s['table_name'], s['schema_type'], s['columns'], s['purpose'], s.get('gotchas'))
            print(f"  ✅ {s['table_name']}")
        c = await db.fetchval("SELECT COUNT(*) FROM project_schemas WHERE project_id = $1", pid)
        print(f"  CogniFy schemas: {c} rows")

        # 4. Entity Relations
        print("\n=== 4. project_entity_relations ===")
        for from_t, to_t, rel_type, join_cond, name in RELATIONS:
            if not dry_run:
                await db.execute("""
                    INSERT INTO project_entity_relations (project_id, from_table, to_table, relation_type, join_condition, relation_name)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (project_id, from_table, to_table, relation_type) DO NOTHING
                """, pid, from_t, to_t, rel_type, join_cond, name)
            print(f"  ✅ {from_t} → {to_t}")
        c = await db.fetchval("SELECT COUNT(*) FROM project_entity_relations WHERE project_id = $1", pid)
        print(f"  CogniFy relations: {c} rows")

        # 5. Learnings
        print("\n=== 5. project_learnings ===")
        for l in LEARNINGS:
            existing = await db.fetchval(
                "SELECT COUNT(*) FROM project_learnings WHERE project_id = $1 AND title = $2",
                pid, l['title']
            )
            if existing > 0:
                continue
            if not dry_run:
                await db.execute("""
                    INSERT INTO project_learnings (project_id, learning_type, category, title, insight, confidence)
                    VALUES ($1, $2, $3, $4, $5, 0.95)
                """, pid, l['type'], l['category'], l['title'], l['insight'])
            print(f"  ✅ {l['title']}")
        c = await db.fetchval("SELECT COUNT(*) FROM project_learnings WHERE project_id = $1", pid)
        print(f"  CogniFy learnings: {c} rows")

        # 6. Technical Decisions
        print("\n=== 6. project_technical_decisions ===")
        for d in DECISIONS:
            existing = await db.fetchval(
                "SELECT COUNT(*) FROM project_technical_decisions WHERE project_id = $1 AND decision_title = $2",
                pid, d['title']
            )
            if existing > 0:
                continue
            if not dry_run:
                await db.execute("""
                    INSERT INTO project_technical_decisions (project_id, decision_title, category, context, decision_made, reasoning, decided_by)
                    VALUES ($1, $2, $3, $4, $5, $6, 'David')
                """, pid, d['title'], d['category'], d['context'], d['decision_made'], d['reasoning'])
            print(f"  ✅ {d['title']}")
        c = await db.fetchval("SELECT COUNT(*) FROM project_technical_decisions WHERE project_id = $1", pid)
        print(f"  CogniFy decisions: {c} rows")

        # 7. Flows
        print("\n=== 7. project_flows ===")
        for f in FLOWS:
            if not dry_run:
                await db.execute("""
                    INSERT INTO project_flows (project_id, flow_name, flow_type, description, steps, critical_notes)
                    VALUES ($1, $2, $3, $4, $5::jsonb, $6)
                    ON CONFLICT (project_id, flow_name) DO UPDATE SET steps = $5::jsonb, critical_notes = $6
                """, pid, f['flow_name'], f['flow_type'], f['description'], f['steps'], f.get('critical_notes'))
            print(f"  ✅ {f['flow_name']}")
        c = await db.fetchval("SELECT COUNT(*) FROM project_flows WHERE project_id = $1", pid)
        print(f"  CogniFy flows: {c} rows")

        # FINAL
        print("\n" + "=" * 60)
        print("FINAL COUNTS (ALL PROJECTS)")
        print("=" * 60)
        for table in [
            'project_tech_stack', 'project_patterns', 'project_schemas',
            'project_entity_relations', 'project_learnings',
            'project_technical_decisions', 'project_flows',
        ]:
            c = await db.fetchval(f"SELECT COUNT(*) FROM {table}")
            print(f"  {table:40s} {c:>5} rows")

    finally:
        await db.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
