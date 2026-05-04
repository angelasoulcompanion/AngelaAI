"""
Video split optimizer — DP that partitions PDF pages into video segments.

Constraints:
  - 8 min ≤ each segment ≤ 13 min (buffer below 15-min hard cap)
  - Cuts prefer to fall on section_start boundaries
  - Cognitive-load is balanced across segments where possible

Cost minimized:
  primary:    number of segments (fewer is better, until duration breaks)
  secondary:  total duration penalty (over/under target)
  tertiary:   boundary penalty (cutting mid-section)
  quaternary: load-imbalance penalty
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Tuple

from .pdf_ingest import PageRecord
from .speech_estimator import (
    estimate_page_seconds,
    cognitive_load,
)


# Tuning knobs — calibrated against C1_W1 (target = 4 segments).
MIN_SEC = 8 * 60        # 8 minutes — anything shorter feels like a fragment
MAX_SEC = 13 * 60       # 13 minutes — leaves headroom under 15-min cap
TARGET_SEC = 11 * 60    # 11 minutes — sweet spot for explainer videos
HARD_CAP_SEC = 15 * 60

PENALTY_BOUNDARY = 240.0  # sec-equivalent for cutting mid-section (hard discourage)
PENALTY_LOAD_VAR = 0.5    # weight on load variance across segments
PER_SEGMENT_OVERHEAD = 240.0  # discourages excessive segment count (~4 min equiv)


@dataclass
class Segment:
    sequence: int            # 1-indexed
    start_page: int          # 1-indexed inclusive
    end_page: int            # 1-indexed inclusive
    est_seconds: float
    cognitive_load: float    # average load across pages
    page_count: int
    title: Optional[str] = None
    summary: Optional[str] = None
    cuts_mid_section: bool = False

    @property
    def est_minutes(self) -> float:
        return round(self.est_seconds / 60.0, 1)

    @property
    def page_range(self) -> str:
        return f"{self.start_page}-{self.end_page}"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["est_minutes"] = self.est_minutes
        d["page_range"] = self.page_range
        return d


def _duration_penalty(seconds: float) -> float:
    """0 inside [MIN, MAX], grows quickly outside."""
    if seconds < MIN_SEC:
        return (MIN_SEC - seconds) ** 2 / 60.0
    if seconds > MAX_SEC:
        return (seconds - MAX_SEC) ** 2 / 60.0
    # mild pull toward TARGET
    return abs(seconds - TARGET_SEC) * 0.05


def _segment_metrics(pages: List[PageRecord], i: int, j: int) -> Tuple[float, float, bool]:
    """For pages[i..j-1]: (est_seconds, avg_load, cuts_mid_section)."""
    chunk = pages[i:j]
    secs = sum(estimate_page_seconds(p) for p in chunk)
    loads = [cognitive_load(p) for p in chunk]
    avg_load = sum(loads) / len(loads) if loads else 0.0
    # If the next page (j) exists and is NOT a section start, cutting here is mid-section.
    cuts_mid = j < len(pages) and not pages[j].is_section_start
    return secs, avg_load, cuts_mid


def segments_from_video_starts(
    pages: List[PageRecord],
    video_starts: List[int],
) -> List[Segment]:
    """
    Build segments directly from LLM-proposed video boundaries.

    When the LLM names video starts (after reading the deck content),
    those are PEDAGOGICAL units — the duration estimate is only a sanity
    check. NotebookLM will elaborate sparse slides with hooks, analogies,
    and worked examples to fit the requested target length.

    Only the 15-min HARD CAP triggers a mechanical split: if any LLM-
    proposed video would exceed 15 min, we DP-split it within those
    page bounds.
    """
    n = len(pages)
    if n == 0:
        return []
    starts = sorted(set(s for s in video_starts if 1 <= s <= n))
    if not starts or starts[0] != 1:
        starts = [1] + [s for s in starts if s != 1]
    bounds = starts + [n + 1]

    segments: List[Segment] = []
    seq = 1
    for s, e in zip(bounds, bounds[1:]):
        i = s - 1            # 0-indexed inclusive
        j = e - 1            # 0-indexed exclusive
        secs, avg_load, _ = _segment_metrics(pages, i, j)
        if secs > HARD_CAP_SEC and (j - i) > 1:
            # Section is too long even with elaboration — DP-split it.
            sub = _dp_split_pages(pages[i:j])
            for sub_i, sub_j in sub:
                ss, ll, cuts = _segment_metrics(pages, i + sub_i, i + sub_j)
                segments.append(Segment(
                    sequence=seq,
                    start_page=pages[i + sub_i].page_num,
                    end_page=pages[i + sub_j - 1].page_num,
                    est_seconds=ss,
                    cognitive_load=ll,
                    page_count=sub_j - sub_i,
                    cuts_mid_section=cuts,
                ))
                seq += 1
        else:
            segments.append(Segment(
                sequence=seq,
                start_page=pages[i].page_num,
                end_page=pages[j - 1].page_num,
                est_seconds=secs,
                cognitive_load=avg_load,
                page_count=j - i,
                cuts_mid_section=False,
            ))
            seq += 1
    return segments


def _dp_split_pages(sub_pages: List[PageRecord]) -> List[tuple]:
    """Internal DP for splitting an oversized section. Returns list of (i, j)."""
    n = len(sub_pages)
    INF = float("inf")
    cost = [INF] * (n + 1)
    cost[0] = 0.0
    parent = [-1] * (n + 1)
    for j in range(1, n + 1):
        for i in range(0, j):
            secs, _, cuts_mid = _segment_metrics(sub_pages, i, j)
            if secs > HARD_CAP_SEC and (j - i) > 1:
                continue
            seg_cost = _duration_penalty(secs) + PER_SEGMENT_OVERHEAD
            if cuts_mid:
                seg_cost += PENALTY_BOUNDARY
            total = cost[i] + seg_cost
            if total < cost[j]:
                cost[j] = total
                parent[j] = i
    boundaries = []
    j = n
    while j > 0:
        i = parent[j]
        boundaries.append((i, j))
        j = i
    boundaries.reverse()
    return boundaries


def optimize_segments(pages: List[PageRecord]) -> List[Segment]:
    """
    Run DP to split pages into segments.

    Returns segments in reading order (sequence 1..N).
    """
    n = len(pages)
    if n == 0:
        return []

    # Force a section_start at page 1 — the deck always starts at page 1.
    pages_marked = list(pages)
    # cost[i] = best total cost to cover pages[0..i-1]
    INF = float("inf")
    cost = [INF] * (n + 1)
    cost[0] = 0.0
    parent = [-1] * (n + 1)

    for j in range(1, n + 1):
        for i in range(0, j):
            secs, avg_load, cuts_mid = _segment_metrics(pages_marked, i, j)
            # Hard cap — never allow a segment over 15 minutes.
            if secs > HARD_CAP_SEC and (j - i) > 1:
                continue
            seg_cost = _duration_penalty(secs)
            if cuts_mid:
                seg_cost += PENALTY_BOUNDARY
            # Reward heavier topics getting their own segment by softly
            # pulling load-weighted seconds toward TARGET.
            seg_cost += avg_load * PENALTY_LOAD_VAR
            # Per-segment overhead — discourages excessive splitting.
            seg_cost += PER_SEGMENT_OVERHEAD
            total = cost[i] + seg_cost
            if total < cost[j]:
                cost[j] = total
                parent[j] = i

    # Backtrack to recover boundaries.
    boundaries: List[Tuple[int, int]] = []
    j = n
    while j > 0:
        i = parent[j]
        boundaries.append((i, j))
        j = i
    boundaries.reverse()

    segments: List[Segment] = []
    for seq, (i, j) in enumerate(boundaries, start=1):
        secs, avg_load, _ = _segment_metrics(pages_marked, i, j)
        cuts_mid = j < n and not pages_marked[j].is_section_start
        seg = Segment(
            sequence=seq,
            start_page=pages_marked[i].page_num,
            end_page=pages_marked[j - 1].page_num,
            est_seconds=secs,
            cognitive_load=avg_load,
            page_count=j - i,
            cuts_mid_section=cuts_mid,
        )
        segments.append(seg)
    return segments


def alternative_splits(pages: List[PageRecord]) -> List[dict]:
    """
    Produce a few candidate splits at fixed segment counts so the UI
    can show 'what if 3? what if 5?' tradeoffs alongside the optimum.
    """
    n = len(pages)
    if n == 0:
        return []

    optimal = optimize_segments(pages)
    optimal_count = len(optimal)
    candidates = []

    for target_count in sorted({optimal_count - 1, optimal_count, optimal_count + 1}):
        if target_count < 1 or target_count > n:
            continue
        # Equal-time split as a baseline.
        total = sum(estimate_page_seconds(p) for p in pages)
        chunk_target = total / target_count
        running = 0.0
        boundaries = [0]
        for idx, p in enumerate(pages):
            running += estimate_page_seconds(p)
            if running >= chunk_target * len(boundaries) and len(boundaries) < target_count:
                boundaries.append(idx + 1)
        boundaries.append(n)
        segs = []
        max_min = 0.0
        any_over_cap = False
        for seq, (i, j) in enumerate(zip(boundaries, boundaries[1:]), start=1):
            secs, _, _ = _segment_metrics(pages, i, j)
            mins = secs / 60.0
            max_min = max(max_min, mins)
            any_over_cap = any_over_cap or mins > 15.0
            segs.append({
                "sequence": seq,
                "page_range": f"{pages[i].page_num}-{pages[j - 1].page_num}",
                "est_minutes": round(mins, 1),
            })
        tradeoff = "✓ optimal" if target_count == optimal_count else (
            "exceeds 15-min cap" if any_over_cap else
            "shorter videos, more fragments" if target_count > optimal_count else
            "fewer videos but longest may feel rushed"
        )
        candidates.append({
            "count": target_count,
            "max_minutes": round(max_min, 1),
            "tradeoff": tradeoff,
            "segments": segs,
        })
    return candidates
