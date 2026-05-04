"""
Analyzer — uses Claude Opus 4.7 to assign titles, learning objectives,
and bracket-fill content for each segment.

Single batched call per PDF (one prompt covering all segments) to keep
latency low and stay cache-friendly.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

from anthropic import Anthropic

from .optimizer import Segment
from .pdf_ingest import PageRecord

# Resolve secrets via angela_core.database (sync).
_angela_root = str(Path(__file__).resolve().parents[4])
if _angela_root not in sys.path:
    sys.path.insert(0, _angela_root)

logger = logging.getLogger(__name__)

ANALYZER_MODEL = "claude-opus-4-7"
MAX_SAMPLE_CHARS_PER_PAGE = 600  # send compact text per page to fit budget


def _get_anthropic_client() -> Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        try:
            from angela_core.database import get_secret_sync
            api_key = get_secret_sync("anthropic_api_key")
        except Exception as e:
            logger.warning(f"Could not resolve anthropic_api_key from our_secrets: {e}")
    if not api_key:
        raise RuntimeError(
            "anthropic_api_key not found. Set ANTHROPIC_API_KEY or add to our_secrets."
        )
    return Anthropic(api_key=api_key)


def _segment_payload(segments: List[Segment], pages: List[PageRecord]) -> List[dict]:
    page_by_num = {p.page_num: p for p in pages}
    out: List[dict] = []
    for seg in segments:
        chunk_text_parts = []
        for pn in range(seg.start_page, seg.end_page + 1):
            page = page_by_num.get(pn)
            if not page:
                continue
            text = page.text.strip()
            if len(text) > MAX_SAMPLE_CHARS_PER_PAGE:
                text = text[:MAX_SAMPLE_CHARS_PER_PAGE] + "…"
            chunk_text_parts.append(f"[p.{pn}] {text}")
        out.append({
            "sequence": seg.sequence,
            "page_range": seg.page_range,
            "est_minutes": seg.est_minutes,
            "cognitive_load": round(seg.cognitive_load, 1),
            "content_sample": "\n\n".join(chunk_text_parts),
        })
    return out


_ANALYSIS_SYSTEM = """You are an expert instructional designer for short \
teaching videos (<=15 min) generated via NotebookLM.

For each segment of a PDF lecture deck, output:
  - a concise title (≤60 chars)
  - 2–4 specific learning objectives (start with 'the learner can ...')
  - 3–6 bullets summarizing what the segment covers
  - 2–4 bullets the segment EXPLICITLY does NOT cover (deferred to other segments)
  - a one-sentence take-home
  - a one-sentence bridge to the NEXT segment (or 'final' for the last one)

Return ONLY valid JSON, matching the schema in the user message.
No prose outside the JSON. No markdown fences.
"""


def analyze_segments(
    segments: List[Segment],
    pages: List[PageRecord],
    deck_title: Optional[str] = None,
    audience: Optional[str] = None,
) -> List[Segment]:
    """
    Mutates each Segment, filling .title and .summary (the summary is a JSON
    blob the prompt-filler then reads). Returns the same list for chaining.

    If the Anthropic call fails, falls back to heuristic titles so the
    pipeline still produces usable output.
    """
    if not segments:
        return segments

    payload = _segment_payload(segments, pages)
    user_prompt = json.dumps({
        "deck_title": deck_title or "Untitled lecture",
        "audience_hint": audience or "smart adult learners with relevant background",
        "total_segments": len(segments),
        "segments": payload,
        "output_schema": {
            "segments": [{
                "sequence": "int",
                "title": "string",
                "learning_objectives": ["string"],
                "covers": ["string"],
                "does_not_cover": ["string"],
                "take_home": "string",
                "bridge_to_next": "string",
            }]
        }
    }, ensure_ascii=False)

    try:
        client = _get_anthropic_client()
        response = client.messages.create(
            model=ANALYZER_MODEL,
            max_tokens=4000,
            system=_ANALYSIS_SYSTEM,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = "".join(b.text for b in response.content if hasattr(b, "text"))
        data = json.loads(text)
        for seg, info in zip(segments, data.get("segments", [])):
            seg.title = info.get("title")
            seg.summary = json.dumps(info, ensure_ascii=False)
        return segments
    except Exception as e:
        logger.warning(f"Analyzer LLM call failed: {e}. Falling back to heuristic titles.")
        for seg in segments:
            seg.title = _heuristic_title(seg, pages)
            seg.summary = json.dumps({
                "sequence": seg.sequence,
                "title": seg.title,
                "learning_objectives": [],
                "covers": [],
                "does_not_cover": [],
                "take_home": "",
                "bridge_to_next": "",
            }, ensure_ascii=False)
        return segments


def _heuristic_title(seg: Segment, pages: List[PageRecord]) -> str:
    page_by_num = {p.page_num: p for p in pages}
    head_page = page_by_num.get(seg.start_page)
    if head_page and head_page.headings:
        return head_page.headings[0][:60]
    return f"Segment {seg.sequence} (p.{seg.page_range})"
