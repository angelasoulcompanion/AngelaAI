#!/usr/bin/env python3
"""
Angelora Video Studio — CLI for analyzing PDFs and generating NotebookLM prompts.

Usage:
    python3 -m scripts.video_studio_cli analyze  <pdf_path> [--audience "..."] [--skip-llm]
    python3 -m scripts.video_studio_cli prompts  <pdf_path> [--out-dir DIR]
    python3 -m scripts.video_studio_cli save     <pdf_path> [--bootstrap]
                                                 (uploads PDF to bucket + DB)
    python3 -m scripts.video_studio_cli status
    python3 -m scripts.video_studio_cli validate <pdf_path> --expected N
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Ensure AITop root and AngelaAI root are importable.
_AITOP_ROOT = Path(__file__).resolve().parent.parent
_ANGELA_ROOT = _AITOP_ROOT.parent.parent
for p in (str(_AITOP_ROOT), str(_ANGELA_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from services.video_studio import analyze_pdf  # noqa: E402


def cmd_analyze(args: argparse.Namespace) -> int:
    result = analyze_pdf(
        args.pdf,
        audience=args.audience,
        deck_title=args.title,
        skip_llm=args.skip_llm,
    )
    out = result.to_dict()
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    print(f"\n📚  {result.deck_title}")
    print(f"     {result.total_pages} pages · ~{result.total_estimated_minutes} min total speech")
    print(f"     Audience: {result.audience}")
    print(f"\n🎬  Recommended split: {result.recommended_count} videos\n")
    print(f"  {'#':<3}{'Title':<55}{'Pages':<10}{'Min':<6}{'Load':<6}")
    print(f"  {'─'*3:<3}{'─'*53:<55}{'─'*8:<10}{'─'*4:<6}{'─'*4:<6}")
    for seg in result.segments:
        title = (seg.get("title") or "")[:54]
        flag = " ⚠" if seg.get("cuts_mid_section") else ""
        print(f"  {seg['sequence']:<3}{title:<55}{seg['page_range']:<10}{seg['est_minutes']:<6}{seg['cognitive_load']:<6.1f}{flag}")
    print()
    print("Alternatives:")
    for alt in result.alternatives:
        print(f"  {alt['count']} videos — max {alt['max_minutes']} min — {alt['tradeoff']}")
    return 0


def cmd_prompts(args: argparse.Namespace) -> int:
    result = analyze_pdf(
        args.pdf,
        audience=args.audience,
        deck_title=args.title,
        skip_llm=args.skip_llm,
    )
    out_dir = Path(args.out_dir or f"prompts_{Path(args.pdf).stem}")
    out_dir.mkdir(parents=True, exist_ok=True)
    # Remove stale prompts from previous runs so renamed segments don't pile up.
    for old in out_dir.glob("video_*.md"):
        old.unlink()
    stale_summary = out_dir / "_summary.json"
    if stale_summary.exists():
        stale_summary.unlink()

    summary = {"deck": result.deck_title, "videos": []}
    for seg in result.segments:
        prompt_pkg = seg["prompt"]
        fname = f"video_{seg['sequence']:02d}_{(seg.get('title') or 'segment').replace(' ', '_')[:40]}.md"
        path = out_dir / fname
        header = (
            f"# Video {seg['sequence']} — {seg.get('title')}\n\n"
            f"- Pages: {seg['page_range']}  ({seg['page_count']} slides)\n"
            f"- Est. minutes: {seg['est_minutes']}\n"
            f"- Cognitive load: {seg['cognitive_load']:.1f}\n"
            f"- Template: {prompt_pkg['template_name']}\n"
            f"- NotebookLM Format: {prompt_pkg['format']}\n"
            f"- NotebookLM Visual Style: {prompt_pkg['visual_style']}\n\n"
            "## Steering Prompt — paste this into NotebookLM\n\n"
        )
        path.write_text(header + prompt_pkg["prompt"], encoding="utf-8")
        summary["videos"].append({
            "sequence": seg["sequence"],
            "title": seg.get("title"),
            "page_range": seg["page_range"],
            "est_minutes": seg["est_minutes"],
            "file": str(path),
        })

    summary_path = out_dir / "_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Wrote {len(result.segments)} prompts to {out_dir}/")
    print(f"   Summary: {summary_path}")
    return 0


def cmd_save(args: argparse.Namespace) -> int:
    """
    Upload PDF to Supabase Storage bucket, analyze, and persist segments+prompts.
    Idempotent: same sha256 reuses the bucket object and updates the project row.
    """
    import asyncio
    from services.video_studio import pdf_storage
    from services.video_studio.db import (
        ensure_schema, save_analysis_result, upsert_video_pdf,
    )
    from services.db_service import init_pool, close_pool

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return 1

    async def run() -> str:
        await init_pool()
        if args.bootstrap:
            await ensure_schema()

        sha = pdf_storage.sha256_of(pdf_path)
        size = pdf_path.stat().st_size
        pdf_storage.upload(pdf_path, sha=sha)

        result = analyze_pdf(
            pdf_path,
            audience=args.audience,
            deck_title=args.title,
            skip_llm=args.skip_llm,
        )
        await upsert_video_pdf(
            sha256=sha,
            original_filename=pdf_path.name,
            byte_size=size,
            page_count=result.total_pages,
        )
        project_id = await save_analysis_result(result, pdf_sha256=sha)
        await close_pool()
        return project_id

    project_id = asyncio.run(run())
    print(f"✅ Saved project {project_id} (PDF in bucket video_studio_pdfs).")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    import asyncio
    from services.video_studio.db import list_projects, get_project
    from services.db_service import init_pool, close_pool

    async def run():
        await init_pool()
        try:
            projects = await list_projects(limit=20)
            details = []
            for p in projects:
                details.append(await get_project(str(p["id"])))
            return details
        finally:
            await close_pool()

    details = asyncio.run(run())
    if not details:
        print("(no projects)")
        return 0
    for d in details:
        proj = d["project"]
        print(f"\n📚  {proj['title']}  ({proj['recommended_count']} videos, {proj['status']})")
        print(f"     ID:  {proj['id']}")
        print(f"     PDF: {proj['original_filename']} ({proj['byte_size']} bytes, sha {proj['pdf_sha256'][:12]}…)")
        for s in d["segments"]:
            tag = {"pending": "·", "prompt_ready": "📝", "analyzed": "📚"}.get(s["status"], "?")
            print(f"   {tag} Seq {s['sequence']}: pp.{s['start_page']}-{s['end_page']:<3}  {s['title']}  [{s['status']}]")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    result = analyze_pdf(args.pdf, skip_llm=True)
    actual = result.recommended_count
    expected = args.expected
    pass_ = actual == expected
    status = "✅ PASS" if pass_ else "❌ FAIL"
    print(f"{status}  {Path(args.pdf).name}")
    print(f"  Expected: {expected} segments")
    print(f"  Actual:   {actual} segments")
    print(f"  Total:    {result.total_estimated_minutes} min ({result.total_pages} pages)")
    for seg in result.segments:
        flag = " ⚠ mid-section" if seg.get("cuts_mid_section") else ""
        print(f"    Seg {seg['sequence']}: pp.{seg['page_range']:<10}  ~{seg['est_minutes']} min  load {seg['cognitive_load']:.1f}{flag}")
    return 0 if pass_ else 1


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(message)s",
    )
    parser = argparse.ArgumentParser(prog="video_studio_cli")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_analyze = sub.add_parser("analyze", help="Show recommended segments")
    p_analyze.add_argument("pdf")
    p_analyze.add_argument("--audience", default=None)
    p_analyze.add_argument("--title", default=None)
    p_analyze.add_argument("--skip-llm", action="store_true")
    p_analyze.add_argument("--json", action="store_true")
    p_analyze.set_defaults(func=cmd_analyze)

    p_prompts = sub.add_parser("prompts", help="Write filled steering prompts to files")
    p_prompts.add_argument("pdf")
    p_prompts.add_argument("--audience", default=None)
    p_prompts.add_argument("--title", default=None)
    p_prompts.add_argument("--skip-llm", action="store_true")
    p_prompts.add_argument("--out-dir", default=None)
    p_prompts.set_defaults(func=cmd_prompts)

    p_save = sub.add_parser("save", help="Upload PDF + analyze + persist to Supabase")
    p_save.add_argument("pdf")
    p_save.add_argument("--audience", default=None)
    p_save.add_argument("--title", default=None)
    p_save.add_argument("--skip-llm", action="store_true")
    p_save.add_argument("--bootstrap", action="store_true",
                        help="Apply schema migrations + seed templates first")
    p_save.set_defaults(func=cmd_save)

    p_validate = sub.add_parser("validate", help="Assert recommended segment count")
    p_validate.add_argument("pdf")
    p_validate.add_argument("--expected", type=int, required=True)
    p_validate.set_defaults(func=cmd_validate)

    p_status = sub.add_parser("status", help="Show all projects and segments")
    p_status.set_defaults(func=cmd_status)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
