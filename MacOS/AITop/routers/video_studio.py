"""
Video Studio router — REST API for the Angelora Video Studio tab.

Surface area is intentionally small:
  POST /video-studio/upload                — multipart PDF upload (sha-keyed)
  GET  /video-studio/projects              — list cached analyses
  GET  /video-studio/projects/{id}         — segments + latest prompts
  POST /video-studio/segments/{id}/regenerate-prompt — bump prompt version
  POST /video-studio/bootstrap             — apply migrations + seed templates

The NotebookLM submission/QA bridge was removed in the 2026-05-04 redesign.
The user copies a prompt and runs NotebookLM manually.
"""

from __future__ import annotations

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from services.video_studio import analyze_pdf, pdf_storage
from services.video_studio.db import (
    add_prompt_version,
    ensure_schema,
    get_pdf_by_sha256,
    get_project,
    list_projects,
    save_analysis_result,
    upsert_video_pdf,
)
from services.video_studio.pdf_ingest import ingest_pdf
from services.video_studio.prompt_filler import fill_master_teacher_prompt

router = APIRouter(prefix="/video-studio", tags=["video-studio"])
logger = logging.getLogger(__name__)


# ============================================================
# Schemas
# ============================================================

class RegeneratePromptRequest(BaseModel):
    template_name: Optional[str] = None
    audience: Optional[str] = None
    persona_name: Optional[str] = None
    note: Optional[str] = None


# ============================================================
# Bootstrap
# ============================================================

@router.post("/bootstrap")
async def bootstrap_schema():
    await ensure_schema()
    return {"ok": True}


# ============================================================
# PDF upload + analyze
# ============================================================

@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    audience: Optional[str] = None,
    skip_llm: bool = False,
):
    """
    Upload a PDF, store it sha-keyed in the bucket, and run analysis.

    Idempotent: re-uploading the same PDF (same sha) reuses the cached
    bucket object and the existing project row (segments/prompts are
    rebuilt from the new analysis).
    """
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail=f"expected PDF, got {file.content_type}")

    # Persist upload to a temp file so analysis (which reads from disk) works.
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    try:
        sha = pdf_storage.sha256_of(tmp_path)
        size = tmp_path.stat().st_size

        # Upload to bucket (no-op if already present).
        await asyncio.get_running_loop().run_in_executor(
            None, lambda: pdf_storage.upload(tmp_path, sha=sha)
        )

        # Run analysis off the event loop — heavy CPU + LLM calls.
        result = await asyncio.get_running_loop().run_in_executor(
            None,
            lambda: analyze_pdf(
                tmp_path,
                deck_title=title or (file.filename or "Untitled").rsplit(".", 1)[0],
                audience=audience,
                skip_llm=skip_llm,
            ),
        )

        # Upsert the PDF library row, then save analysis (FK is consistent).
        await upsert_video_pdf(
            sha256=sha,
            original_filename=file.filename or f"{sha[:12]}.pdf",
            byte_size=size,
            page_count=result.total_pages,
        )
        project_id = await save_analysis_result(result, pdf_sha256=sha)
        return {
            "ok": True,
            "project_id": project_id,
            "pdf_sha256": sha,
            "summary": result.to_dict(),
        }
    except Exception:
        logger.exception("upload+analyze failed")
        raise HTTPException(status_code=500, detail="upload+analyze failed")
    finally:
        tmp_path.unlink(missing_ok=True)


# ============================================================
# Projects
# ============================================================

@router.get("/projects")
async def list_projects_endpoint(limit: int = 50):
    return {"projects": await list_projects(limit=limit)}


@router.get("/projects/{project_id}")
async def get_project_endpoint(project_id: str):
    proj = await get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="project not found")
    return proj


@router.get("/pdfs/{sha256}")
async def get_pdf_endpoint(sha256: str):
    rec = await get_pdf_by_sha256(sha256)
    if not rec:
        raise HTTPException(status_code=404, detail="pdf not found")
    return rec


# ============================================================
# Segments — prompt regeneration only (manual NotebookLM flow)
# ============================================================

@router.post("/segments/{segment_id}/regenerate-prompt")
async def regenerate_prompt(segment_id: str, req: RegeneratePromptRequest):
    """
    Re-render a steering prompt with a different template / audience /
    persona. Bumps the prompt version on the segment.
    """
    full = await _get_project_for_segment(segment_id)
    if not full:
        raise HTTPException(status_code=404, detail="segment not found")
    project, segment = full
    cached_pdf = pdf_storage.ensure_local(project["pdf_sha256"])
    pages = ingest_pdf(cached_pdf)

    from services.video_studio.optimizer import Segment as SegmentObj
    import json as _json
    seg_obj = SegmentObj(
        sequence=segment["sequence"],
        start_page=segment["start_page"],
        end_page=segment["end_page"],
        est_seconds=float(segment["est_minutes"]) * 60.0,
        cognitive_load=float(segment["cognitive_load"]),
        page_count=segment["page_count"],
        title=segment.get("title"),
        summary=(segment.get("summary") if isinstance(segment.get("summary"), str)
                 else _json.dumps(segment.get("summary") or {})),
    )
    prompt_pkg = fill_master_teacher_prompt(
        seg_obj,
        pages,
        deck_title=project["title"],
        total_segments=project["recommended_count"],
        audience=req.audience or project["audience"],
        template_name=req.template_name,
        persona_name=req.persona_name,
    )
    est_min = float(segment["est_minutes"])
    target_min = max(2, min(13, int(round(est_min)))) if est_min >= 8 else 10
    version = await add_prompt_version(
        segment_id, prompt_pkg, target_min, note=req.note,
    )
    return {"ok": True, "version": version, "prompt": prompt_pkg}


# ============================================================
# Helpers
# ============================================================

async def _get_project_for_segment(segment_id: str):
    from services.db_service import get_pool
    pool = await get_pool()
    seg = await pool.fetchrow(
        """
        SELECT s.*, p.title AS project_title, p.pdf_sha256,
               p.audience, p.recommended_count
        FROM angela_video_studio.video_segments s
        JOIN angela_video_studio.video_projects p ON p.id = s.project_id
        WHERE s.id = $1
        """,
        segment_id,
    )
    if not seg:
        return None
    project = {
        "title": seg["project_title"],
        "pdf_sha256": seg["pdf_sha256"],
        "audience": seg["audience"],
        "recommended_count": seg["recommended_count"],
    }
    segment = dict(seg)
    return project, segment
