"""
Pipeline — end-to-end orchestrator: PDF → segments + filled prompts.

Used by both the CLI and the FastAPI router.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional

from .pdf_ingest import ingest_pdf
from .optimizer import (
    Segment,
    alternative_splits,
    optimize_segments,
    segments_from_video_starts,
)
from .analyzer import analyze_segments
from .prompt_filler import fill_master_teacher_prompt
from .speech_estimator import estimate_total_seconds
from .topic_segmenter import detect_section_starts, apply_section_starts


logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    pdf_path: str
    deck_title: str
    audience: str
    total_pages: int
    total_estimated_minutes: float
    recommended_count: int
    alternatives: list
    segments: list  # list of dict (Segment.to_dict + prompts)

    def to_dict(self) -> dict:
        return asdict(self)


def analyze_pdf(
    pdf_path: str | Path,
    *,
    deck_title: Optional[str] = None,
    audience: Optional[str] = None,
    skip_llm: bool = False,
) -> AnalysisResult:
    """
    Run the full pipeline on a PDF.

    Args:
        pdf_path: Path to the source PDF.
        deck_title: Display title (defaults to filename).
        audience: Target audience description (defaults to generic).
        skip_llm: If True, skip the analyzer LLM call (heuristic titles only).
                  Useful for fast iteration during development.
    """
    pdf_path = Path(pdf_path)
    deck_title = deck_title or pdf_path.stem
    audience = audience or "engaged adult learners with relevant background"

    logger.info(f"Ingesting {pdf_path}…")
    pages = ingest_pdf(pdf_path)
    logger.info(f"  {len(pages)} pages extracted.")

    total_seconds = estimate_total_seconds(pages)
    logger.info(f"  Estimated total speech time: {total_seconds/60:.1f} minutes")

    video_starts: Optional[list] = None
    if not skip_llm:
        logger.info("Running topic segmenter (Claude Opus 4.7)…")
        video_starts = detect_section_starts(pages, deck_title=deck_title)
        apply_section_starts(pages, video_starts)
        logger.info(f"  Video starts: {video_starts}")

    logger.info("Running optimizer…")
    if video_starts:
        segments = segments_from_video_starts(pages, video_starts)
    else:
        segments = optimize_segments(pages)
    logger.info(f"  Recommended {len(segments)} segments.")

    if not skip_llm:
        logger.info("Running analyzer (Claude Opus 4.7)…")
        segments = analyze_segments(segments, pages, deck_title=deck_title, audience=audience)
    else:
        logger.info("Skipping LLM analyzer (skip_llm=True).")
        # Heuristic titles only.
        for seg in segments:
            from .analyzer import _heuristic_title
            seg.title = _heuristic_title(seg, pages)
            seg.summary = json.dumps({}, ensure_ascii=False)

    logger.info("Filling steering prompts…")
    seg_dicts = []
    for seg in segments:
        prompt_pkg = fill_master_teacher_prompt(
            seg,
            pages,
            deck_title=deck_title,
            total_segments=len(segments),
            audience=audience,
        )
        d = seg.to_dict()
        d["prompt"] = prompt_pkg
        seg_dicts.append(d)

    alternatives = alternative_splits(pages)

    return AnalysisResult(
        pdf_path=str(pdf_path),
        deck_title=deck_title,
        audience=audience,
        total_pages=len(pages),
        total_estimated_minutes=round(total_seconds / 60.0, 1),
        recommended_count=len(segments),
        alternatives=alternatives,
        segments=seg_dicts,
    )
