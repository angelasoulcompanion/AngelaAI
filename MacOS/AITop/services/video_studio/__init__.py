"""
Angelora Video Studio — analyze PDFs and generate paste-ready NotebookLM
steering prompts. The lecturer copies each prompt and runs the actual
video generation in NotebookLM manually.

Pipeline:
    PDF → upload (Supabase Storage) → ingest → analyze → optimize
        → fill prompts → persist (segments + prompts in DB)
"""

from .pdf_ingest import ingest_pdf, PageRecord
from .speech_estimator import estimate_page_seconds
from .optimizer import optimize_segments, Segment
from .analyzer import analyze_segments
from .prompt_filler import fill_master_teacher_prompt
from .pipeline import analyze_pdf
from . import pdf_storage

__all__ = [
    "ingest_pdf",
    "PageRecord",
    "estimate_page_seconds",
    "optimize_segments",
    "Segment",
    "analyze_segments",
    "fill_master_teacher_prompt",
    "analyze_pdf",
    "pdf_storage",
]
