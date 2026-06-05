"""wiki_lint.py — LLM Wiki LINT for Angela memory (dogfood Phase 0, v2).

Health-check Angela's hand-curated memory wiki at
~/.claude/projects/-Users-davidsamanyaporn-PycharmProjects-AngelaAI/memory/

Runs five passes:
  1. ORPHAN          — files in /memory/ not referenced by MEMORY.md
  2. BROKEN LINKS    — MEMORY.md links pointing to missing files
  3. CROSS-REFS      — links inside any memory file pointing to missing files
  4. DUPLICATES      — pairs of files whose body content is semantically similar.
                       v2 uses Ollama nomic-embed-text (768d) cosine similarity over
                       body text (frontmatter stripped). Embeddings cached to disk.
                       Falls back to difflib if Ollama unavailable.
  5. STALE           — files older than 30 days flagged for revalidation

Usage:
    python3 tools/wiki_lint.py             # human-readable report
    python3 tools/wiki_lint.py --json      # machine-readable
    python3 tools/wiki_lint.py --no-embed  # skip semantic dedup (text-only)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

MEMORY_DIR = Path.home() / ".claude/projects/-Users-davidsamanyaporn-PycharmProjects-AngelaAI/memory"
INDEX_FILE = MEMORY_DIR / "MEMORY.md"
STALE_DAYS = 30
# Behavioral/profile memories don't decay with code — mirror init.py's skip set.
SKIP_STALE_TYPES = {"feedback", "user"}
TEXT_DUPLICATE_THRESHOLD = 0.70
EMBED_DUPLICATE_THRESHOLD = 0.88
OLLAMA_URL = "http://localhost:11434/api/embeddings"
OLLAMA_MODEL = "nomic-embed-text"
CACHE_FILE = Path.home() / ".cache/angela_wiki_lint_embeds.json"

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+\.md)\)")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


@dataclass
class MemoryFile:
    path: Path
    name: str = ""
    description: str = ""
    type: str = ""
    age_days: int = 0
    body: str = ""
    body_sha: str = ""
    outbound_links: list[str] = field(default_factory=list)


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Return (frontmatter dict, body without frontmatter).

    Note: keys are stripped, so nested-style children (e.g. `  type: feedback`
    under a `metadata:` block) are hoisted to top-level keys. This means both the
    flat (`type: feedback`) and nested (`metadata:\n  type: feedback`) frontmatter
    styles resolve `type`/`name`/`description` correctly here — do not "fix" this
    by skipping indented lines or it will regress nested-style files.
    """
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    out = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        out[k.strip()] = v.strip()
    body = text[m.end():].lstrip("\n")
    return out, body


def load_memory(path: Path) -> MemoryFile:
    text = path.read_text(encoding="utf-8", errors="replace")
    fm, body = parse_frontmatter(text)
    age = (datetime.now(tz=timezone.utc).timestamp() - path.stat().st_mtime) / 86400
    return MemoryFile(
        path=path,
        name=fm.get("name", path.stem),
        description=fm.get("description", ""),
        type=fm.get("type", ""),
        age_days=int(age),
        body=body,
        body_sha=hashlib.sha1(body.encode("utf-8")).hexdigest()[:12],
        outbound_links=[m.group(2) for m in LINK_RE.finditer(text)],
    )


def ollama_embed(text: str, timeout: float = 60.0) -> list[float] | None:
    """Call Ollama embeddings API. Returns None on failure."""
    payload = json.dumps({"model": OLLAMA_MODEL, "prompt": text}).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            return data.get("embedding")
    except (urllib.error.URLError, TimeoutError, OSError):
        return None


def load_embed_cache() -> dict[str, list[float]]:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_embed_cache(cache: dict[str, list[float]]) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache), encoding="utf-8")


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def embed_files(files: list[MemoryFile], verbose: bool = True) -> dict[str, list[float]]:
    """Return {filename: embedding}, using cache keyed by body_sha."""
    cache = load_embed_cache()
    out: dict[str, list[float]] = {}
    new_count = 0
    for f in files:
        if f.path.name == "MEMORY.md" or not f.body.strip():
            continue
        cache_key = f.body_sha
        if cache_key in cache:
            out[f.path.name] = cache[cache_key]
            continue
        # Truncate to ~3000 chars (well within nomic context)
        text = (f.description + "\n\n" + f.body)[:3000]
        emb = ollama_embed(text)
        if emb is None:
            if verbose:
                print(f"   ⚠️  embed failed for {f.path.name} — skipping semantic dedup", file=sys.stderr)
            return {}
        cache[cache_key] = emb
        out[f.path.name] = emb
        new_count += 1
        if verbose:
            print(f"   embedded {f.path.name} ({new_count} new)", file=sys.stderr, flush=True)
    save_embed_cache(cache)
    return out


def find_orphans(files: list[MemoryFile], index_text: str) -> list[str]:
    indexed = {m.group(2) for m in LINK_RE.finditer(index_text)}
    return sorted(
        f.path.name for f in files
        if f.path.name != "MEMORY.md" and f.path.name not in indexed
    )


def find_broken_index_links(index_text: str, existing: set[str]) -> list[str]:
    return sorted(
        m.group(2) for m in LINK_RE.finditer(index_text)
        if m.group(2) not in existing
    )


def find_broken_cross_refs(files: list[MemoryFile], existing: set[str]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for f in files:
        if f.path.name == "MEMORY.md":
            continue
        for link in f.outbound_links:
            # ignore http(s) and anchors
            if link.startswith(("http", "#", "/")):
                continue
            if link not in existing:
                out.append((f.path.name, link))
    return sorted(out)


def find_duplicates_text(files: list[MemoryFile]) -> list[tuple[str, str, float]]:
    """Fallback: difflib over descriptions when embeddings unavailable."""
    candidates = [f for f in files if f.description and f.path.name != "MEMORY.md"]
    out: list[tuple[str, str, float]] = []
    for i in range(len(candidates)):
        for j in range(i + 1, len(candidates)):
            a, b = candidates[i], candidates[j]
            ratio = SequenceMatcher(None, a.description.lower(), b.description.lower()).ratio()
            if ratio >= TEXT_DUPLICATE_THRESHOLD:
                out.append((a.path.name, b.path.name, round(ratio, 3)))
    return sorted(out, key=lambda x: -x[2])


def find_duplicates_semantic(embeds: dict[str, list[float]]) -> list[tuple[str, str, float]]:
    """v2: pairwise cosine similarity over body embeddings."""
    names = sorted(embeds.keys())
    out: list[tuple[str, str, float]] = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            sim = cosine(embeds[a], embeds[b])
            if sim >= EMBED_DUPLICATE_THRESHOLD:
                out.append((a, b, round(sim, 3)))
    return sorted(out, key=lambda x: -x[2])


def find_stale(files: list[MemoryFile]) -> list[tuple[str, int]]:
    """Stale = max(mtime_age, last_validated_age) > STALE_DAYS.
    last_validated frontmatter (ISO date) lets us reset the clock without
    touching mtime — the validate-don't-touch rule from CLAUDE.md.

    Skips type=feedback/user (behavioral/profile rules, no code dependency) so
    this matches init.py's SKIP_STALE_TYPES — those memories don't decay.
    """
    today = datetime.now(tz=timezone.utc).date()
    out = []
    for f in files:
        if f.path.name == "MEMORY.md":
            continue
        if f.type.strip().lower() in SKIP_STALE_TYPES:
            continue
        # Parse last_validated if present
        validated_age = f.age_days  # fallback to mtime
        text = f.path.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^last_validated:\s*(\d{4}-\d{2}-\d{2})", text, re.MULTILINE)
        if m:
            try:
                validated_date = datetime.strptime(m.group(1), "%Y-%m-%d").date()
                validated_age = (today - validated_date).days
            except ValueError:
                pass
        effective_age = min(f.age_days, validated_age)
        if effective_age > STALE_DAYS:
            out.append((f.path.name, effective_age))
    return sorted(out, key=lambda x: -x[1])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--json", action="store_true", help="machine-readable JSON output")
    ap.add_argument("--no-embed", action="store_true", help="skip semantic dedup (text-only fallback)")
    args = ap.parse_args()

    if not MEMORY_DIR.exists():
        print(f"❌ memory dir not found: {MEMORY_DIR}", file=sys.stderr)
        return 2

    md_paths = sorted(MEMORY_DIR.glob("*.md"))
    files = [load_memory(p) for p in md_paths]
    existing_names = {p.name for p in md_paths}
    index_text = INDEX_FILE.read_text(encoding="utf-8")

    orphans = find_orphans(files, index_text)
    broken_index = find_broken_index_links(index_text, existing_names)
    broken_xrefs = find_broken_cross_refs(files, existing_names)
    stale = find_stale(files)

    dup_method = "embeddings"
    duplicates: list[tuple[str, str, float]] = []
    if not args.no_embed:
        if not args.json:
            print("🧠 Embedding bodies via Ollama nomic-embed-text…", file=sys.stderr)
        embeds = embed_files(files, verbose=not args.json)
        if embeds:
            duplicates = find_duplicates_semantic(embeds)
        else:
            dup_method = "difflib (fallback)"
            duplicates = find_duplicates_text(files)
    else:
        dup_method = "difflib"
        duplicates = find_duplicates_text(files)

    report = {
        "scanned": len(md_paths),
        "memory_dir": str(MEMORY_DIR),
        "checks": {
            "orphans":            {"count": len(orphans),       "items": orphans},
            "broken_index_links": {"count": len(broken_index),  "items": broken_index},
            "broken_cross_refs":  {"count": len(broken_xrefs),  "items": [{"from": a, "to": b} for a, b in broken_xrefs]},
            "duplicates":         {"count": len(duplicates),    "method": dup_method, "items": [{"a": a, "b": b, "score": r} for a, b, r in duplicates]},
            "stale":              {"count": len(stale),         "items": [{"file": n, "age_days": d} for n, d in stale]},
        },
    }

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    print(f"🔍 Wiki LINT — scanned {len(md_paths)} files in {MEMORY_DIR.name}/\n")

    print(f"📋 Orphans ({len(orphans)}) — files exist but MEMORY.md doesn't index them:")
    if orphans:
        for n in orphans:
            print(f"   ⚠️  {n}")
    else:
        print("   ✓ none")

    print(f"\n❌ Broken links in MEMORY.md ({len(broken_index)}):")
    if broken_index:
        for n in broken_index:
            print(f"   ⚠️  {n}  ← indexed but file missing")
    else:
        print("   ✓ none")

    print(f"\n🔗 Broken cross-references inside files ({len(broken_xrefs)}):")
    if broken_xrefs:
        for a, b in broken_xrefs:
            print(f"   ⚠️  {a:40s} → {b}")
    else:
        print("   ✓ none")

    threshold_label = f"{EMBED_DUPLICATE_THRESHOLD}" if "embed" in dup_method else f"{TEXT_DUPLICATE_THRESHOLD}"
    print(f"\n🔁 Duplicate concepts ({dup_method}, similarity ≥ {threshold_label}):")
    if duplicates:
        for a, b, r in duplicates:
            print(f"   ⚠️  {r:.3f}  {a}\n          ↔  {b}")
    else:
        print("   ✓ none")

    print(f"\n⏰ Stale files (> {STALE_DAYS} days, sorted oldest first):")
    if stale:
        for n, d in stale[:15]:
            print(f"   ⚠️  {d:3d}d  {n}")
        if len(stale) > 15:
            print(f"   … + {len(stale) - 15} more")
    else:
        print("   ✓ none")

    total_issues = (
        len(orphans) + len(broken_index) + len(broken_xrefs)
        + len(duplicates) + len(stale)
    )
    print(f"\n{'='*60}")
    print(f"Total issues: {total_issues}")
    return 1 if (broken_index or broken_xrefs) else 0


if __name__ == "__main__":
    sys.exit(main())
