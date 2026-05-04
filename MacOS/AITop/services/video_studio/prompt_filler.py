"""
Prompt filler — turns a Segment + analyzer output into a ready-to-paste
NotebookLM steering prompt.

The filler picks a default template based on the segment's profile
(equation density, code density, sequence position) but the UI can
override the choice.
"""

from __future__ import annotations

import json
from typing import List, Optional

from jinja2 import Environment, BaseLoader, StrictUndefined

from .optimizer import Segment
from .pdf_ingest import PageRecord
from .prompt_templates import TEMPLATES, DEFAULT_VISUAL_STYLE, DEFAULT_FORMAT
from .speech_estimator import cognitive_load


_env = Environment(
    loader=BaseLoader(),
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
)


def _structure_for_minutes(target_minutes: int) -> List[dict]:
    """Default 8-slot Explainer structure for a target duration."""
    chunks = [
        ("Hook", 0.06),
        ("Recap of previous video (skip on Video 1)", 0.04),
        ("The big question this video answers", 0.05),
        ("Foundations / minimum mental model", 0.20),
        ("Core concept built up step by step", 0.30),
        ("Worked example or concrete case", 0.18),
        ("Common misconceptions and bigger picture", 0.10),
        ("Take-home + bridge to next video", 0.07),
    ]
    out = []
    cum_min = 0.0
    for label, frac in chunks:
        slot_min = round(target_minutes * frac, 1)
        out.append({
            "t": f"{int(cum_min):02d}:{int(round((cum_min - int(cum_min)) * 60)):02d}",
            "label": f"{label}  (~{slot_min} min)",
        })
        cum_min += slot_min
    return out


def _position_phrase(seq: int, total: int) -> str:
    if total == 1:
        return "Standalone — the one and only video on this material."
    if seq == 1:
        return f"First video of {total}. Sets up the framework the rest of the series builds on."
    if seq == total:
        return f"Final video of {total}. Pays off the series and ties everything together."
    return f"Middle of the series ({seq} of {total}). Build on prior videos; set up what's next."


def _pick_template(segment: Segment, pages_in_segment: List[PageRecord]) -> str:
    """
    Choose template by content profile, NOT by mechanical duration.

    NotebookLM elaborates sparse-but-conceptual decks (e.g. notation
    pages) into full 10-min videos when the steering prompt says so.
    So we pick template based on what the segment IS about:

      - notation / equations / symbols  → walk_through
      - code-heavy                      → walk_through
      - very large segment (>40 slides) → master_teacher (Explainer)
      - tiny review/recap (<=4 pages,
        no equations, no code)          → brief
      - default                         → master_teacher
    """
    eq_total = sum(p.equation_count for p in pages_in_segment)
    code_total = sum(p.code_blocks for p in pages_in_segment)
    n_pages = max(len(pages_in_segment), 1)

    # Title hints (from analyzer) — notation/symbols/equations imply walk_through.
    title = (segment.title or "").lower()
    notation_keywords = (
        "notation", "symbol", "equation", "formula", "math",
        "derivat", "gradient", "cost function", "loss function",
        "model with one variable", "linear regression model",
    )
    has_notation_theme = any(k in title for k in notation_keywords)

    if eq_total >= 3 or code_total >= 4 or has_notation_theme:
        return "walk_through"
    if n_pages <= 4 and eq_total == 0 and code_total == 0:
        return "brief"
    return "master_teacher"


def _target_minutes_for(segment: Segment) -> int:
    """
    Target length to request from NotebookLM.

    Clamp to [8, 13] regardless of mechanical estimate — sparse pedagogical
    units (e.g. 6-slide notation) deserve a full 10-min video because
    NotebookLM expands with hooks, analogies, and worked examples.
    """
    est = segment.est_minutes
    if est >= 8:
        return min(int(round(est)), 13)
    return 10  # default for sparse-but-conceptual segments


def fill_master_teacher_prompt(
    segment: Segment,
    pages: List[PageRecord],
    *,
    deck_title: str,
    total_segments: int,
    audience: str,
    template_name: Optional[str] = None,
    persona_name: Optional[str] = None,
    avoid_topics: Optional[List[str]] = None,
) -> dict:
    """
    Render one steering prompt for a segment.

    Returns: {
        "template_name": str,
        "format": "Explainer" | "Brief" | ...,
        "visual_style": "Whiteboard" | ...,
        "prompt": "<text to paste into NotebookLM>",
    }
    """
    info = json.loads(segment.summary or "{}") if segment.summary else {}
    pages_in_seg = [p for p in pages if segment.start_page <= p.page_num <= segment.end_page]

    chosen_template = template_name or _pick_template(segment, pages_in_seg)
    template_str = TEMPLATES[chosen_template]
    template = _env.from_string(template_str)

    target_minutes = _target_minutes_for(segment)
    headline_question = (
        info.get("learning_objectives", [None])[0]
        if info.get("learning_objectives") else
        f"What is the core idea on pages {segment.page_range}?"
    )

    rendered = template.render(
        deck_title=deck_title,
        audience=audience or "engaged adult learners with relevant background",
        seq=segment.sequence,
        total=total_segments,
        position_phrase=_position_phrase(segment.sequence, total_segments),
        page_range=segment.page_range,
        target_minutes=target_minutes,
        learning_objectives=info.get("learning_objectives", []),
        covers=info.get("covers", []),
        does_not_cover=info.get("does_not_cover", []),
        take_home=info.get("take_home", "") or "(write one sentence the learner will remember next year)",
        bridge_to_next=info.get("bridge_to_next", "") or ("final" if segment.sequence == total_segments else ""),
        structure=_structure_for_minutes(target_minutes),
        avoid_topics=avoid_topics or [],
        headline_question=headline_question,
        persona_name=persona_name or "Walter Lewin (clear, kinetic, demo-driven)",
        length_feel="brief" if segment.est_minutes <= 5 else "standard" if segment.est_minutes <= 12 else "deep dive",
    )

    return {
        "template_name": chosen_template,
        "format": DEFAULT_FORMAT[chosen_template],
        "visual_style": DEFAULT_VISUAL_STYLE[chosen_template],
        "prompt": rendered,
    }
