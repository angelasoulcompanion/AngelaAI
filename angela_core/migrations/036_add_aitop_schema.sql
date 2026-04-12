-- Migration 036: Create angela_aitop schema for AI TOP app
-- Shared storage for finetune jobs, RAG documents, and datasets across machines (M3/M4)

CREATE SCHEMA IF NOT EXISTS angela_aitop;

-- ============================================================
-- Fine-Tune Jobs
-- ============================================================
CREATE TABLE IF NOT EXISTS angela_aitop.finetune_jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    short_id        VARCHAR(8) NOT NULL UNIQUE,
    model           TEXT NOT NULL,
    dataset_path    TEXT NOT NULL,
    strategy        VARCHAR(20) NOT NULL DEFAULT 'standard',
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    epochs          INT NOT NULL DEFAULT 3,
    learning_rate   DOUBLE PRECISION NOT NULL DEFAULT 0.0002,
    lora_rank       INT NOT NULL DEFAULT 8,
    batch_size      INT NOT NULL DEFAULT 2,
    current_epoch   INT NOT NULL DEFAULT 0,
    current_step    INT NOT NULL DEFAULT 0,
    total_steps     INT NOT NULL DEFAULT 0,
    loss            DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    loss_history    JSONB NOT NULL DEFAULT '[]'::jsonb,
    output_dir      TEXT,
    error           TEXT,
    machine         VARCHAR(20),  -- 'M3' or 'M4'
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_aitop_finetune_status ON angela_aitop.finetune_jobs (status);
CREATE INDEX IF NOT EXISTS idx_aitop_finetune_machine ON angela_aitop.finetune_jobs (machine);

-- ============================================================
-- Fine-Tune Datasets
-- ============================================================
CREATE TABLE IF NOT EXISTS angela_aitop.finetune_datasets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename        TEXT NOT NULL,
    file_path       TEXT NOT NULL,
    size_bytes      BIGINT NOT NULL DEFAULT 0,
    line_count      INT NOT NULL DEFAULT 0,
    format          VARCHAR(10) NOT NULL DEFAULT 'jsonl',
    machine         VARCHAR(20),
    uploaded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_aitop_datasets_machine ON angela_aitop.finetune_datasets (machine);

-- ============================================================
-- RAG Documents
-- ============================================================
CREATE TABLE IF NOT EXISTS angela_aitop.rag_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    short_id        VARCHAR(8) NOT NULL UNIQUE,
    filename        TEXT NOT NULL,
    content_preview TEXT,          -- first 500 chars
    chunk_count     INT NOT NULL DEFAULT 0,
    char_count      INT NOT NULL DEFAULT 0,
    indexed         BOOLEAN NOT NULL DEFAULT FALSE,
    machine         VARCHAR(20),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_aitop_rag_docs_machine ON angela_aitop.rag_documents (machine);

-- ============================================================
-- RAG Chunks + Embeddings
-- ============================================================
CREATE TABLE IF NOT EXISTS angela_aitop.rag_chunks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id          UUID NOT NULL REFERENCES angela_aitop.rag_documents(id) ON DELETE CASCADE,
    chunk_index     INT NOT NULL,
    chunk_text      TEXT NOT NULL,
    embedding       vector(384),   -- all-MiniLM-L6-v2 = 384 dims
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(doc_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_aitop_rag_chunks_doc ON angela_aitop.rag_chunks (doc_id);

-- pgvector index for similarity search (IVFFlat)
-- Only create if pgvector extension exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        EXECUTE 'CREATE INDEX IF NOT EXISTS idx_aitop_rag_embedding ON angela_aitop.rag_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10)';
    END IF;
END $$;

-- ============================================================
-- Hardware Snapshots (optional: track usage over time)
-- ============================================================
CREATE TABLE IF NOT EXISTS angela_aitop.hardware_snapshots (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    machine         VARCHAR(20) NOT NULL,
    cpu_percent     DOUBLE PRECISION,
    gpu_percent     DOUBLE PRECISION,
    memory_percent  DOUBLE PRECISION,
    memory_used_gb  DOUBLE PRECISION,
    thermal         VARCHAR(20),
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_aitop_hw_machine_time ON angela_aitop.hardware_snapshots (machine, recorded_at DESC);

-- ============================================================
-- Updated_at trigger
-- ============================================================
CREATE OR REPLACE FUNCTION angela_aitop.update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_finetune_jobs_updated
    BEFORE UPDATE ON angela_aitop.finetune_jobs
    FOR EACH ROW EXECUTE FUNCTION angela_aitop.update_timestamp();
