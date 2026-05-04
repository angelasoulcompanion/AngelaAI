"""
DB helpers for Video Studio — uses AITop's existing asyncpg pool.

Persists pipeline output:
  PDF upload → video_pdfs (sha256-keyed central library)
  analyze_pdf() result → video_projects + video_segments + video_prompts

The submission/QA tracking layer was removed in migration 002 — AITop now
stops at "prompt ready"; the user copies the prompt and runs NotebookLM
manually.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Reuse AITop's pool (no second pool — connection budget is tight on Supabase).
from services.db_service import get_pool, MACHINE_TAG  # type: ignore

from . import pdf_storage
from .pipeline import AnalysisResult
from .prompt_templates import (
    DEFAULT_FORMAT,
    DEFAULT_VISUAL_STYLE,
    TEMPLATES,
)


# ============================================================
# Schema bootstrap
# ============================================================

async def ensure_schema() -> None:
    """Apply migrations idempotently and seed templates."""
    pool = await get_pool()
    migrations_dir = Path(__file__).resolve().parent / "migrations"
    sql_files = sorted(migrations_dir.glob("*.sql"))
    async with pool.acquire() as conn:
        for sql_file in sql_files:
            await conn.execute(sql_file.read_text(encoding="utf-8"))
    await seed_templates()


async def seed_templates() -> None:
    """Upsert the 4 master templates from prompt_templates.py."""
    pool = await get_pool()
    descriptions = {
        "master_teacher": "Default Explainer — Feynman-style, hook-first, analogy-driven.",
        "brief":          "Brief format — 2-4 minute compressed summary, single take-home.",
        "walk_through":   "Technical / equation-heavy — decode every symbol, worked example, common pitfalls.",
        "persona_driven": "Stylistic consistency across a series — adopt a named teacher's signature moves.",
    }
    async with pool.acquire() as conn:
        for name, content in TEMPLATES.items():
            await conn.execute(
                """
                INSERT INTO angela_video_studio.video_prompt_templates
                    (name, content, default_format, default_visual_style, description)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (name) DO UPDATE SET
                    content              = EXCLUDED.content,
                    default_format       = EXCLUDED.default_format,
                    default_visual_style = EXCLUDED.default_visual_style,
                    description          = EXCLUDED.description
                """,
                name, content, DEFAULT_FORMAT[name], DEFAULT_VISUAL_STYLE[name],
                descriptions.get(name),
            )


# ============================================================
# PDF library — Supabase Storage bucket + video_pdfs table
# ============================================================

async def upsert_video_pdf(
    sha256: str,
    original_filename: str,
    byte_size: int,
    page_count: int,
) -> None:
    """Idempotent upsert. The bucket object itself is uploaded by pdf_storage.upload()."""
    pool = await get_pool()
    await pool.execute(
        """
        INSERT INTO angela_video_studio.video_pdfs
            (sha256, original_filename, byte_size, page_count,
             storage_bucket, storage_object_path, machine)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (sha256) DO UPDATE SET
            original_filename = EXCLUDED.original_filename,
            byte_size         = EXCLUDED.byte_size,
            page_count        = EXCLUDED.page_count
        """,
        sha256, original_filename, byte_size, page_count,
        pdf_storage.BUCKET, pdf_storage.object_path_for(sha256), MACHINE_TAG,
    )


async def get_pdf_by_sha256(sha256: str) -> Optional[dict]:
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        SELECT sha256, original_filename, byte_size, page_count,
               storage_bucket, storage_object_path, machine, uploaded_at
        FROM angela_video_studio.video_pdfs
        WHERE sha256 = $1
        """,
        sha256,
    )
    return dict(row) if row else None


# ============================================================
# Persist analysis result
# ============================================================

async def save_analysis_result(result: AnalysisResult, pdf_sha256: str) -> str:
    """
    Save an AnalysisResult and return the project_id (uuid).

    `pdf_sha256` is required and must already exist in `video_pdfs`
    (caller is responsible for upserting that row first).

    If a project with the same pdf_sha256 already exists, REPLACE its
    segments and prompts (re-analysis flow).
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            existing = await conn.fetchrow(
                """
                SELECT id FROM angela_video_studio.video_projects
                WHERE pdf_sha256 = $1
                ORDER BY created_at DESC LIMIT 1
                """,
                pdf_sha256,
            )

            if existing:
                project_id = existing["id"]
                await conn.execute(
                    """
                    UPDATE angela_video_studio.video_projects SET
                        title = $2,
                        audience = $3,
                        total_pages = $4,
                        total_estimated_minutes = $5,
                        recommended_count = $6,
                        alternatives = $7::jsonb,
                        machine = $8,
                        status = 'analyzed'
                    WHERE id = $1
                    """,
                    project_id,
                    result.deck_title,
                    result.audience,
                    result.total_pages,
                    result.total_estimated_minutes,
                    result.recommended_count,
                    json.dumps(result.alternatives, ensure_ascii=False),
                    MACHINE_TAG,
                )
                # Wipe segments (cascade kills prompts) so we can reinsert.
                await conn.execute(
                    "DELETE FROM angela_video_studio.video_segments WHERE project_id = $1",
                    project_id,
                )
            else:
                row = await conn.fetchrow(
                    """
                    INSERT INTO angela_video_studio.video_projects
                        (title, pdf_sha256, audience,
                         total_pages, total_estimated_minutes, recommended_count,
                         alternatives, machine, status)
                    VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8, 'analyzed')
                    RETURNING id
                    """,
                    result.deck_title,
                    pdf_sha256,
                    result.audience,
                    result.total_pages,
                    result.total_estimated_minutes,
                    result.recommended_count,
                    json.dumps(result.alternatives, ensure_ascii=False),
                    MACHINE_TAG,
                )
                project_id = row["id"]

            # Segments + first-version prompts.
            for seg in result.segments:
                seg_row = await conn.fetchrow(
                    """
                    INSERT INTO angela_video_studio.video_segments
                        (project_id, sequence, title, start_page, end_page,
                         page_count, est_minutes, cognitive_load,
                         cuts_mid_section, summary, status)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb, 'prompt_ready')
                    RETURNING id
                    """,
                    project_id,
                    seg["sequence"],
                    seg.get("title"),
                    seg["start_page"],
                    seg["end_page"],
                    seg["page_count"],
                    seg["est_minutes"],
                    seg["cognitive_load"],
                    seg.get("cuts_mid_section", False),
                    seg.get("summary") or "{}",
                )
                seg_id = seg_row["id"]

                prompt_pkg = seg["prompt"]
                target_min = max(2, min(13, int(round(seg["est_minutes"])))) \
                    if seg["est_minutes"] >= 8 else 10
                await conn.execute(
                    """
                    INSERT INTO angela_video_studio.video_prompts
                        (segment_id, template_name, notebooklm_format, visual_style,
                         target_minutes, filled_prompt, version)
                    VALUES ($1, $2, $3, $4, $5, $6, 1)
                    """,
                    seg_id,
                    prompt_pkg["template_name"],
                    prompt_pkg["format"],
                    prompt_pkg["visual_style"],
                    target_min,
                    prompt_pkg["prompt"],
                )

    return str(project_id)


# ============================================================
# Read helpers
# ============================================================

async def list_projects(limit: int = 50) -> list[dict]:
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT p.id, p.title, p.pdf_sha256,
               pdf.original_filename, pdf.byte_size,
               p.total_pages, p.total_estimated_minutes,
               p.recommended_count, p.status, p.machine, p.created_at
        FROM angela_video_studio.video_projects p
        JOIN angela_video_studio.video_pdfs pdf ON pdf.sha256 = p.pdf_sha256
        ORDER BY p.created_at DESC
        LIMIT $1
        """,
        limit,
    )
    return [dict(r) for r in rows]


async def get_project(project_id: str) -> Optional[dict]:
    pool = await get_pool()
    proj = await pool.fetchrow(
        """
        SELECT p.*, pdf.original_filename, pdf.byte_size,
               pdf.storage_bucket, pdf.storage_object_path
        FROM angela_video_studio.video_projects p
        JOIN angela_video_studio.video_pdfs pdf ON pdf.sha256 = p.pdf_sha256
        WHERE p.id = $1
        """,
        project_id,
    )
    if not proj:
        return None
    segs = await pool.fetch(
        """
        SELECT s.*,
               (SELECT row_to_json(p) FROM (
                  SELECT template_name, notebooklm_format, visual_style,
                         target_minutes, filled_prompt, version
                  FROM angela_video_studio.video_prompts
                  WHERE segment_id = s.id
                  ORDER BY version DESC LIMIT 1
               ) p) AS latest_prompt
        FROM angela_video_studio.video_segments s
        WHERE s.project_id = $1
        ORDER BY s.sequence
        """,
        project_id,
    )
    proj_d = _decode_jsonb_fields(dict(proj), ["alternatives"])
    out_segs = []
    for s in segs:
        d = _decode_jsonb_fields(dict(s), ["summary"])
        if isinstance(d.get("latest_prompt"), str):
            try:
                d["latest_prompt"] = json.loads(d["latest_prompt"])
            except json.JSONDecodeError:
                pass
        out_segs.append(d)
    return {
        "project": proj_d,
        "segments": out_segs,
    }


def _decode_jsonb_fields(row: dict, fields: list[str]) -> dict:
    """asyncpg returns jsonb as text; decode named fields to native types."""
    for f in fields:
        v = row.get(f)
        if isinstance(v, str):
            try:
                row[f] = json.loads(v)
            except json.JSONDecodeError:
                pass
    return row


# ============================================================
# Prompt regeneration — keep history of every version that was rendered
# ============================================================

async def add_prompt_version(segment_id: str, prompt_pkg: dict, target_minutes: int,
                              note: Optional[str] = None) -> int:
    """Insert a new prompt version for an existing segment (regenerate flow)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                SELECT COALESCE(MAX(version), 0) + 1 AS next_v
                FROM angela_video_studio.video_prompts WHERE segment_id = $1
                """,
                segment_id,
            )
            next_v = row["next_v"]
            await conn.execute(
                """
                INSERT INTO angela_video_studio.video_prompts
                    (segment_id, template_name, notebooklm_format, visual_style,
                     target_minutes, filled_prompt, version, note)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                segment_id,
                prompt_pkg["template_name"],
                prompt_pkg["format"],
                prompt_pkg["visual_style"],
                target_minutes,
                prompt_pkg["prompt"],
                next_v,
                note,
            )
    return next_v
