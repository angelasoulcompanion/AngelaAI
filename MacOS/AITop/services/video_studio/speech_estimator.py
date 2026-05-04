"""
Speech-time estimator — predicts spoken duration per page.

Calibrated against NotebookLM's actual video pacing (faster than a live
lecturer — narrator runs ~180 wpm and presenter notes are SKIPPED).
Ground truth: Andrew Ng's C1_W1 (85 slides) → user's manual 4-video
plan totals ~49 min, i.e. ~35 s/slide on average.

Per-page contribution:
  - Spoken words:     word_count × (60 / 180) × 0.40  (notes get skipped)
  - Each equation:    +18 s  for symbol-by-symbol walk
  - Each figure:      +10 s  for visual explanation (only content figs)
  - Each code block:  +12 s
  - Each table:       +8  s
  - Section open:     +6  s framing pause
  - Floor:            5  s  (title slides still need a beat)
  - Cap:              90 s  (no single slide drives a video alone)
"""

from __future__ import annotations

from typing import Iterable, List

from .pdf_ingest import PageRecord


WORDS_PER_MINUTE = 180.0     # narrator pace
SPOKEN_FRACTION = 0.40       # presenter skips most slide text
SEC_PER_EQUATION = 18.0
SEC_PER_FIGURE = 10.0
SEC_PER_CODE = 12.0
SEC_PER_TABLE = 8.0
SEC_SECTION_OPEN = 6.0
PAGE_FLOOR_SEC = 5.0
PAGE_CEIL_SEC = 90.0


def estimate_page_seconds(page: PageRecord) -> float:
    sec = page.word_count * 60.0 / WORDS_PER_MINUTE * SPOKEN_FRACTION
    sec += page.equation_count * SEC_PER_EQUATION
    sec += page.figure_count * SEC_PER_FIGURE
    sec += page.code_blocks * SEC_PER_CODE
    if page.has_table:
        sec += SEC_PER_TABLE
    if page.is_section_start:
        sec += SEC_SECTION_OPEN
    return max(min(sec, PAGE_CEIL_SEC), PAGE_FLOOR_SEC)


def estimate_total_seconds(pages: Iterable[PageRecord]) -> float:
    return sum(estimate_page_seconds(p) for p in pages)


def cognitive_load(page: PageRecord) -> float:
    """
    0–10 score — how heavy this page is for a learner.

    Weights tuned against C1_W1: cost-function pages (eq + figure + worked
    example) score ~7–8; intro/agenda pages score ~1–2.
    """
    score = 0.0
    score += min(page.equation_count * 0.8, 5.0)        # cap equations contribution
    score += min(page.figure_count * 0.6, 2.5)
    score += min(page.code_blocks * 0.5, 2.0)
    score += min(page.word_count / 80.0, 2.5)            # dense text
    if page.has_table:
        score += 0.5
    return min(score, 10.0)
