"""
DB Service — Supabase PostgreSQL connection pool for AI TOP.
Schema: angela_aitop
"""

import json
import logging
import platform
import socket
import sys
from pathlib import Path
from typing import Optional

import asyncpg
import numpy as np

# Add AngelaAI root to sys.path for config imports
_angela_root = str(Path(__file__).resolve().parents[3])
if _angela_root not in sys.path:
    sys.path.insert(0, _angela_root)

from config.db_url import get_supabase_url

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None

# Detect machine name: M3/M4 based on hostname, fallback to chip
MACHINE_TAG = "M4" if "M4" in platform.processor().upper() or "m4" in socket.gethostname().lower() else "M3"


async def init_pool():
    """Initialize asyncpg connection pool."""
    global _pool
    if _pool is not None:
        return
    url = get_supabase_url()
    _pool = await asyncpg.create_pool(url, ssl="require", min_size=2, max_size=5, statement_cache_size=0)
    logger.info(f"Supabase pool initialized (machine={MACHINE_TAG})")


async def close_pool():
    """Close the connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Supabase pool closed")


async def get_pool() -> asyncpg.Pool:
    """Get the connection pool, initializing if needed."""
    if _pool is None:
        await init_pool()
    return _pool


# ============================================================
# Fine-Tune Jobs
# ============================================================

async def save_finetune_job(job_dict: dict) -> None:
    """Upsert a finetune job to Supabase (expanded for Fine-Tune Studio)."""
    pool = await get_pool()
    await pool.execute("""
        INSERT INTO angela_aitop.finetune_jobs
            (short_id, model, dataset_path, strategy, status, epochs, learning_rate,
             lora_rank, batch_size, current_epoch, current_step, total_steps,
             loss, loss_history, output_dir, error, machine,
             training_method, engine, config, best_loss, lr_history,
             memory_peak_gb, estimated_duration_s, estimated_memory_gb,
             started_at, finished_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14::jsonb, $15, $16, $17,
                $18, $19, $20::jsonb, $21, $22::jsonb, $23, $24, $25,
                CASE WHEN $26 > 0 THEN to_timestamp($26) ELSE NULL END,
                CASE WHEN $27 > 0 THEN to_timestamp($27) ELSE NULL END)
        ON CONFLICT (short_id) DO UPDATE SET
            status = EXCLUDED.status,
            current_epoch = EXCLUDED.current_epoch,
            current_step = EXCLUDED.current_step,
            total_steps = EXCLUDED.total_steps,
            loss = EXCLUDED.loss,
            loss_history = EXCLUDED.loss_history,
            best_loss = EXCLUDED.best_loss,
            lr_history = EXCLUDED.lr_history,
            memory_peak_gb = EXCLUDED.memory_peak_gb,
            error = EXCLUDED.error,
            started_at = EXCLUDED.started_at,
            finished_at = EXCLUDED.finished_at,
            updated_at = NOW()
    """,
        job_dict.get("id", ""),
        job_dict.get("model", ""),
        job_dict.get("dataset_path", ""),
        job_dict.get("strategy", "standard"),
        job_dict.get("status", "pending"),
        job_dict.get("epochs", 3),
        job_dict.get("learning_rate", 0.0002),
        job_dict.get("lora_rank", 8),
        job_dict.get("batch_size", 2),
        job_dict.get("current_epoch", 0),
        job_dict.get("current_step", 0),
        job_dict.get("total_steps", 0),
        job_dict.get("loss", 0.0),
        json.dumps(job_dict.get("loss_history", [])),
        job_dict.get("output_dir", ""),
        job_dict.get("error", ""),
        MACHINE_TAG,
        job_dict.get("training_method", "mlx_lora"),
        job_dict.get("engine", "mlx"),
        json.dumps(job_dict.get("config", {})),
        job_dict.get("best_loss"),
        json.dumps(job_dict.get("lr_history", [])),
        job_dict.get("memory_peak_gb"),
        job_dict.get("estimated_duration_s"),
        job_dict.get("estimated_memory_gb"),
        job_dict.get("started_at", 0),
        job_dict.get("finished_at", 0),
    )


async def load_finetune_jobs() -> list[dict]:
    """Load all finetune jobs from Supabase (expanded for Fine-Tune Studio)."""
    pool = await get_pool()
    rows = await pool.fetch("""
        SELECT short_id, model, dataset_path, strategy, status, epochs, learning_rate,
               lora_rank, batch_size, current_epoch, current_step, total_steps,
               loss, loss_history, output_dir, error, machine,
               training_method, engine, config, best_loss, lr_history,
               memory_peak_gb, estimated_duration_s, estimated_memory_gb,
               EXTRACT(EPOCH FROM started_at) as started_at,
               EXTRACT(EPOCH FROM finished_at) as finished_at
        FROM angela_aitop.finetune_jobs
        ORDER BY created_at DESC
    """)
    jobs = []
    for r in rows:
        def _parse_jsonb(val):
            if val is None:
                return []
            if isinstance(val, str):
                return json.loads(val)
            return val  # already parsed by asyncpg

        jobs.append({
            "id": r["short_id"],
            "model": r["model"],
            "dataset_path": r["dataset_path"],
            "strategy": r["strategy"],
            "status": r["status"],
            "epochs": r["epochs"],
            "learning_rate": r["learning_rate"],
            "lora_rank": r["lora_rank"],
            "batch_size": r["batch_size"],
            "current_epoch": r["current_epoch"],
            "current_step": r["current_step"],
            "total_steps": r["total_steps"],
            "loss": r["loss"],
            "loss_history": _parse_jsonb(r["loss_history"]),
            "output_dir": r["output_dir"] or "",
            "error": r["error"] or "",
            "training_method": r["training_method"] or "mlx_lora",
            "engine": r["engine"] or "mlx",
            "config": _parse_jsonb(r["config"]) if r["config"] else {},
            "best_loss": r["best_loss"],
            "lr_history": _parse_jsonb(r["lr_history"]),
            "memory_peak_gb": r["memory_peak_gb"],
            "estimated_duration_s": r["estimated_duration_s"],
            "estimated_memory_gb": r["estimated_memory_gb"],
            "started_at": float(r["started_at"] or 0),
            "finished_at": float(r["finished_at"] or 0),
        })
    return jobs


# ============================================================
# Fine-Tune Datasets
# ============================================================

async def save_dataset(filename: str, file_path: str, size_bytes: int, line_count: int,
                       fmt: str = "jsonl", name: str = None, dataset_type: str = "sft") -> str:
    """Save dataset metadata to Supabase. Returns the dataset UUID."""
    pool = await get_pool()
    row = await pool.fetchrow("""
        INSERT INTO angela_aitop.finetune_datasets
            (filename, file_path, size_bytes, line_count, format, machine, name, dataset_type)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING id::text
    """, filename, file_path, size_bytes, line_count, fmt, MACHINE_TAG,
        name or filename, dataset_type)
    return row["id"] if row else ""


async def update_dataset_validation(dataset_id: str, total_examples: int,
                                     avg_input_length: int, avg_output_length: int,
                                     is_validated: bool, validation_errors: list = None,
                                     file_hash: str = None, status: str = "ready") -> None:
    """Update dataset with validation results."""
    pool = await get_pool()
    await pool.execute("""
        UPDATE angela_aitop.finetune_datasets
        SET total_examples = $2, avg_input_length = $3, avg_output_length = $4,
            is_validated = $5, validation_errors = $6::jsonb, file_hash = $7, status = $8
        WHERE id = $1::uuid
    """, dataset_id, total_examples, avg_input_length, avg_output_length,
        is_validated, json.dumps(validation_errors or []), file_hash, status)


async def list_datasets() -> list[dict]:
    """List all datasets from Supabase (expanded)."""
    pool = await get_pool()
    rows = await pool.fetch("""
        SELECT id::text, filename, file_path, size_bytes, line_count, format, machine,
               uploaded_at, name, dataset_type, status, total_examples,
               avg_input_length, avg_output_length, is_validated, validation_errors, file_hash
        FROM angela_aitop.finetune_datasets ORDER BY uploaded_at DESC
    """)
    result = []
    for r in rows:
        d = dict(r)
        if isinstance(d.get("validation_errors"), str):
            d["validation_errors"] = json.loads(d["validation_errors"])
        result.append(d)
    return result


async def delete_dataset(dataset_id: str) -> bool:
    """Delete a dataset from Supabase."""
    pool = await get_pool()
    result = await pool.execute(
        "DELETE FROM angela_aitop.finetune_datasets WHERE id = $1::uuid", dataset_id)
    return "DELETE 1" in result


# ============================================================
# Local Models Registry
# ============================================================

async def save_local_model(model_dict: dict) -> str:
    """Upsert a local model to Supabase. Returns model UUID."""
    pool = await get_pool()
    row = await pool.fetchrow("""
        INSERT INTO angela_aitop.local_models
            (name, model_type, hf_model_id, file_path, file_size_mb, status,
             parent_model_id, training_job_id, ollama_name, machine)
        VALUES ($1, $2, $3, $4, $5, $6, $7::uuid, $8, $9, $10)
        RETURNING id::text
    """,
        model_dict["name"],
        model_dict["model_type"],
        model_dict.get("hf_model_id"),
        model_dict.get("file_path"),
        model_dict.get("file_size_mb"),
        model_dict.get("status", "ready"),
        model_dict.get("parent_model_id"),
        model_dict.get("training_job_id"),
        model_dict.get("ollama_name"),
        MACHINE_TAG,
    )
    return row["id"] if row else ""


async def update_local_model_status(model_id: str, status: str, **kwargs) -> None:
    """Update local model status and optional fields."""
    pool = await get_pool()
    sets = ["status = $2", "updated_at = NOW()"]
    params = [model_id, status]
    idx = 3
    for key in ("ollama_name", "file_path", "file_size_mb"):
        if key in kwargs:
            sets.append(f"{key} = ${idx}")
            params.append(kwargs[key])
            idx += 1
    await pool.execute(
        f"UPDATE angela_aitop.local_models SET {', '.join(sets)} WHERE id = $1::uuid",
        *params)


async def list_local_models() -> list[dict]:
    """List all local models from Supabase."""
    pool = await get_pool()
    rows = await pool.fetch("""
        SELECT id::text, name, model_type, hf_model_id, file_path, file_size_mb,
               status, parent_model_id::text, training_job_id, ollama_name, machine,
               created_at, updated_at
        FROM angela_aitop.local_models ORDER BY created_at DESC
    """)
    return [dict(r) for r in rows]


async def delete_local_model(model_id: str) -> bool:
    """Delete a local model from Supabase."""
    pool = await get_pool()
    result = await pool.execute(
        "DELETE FROM angela_aitop.local_models WHERE id = $1::uuid", model_id)
    return "DELETE 1" in result


# ============================================================
# RAG Documents
# ============================================================

async def save_rag_document(doc: dict) -> None:
    """Save RAG document metadata to Supabase."""
    pool = await get_pool()
    await pool.execute("""
        INSERT INTO angela_aitop.rag_documents (short_id, filename, content_preview, chunk_count, char_count, indexed, machine)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (short_id) DO UPDATE SET
            chunk_count = EXCLUDED.chunk_count,
            indexed = EXCLUDED.indexed
    """,
        doc["id"],
        doc["filename"],
        doc.get("content", "")[:500],
        doc.get("chunk_count", 0),
        doc.get("char_count", 0),
        doc.get("indexed", False),
        MACHINE_TAG,
    )


async def save_rag_chunks(doc_id_short: str, chunks: list[dict], embeddings: np.ndarray) -> None:
    """Save RAG chunks + embeddings to Supabase using pgvector."""
    pool = await get_pool()
    # Get the UUID for this doc
    doc_uuid = await pool.fetchval(
        "SELECT id FROM angela_aitop.rag_documents WHERE short_id = $1", doc_id_short
    )
    if not doc_uuid:
        logger.error(f"Document {doc_id_short} not found in DB")
        return

    # Batch insert chunks
    async with pool.acquire() as conn:
        # Delete old chunks for this doc (re-index case)
        await conn.execute("DELETE FROM angela_aitop.rag_chunks WHERE doc_id = $1", doc_uuid)
        # Insert new
        for i, chunk in enumerate(chunks):
            emb = embeddings[i] if i < len(embeddings) else None
            emb_str = f"[{','.join(str(float(x)) for x in emb)}]" if emb is not None else None
            await conn.execute("""
                INSERT INTO angela_aitop.rag_chunks (doc_id, chunk_index, chunk_text, embedding)
                VALUES ($1, $2, $3, $4::vector)
            """, doc_uuid, chunk.get("index", i), chunk.get("text", ""), emb_str)


async def delete_rag_document(short_id: str) -> bool:
    """Delete RAG document + chunks (CASCADE) from Supabase."""
    pool = await get_pool()
    result = await pool.execute(
        "DELETE FROM angela_aitop.rag_documents WHERE short_id = $1", short_id
    )
    return "DELETE 1" in result


async def load_rag_documents() -> list[dict]:
    """Load all RAG documents from Supabase."""
    pool = await get_pool()
    rows = await pool.fetch("""
        SELECT short_id as id, filename, content_preview as content, chunk_count, char_count, indexed, machine
        FROM angela_aitop.rag_documents ORDER BY created_at DESC
    """)
    return [dict(r) for r in rows]


async def load_rag_chunks() -> tuple[list[dict], Optional[np.ndarray]]:
    """Load all RAG chunks + embeddings from Supabase."""
    pool = await get_pool()
    rows = await pool.fetch("""
        SELECT c.doc_id, d.short_id as doc_short_id, c.chunk_index, c.chunk_text, c.embedding::text as embedding_text
        FROM angela_aitop.rag_chunks c
        JOIN angela_aitop.rag_documents d ON d.id = c.doc_id
        ORDER BY d.short_id, c.chunk_index
    """)
    if not rows:
        return [], None

    chunks = []
    embeddings = []
    for r in rows:
        chunks.append({
            "doc_id": r["doc_short_id"],
            "index": r["chunk_index"],
            "text": r["chunk_text"],
        })
        # Parse pgvector text format: [0.1,0.2,...]
        if r["embedding_text"]:
            emb_str = r["embedding_text"].strip("[]")
            emb = np.array([float(x) for x in emb_str.split(",")], dtype=np.float32)
            embeddings.append(emb)

    emb_matrix = np.array(embeddings) if embeddings else None
    return chunks, emb_matrix


async def search_rag_pgvector(query_embedding: np.ndarray, top_k: int = 5) -> list[dict]:
    """Search RAG chunks using pgvector cosine similarity (server-side)."""
    pool = await get_pool()
    emb_str = f"[{','.join(str(float(x)) for x in query_embedding)}]"
    rows = await pool.fetch("""
        SELECT c.chunk_text, 1 - (c.embedding <=> $1::vector) as score,
               d.short_id as doc_id, d.filename as doc_name, c.chunk_index
        FROM angela_aitop.rag_chunks c
        JOIN angela_aitop.rag_documents d ON d.id = c.doc_id
        ORDER BY c.embedding <=> $1::vector
        LIMIT $2
    """, emb_str, top_k)
    return [
        {
            "chunk_text": r["chunk_text"],
            "score": float(r["score"]),
            "doc_id": r["doc_id"],
            "doc_name": r["doc_name"],
            "chunk_index": r["chunk_index"],
        }
        for r in rows
    ]


# ============================================================
# Export Batches
# ============================================================

async def save_export_batch(batch: dict) -> str:
    """Save an export batch record. Returns batch UUID."""
    pool = await get_pool()
    row = await pool.fetchrow("""
        INSERT INTO angela_aitop.export_batches
            (batch_name, export_type, status, output_path, preview_path,
             total_pairs, filtered_out, avg_quality, file_size_kb,
             export_config, quality_distribution, source_distribution, top_topics,
             avg_user_length, avg_angela_length, machine)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb, $11::jsonb, $12::jsonb, $13::jsonb, $14, $15, $16)
        RETURNING id::text
    """,
        batch["batch_name"],
        batch.get("export_type", "sft"),
        batch.get("status", "ready"),
        batch.get("output_path", ""),
        batch.get("preview_path", ""),
        batch.get("total_pairs", 0),
        batch.get("filtered_out", 0),
        batch.get("avg_quality"),
        batch.get("file_size_kb"),
        json.dumps(batch.get("export_config", {})),
        json.dumps(batch.get("quality_distribution", {})),
        json.dumps(batch.get("source_distribution", {})),
        json.dumps(batch.get("top_topics", [])),
        batch.get("avg_user_length"),
        batch.get("avg_angela_length"),
        MACHINE_TAG,
    )
    return row["id"] if row else ""


async def list_export_batches() -> list[dict]:
    """List all export batches, newest first."""
    pool = await get_pool()
    rows = await pool.fetch("""
        SELECT id::text, batch_name, export_type, status, output_path, preview_path,
               total_pairs, filtered_out, avg_quality, file_size_kb,
               export_config, quality_distribution, source_distribution, top_topics,
               avg_user_length, avg_angela_length, used_in_jobs, machine, created_at
        FROM angela_aitop.export_batches
        ORDER BY created_at DESC
    """)
    result = []
    for r in rows:
        d = dict(r)
        for key in ("export_config", "quality_distribution", "source_distribution", "top_topics"):
            if isinstance(d.get(key), str):
                d[key] = json.loads(d[key])
        result.append(d)
    return result


async def mark_batch_used(batch_id: str, job_id: str) -> None:
    """Mark a batch as used in a training job."""
    pool = await get_pool()
    await pool.execute("""
        UPDATE angela_aitop.export_batches
        SET used_in_jobs = array_append(COALESCE(used_in_jobs, '{}'), $2)
        WHERE id = $1::uuid
    """, batch_id, job_id)


# ============================================================
# Trained Model History
# ============================================================

async def save_trained_model(model: dict) -> str:
    """Save a trained model record after fine-tuning completes. Returns UUID."""
    pool = await get_pool()
    row = await pool.fetchrow("""
        INSERT INTO angela_aitop.local_models
            (name, model_type, hf_model_id, file_path, file_size_mb, status,
             parent_model_id, training_job_id, ollama_name, machine,
             export_batch_id, training_config, best_loss, training_duration_s)
        VALUES ($1, $2, $3, $4, $5, $6, $7::uuid, $8, $9, $10, $11::uuid, $12::jsonb, $13, $14)
        RETURNING id::text
    """,
        model["name"],
        model.get("model_type", "lora"),
        model.get("hf_model_id"),
        model.get("file_path"),
        model.get("file_size_mb"),
        model.get("status", "ready"),
        model.get("parent_model_id"),
        model.get("training_job_id"),
        model.get("ollama_name"),
        MACHINE_TAG,
        model.get("export_batch_id"),
        json.dumps(model.get("training_config", {})),
        model.get("best_loss"),
        model.get("training_duration_s"),
    )
    return row["id"] if row else ""


async def link_job_to_model(job_id: str, model_id: str, batch_id: str = None) -> None:
    """Link a finetune job to its output model and source batch."""
    pool = await get_pool()
    await pool.execute("""
        UPDATE angela_aitop.finetune_jobs
        SET trained_model_id = $2::uuid,
            export_batch_id = CASE WHEN $3 != '' THEN $3::uuid ELSE export_batch_id END
        WHERE short_id = $1
    """, job_id, model_id, batch_id or "")


# ============================================================
# Hardware Snapshots
# ============================================================

async def save_hardware_snapshot(stats: dict) -> None:
    """Save a hardware snapshot to Supabase."""
    pool = await get_pool()
    await pool.execute("""
        INSERT INTO angela_aitop.hardware_snapshots (machine, cpu_percent, gpu_percent, memory_percent, memory_used_gb, thermal)
        VALUES ($1, $2, $3, $4, $5, $6)
    """,
        MACHINE_TAG,
        stats.get("cpu", {}).get("percent", 0),
        stats.get("gpu", {}).get("percent", 0),
        stats.get("memory", {}).get("percent", 0),
        stats.get("memory", {}).get("used_gb", 0),
        stats.get("thermal", "unknown"),
    )
