"""
PDF ingest — extract per-page records (text, equations, figures, code, headings).

Output: list of PageRecord, one per page, with structural features
that the optimizer and analyzer use downstream.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional

import fitz  # pymupdf
import pdfplumber


# Equation/symbol patterns — matches typical lecture-slide notation.
# Hits: f_w,b(x), Σ, ∂J/∂w, x², ŷ, α, ≈, ≤, ≥, ∇, integrals, fractions.
_EQ_SYMBOLS = re.compile(
    r"[ΣΠ∑∏∫∂∇αβγδεθλμπσφψω→←⇒⇐≈≠≤≥±×÷√∞°^_]|"
    r"\b[fghJL]\s*[_^]\s*[a-zA-Z]|"
    r"\b\d+\s*[+\-*/]\s*\d+\b"
)

# Code/notation hints (NumPy / PyTorch / common ML APIs).
_CODE_HINTS = re.compile(
    r"\b(numpy|np\.|torch\.|sklearn|pandas|pd\.|nn\.Linear|MSELoss|"
    r"def\s+\w+\s*\(|import\s+\w+|return\s+\w+|y_hat|alpha|epoch)\b",
    re.IGNORECASE,
)

# Heading detection — short uppercase-ish lines, or numbered sections.
_HEADING_HINT = re.compile(r"^([0-9]+\.|[A-Z][A-Z][A-Z\s\-:]{3,}|[A-Z][\w\s]{0,40})$")

# Words to estimate speaking time.
_WORD_RE = re.compile(r"\b\w+\b")


@dataclass
class PageRecord:
    page_num: int  # 1-indexed
    text: str
    word_count: int
    headings: List[str] = field(default_factory=list)
    equation_count: int = 0
    figure_count: int = 0
    code_blocks: int = 0
    has_table: bool = False
    is_section_start: bool = False  # heuristic: short text + heading-ish

    def to_dict(self) -> dict:
        return asdict(self)


def _extract_headings(text: str) -> List[str]:
    headings: List[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or len(line) > 80:
            continue
        if _HEADING_HINT.match(line):
            headings.append(line)
    return headings


def _count_equations(text: str) -> int:
    return len(_EQ_SYMBOLS.findall(text))


def _count_code(text: str) -> int:
    return len(_CODE_HINTS.findall(text))


def _is_section_start(text: str, headings: List[str], word_count: int) -> bool:
    """
    Strict section-start detection — only fires for true section/title slides.

    A page is a section start when it is a sparse title slide:
    very few words AND a heading-shaped line. Dense content slides that
    happen to begin with a section name don't qualify.
    """
    if not headings or word_count > 18:
        return False
    # Title-shaped: heading line covers most of the (sparse) content.
    head = headings[0]
    return len(head) >= 4 and word_count <= 18


def ingest_pdf(pdf_path: str | Path) -> List[PageRecord]:
    """
    Extract a structured record per page.

    Combines pdfplumber (text + tables) with pymupdf (images/figures).
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    # Pass 1 — pymupdf for content-image counts (filter out template logos).
    # Logos / repeated header-footer marks appear as the SAME xref on most
    # pages. Anything that recurs on >40% of pages is template chrome.
    figure_counts: dict[int, int] = {}
    doc = fitz.open(pdf_path)
    try:
        n = len(doc)
        xref_pages: dict[int, set[int]] = {}
        per_page: dict[int, list[tuple[int, float]]] = {}
        for i in range(n):
            page = doc[i]
            entries: list[tuple[int, float]] = []
            page_rect = page.rect
            page_area = max(page_rect.width * page_rect.height, 1.0)
            for img in page.get_images(full=True):
                xref = img[0]
                width = img[2] or 0
                height = img[3] or 0
                rel_area = (width * height) / page_area
                entries.append((xref, rel_area))
                xref_pages.setdefault(xref, set()).add(i)
            per_page[i] = entries
        recurrence_threshold = max(int(n * 0.4), 3)
        recurring_xrefs = {x for x, pgs in xref_pages.items() if len(pgs) >= recurrence_threshold}
        for i, entries in per_page.items():
            count = 0
            for xref, rel_area in entries:
                if xref in recurring_xrefs:
                    continue
                # Drop tiny inline icons (<0.5% of page area).
                if rel_area < 0.005:
                    continue
                count += 1
            figure_counts[i + 1] = count
    finally:
        doc.close()

    # Pass 2 — pdfplumber for text + tables.
    records: List[PageRecord] = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            tables = page.find_tables() if page.find_tables else []
            headings = _extract_headings(text)
            word_count = len(_WORD_RE.findall(text))
            eq = _count_equations(text)
            code = _count_code(text)
            rec = PageRecord(
                page_num=i,
                text=text,
                word_count=word_count,
                headings=headings,
                equation_count=eq,
                figure_count=figure_counts.get(i, 0),
                code_blocks=code,
                has_table=bool(tables),
                is_section_start=_is_section_start(text, headings, word_count),
            )
            records.append(rec)

    return records
