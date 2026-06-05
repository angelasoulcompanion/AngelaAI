#!/usr/bin/env python3
"""normalize_frontmatter.py — canonicalize Angela memory frontmatter to nested style.

Canonical schema (matches the memory spec in the system prompt):

    ---
    name: <slug>
    description: <one-line>
    last_validated: <ISO date>      # kept top-level (wiki_lint reads ^last_validated:)
    metadata:
      type: user | feedback | project | reference
      originSessionId: <id>
      node_type: memory
    ---

Routing rule:
  * top-level keys kept at top: name, description, last_validated
  * everything else (type, originSessionId, node_type, any already-nested child)
    moves under a single `metadata:` block

Idempotent: files already in canonical form are reported "unchanged".
Files with NO frontmatter are skipped + reported (need manual name/description).

Usage:
  python3 tools/normalize_frontmatter.py            # dry-run, prints unified diffs
  python3 tools/normalize_frontmatter.py --apply     # write changes in place
"""
from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path

MEMORY_DIR = Path.home() / ".claude/projects/-Users-davidsamanyaporn-PycharmProjects-AngelaAI/memory"
TOP_LEVEL_KEEP = ["name", "description", "last_validated"]
METADATA_ORDER = ["type", "node_type", "originSessionId"]  # preferred order; extras appended


def split_frontmatter(text: str) -> tuple[list[str], str] | None:
    """Return (frontmatter_lines, body) or None if no leading `---` block."""
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    fm = text[4:end]
    # body starts after the closing '---' line
    rest = text[end + 1:]
    nl = rest.find("\n")
    body = rest[nl + 1:] if nl != -1 else ""
    return fm.splitlines(), body


def parse_fields(fm_lines: list[str]) -> dict[str, str]:
    """Flatten frontmatter into {key: value}. Indented children are hoisted.

    A bare `metadata:` line (no value) is dropped — its children are hoisted by
    the indent rule, then re-grouped on output.
    """
    out: dict[str, str] = {}
    for line in fm_lines:
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip()
        if not key:
            continue
        if key == "metadata" and val == "":
            continue  # block marker — children hoisted via their own lines
        out[key] = val
    return out


def render(fields: dict[str, str]) -> str:
    """Render canonical nested frontmatter from a flat field dict."""
    lines = ["---"]
    for k in TOP_LEVEL_KEEP:
        if k in fields and fields[k] != "":
            lines.append(f"{k}: {fields[k]}")
    # metadata = everything not kept top-level
    meta_keys = [k for k in fields if k not in TOP_LEVEL_KEEP]
    ordered = [k for k in METADATA_ORDER if k in meta_keys]
    ordered += [k for k in meta_keys if k not in METADATA_ORDER]
    if ordered:
        lines.append("metadata:")
        for k in ordered:
            lines.append(f"  {k}: {fields[k]}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def normalize_file(path: Path) -> tuple[str, str] | None:
    """Return (old_text, new_text) if a change is needed, else None.

    Returns the sentinel ('NOFM', '') for files lacking frontmatter.
    """
    old = path.read_text(encoding="utf-8")
    split = split_frontmatter(old)
    if split is None:
        return ("NOFM", "")
    fm_lines, body = split
    fields = parse_fields(fm_lines)
    new_fm = render(fields)
    new = new_fm + body
    if new == old:
        return None
    return (old, new)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry-run)")
    args = ap.parse_args()

    changed, unchanged, nofm = [], [], []
    for path in sorted(MEMORY_DIR.glob("*.md")):
        if path.name == "MEMORY.md":
            continue
        res = normalize_file(path)
        if res is None:
            unchanged.append(path.name)
            continue
        old, new = res
        if old == "NOFM":
            nofm.append(path.name)
            continue
        changed.append(path.name)
        diff = difflib.unified_diff(
            old.splitlines(keepends=True), new.splitlines(keepends=True),
            fromfile=f"a/{path.name}", tofile=f"b/{path.name}",
        )
        sys.stdout.writelines(diff)
        print()
        if args.apply:
            path.write_text(new, encoding="utf-8")

    print("=" * 60)
    print(f"changed:   {len(changed)}")
    print(f"unchanged: {len(unchanged)} (already canonical)")
    print(f"no-frontmatter (skipped, fix manually): {len(nofm)} -> {nofm}")
    print(f"mode: {'APPLIED' if args.apply else 'DRY-RUN (no files written)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
