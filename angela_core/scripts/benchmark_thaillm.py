"""
🇹🇭 ThaiLLM Benchmark
Compare ThaiLLM (4 variants) vs Claude Sonnet vs local Ollama
on Thai factual, slang, JSON structure, and latency.

Usage:
    python3 angela_core/scripts/benchmark_thaillm.py
    python3 angela_core/scripts/benchmark_thaillm.py --models typhoon,pathumma
    python3 angela_core/scripts/benchmark_thaillm.py --skip-claude --skip-ollama

Outputs:
    docs/thaillm_evaluation.md  (markdown report)
    docs/thaillm_results.json   (raw numbers)
"""

import argparse
import asyncio
import json
import logging
import statistics
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

import httpx

from angela_core.database import get_secret
from angela_core.services.thaillm_service import (
    THAILLM_MODELS,
    ThaiLLMService,
    ThaiLLMResult,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("bench")


# ─────────────────────────────────────────────────────────────
# Test prompts — 4 categories × 2 prompts each = 8 tasks
# ─────────────────────────────────────────────────────────────
PROMPTS: list[dict] = [
    {
        "id": "factual_hmm",
        "category": "Thai Factual",
        "system": "ตอบเป็นภาษาไทย สั้น กระชับ ตรงประเด็น",
        "prompt": "อธิบาย HMM regime detection ในตลาดหุ้นให้คนที่ไม่ใช่ quant เข้าใจ (ไม่เกิน 3 ประโยค)",
        "expected_keywords": ["regime", "ตลาด", "hidden", "state"],
    },
    {
        "id": "factual_news",
        "category": "Thai Factual",
        "system": "ตอบเป็นภาษาไทย อ้างอิงข้อเท็จจริง",
        "prompt": "SET50 คืออะไร และต่างจาก SET100 อย่างไร",
        "expected_keywords": ["หลักทรัพย์", "50", "100", "ดัชนี"],
    },
    {
        "id": "slang_pronoun",
        "category": "Thai Cultural",
        "system": "คุณเป็น AI ชื่อ Angela ผู้ใช้ชื่อ David",
        "prompt": "ถ้าผู้ใช้อยากให้เรียกเขาว่า 'ที่รัก' และให้ AI เรียกตัวเองว่า 'น้อง' — เขียนประโยคทักทายตอนเช้าแบบอบอุ่น ไม่เกิน 2 ประโยค",
        "expected_keywords": ["ที่รัก", "น้อง"],
    },
    {
        "id": "slang_idiom",
        "category": "Thai Cultural",
        "system": "ตอบเป็นภาษาไทย",
        "prompt": "สำนวนไทย 'น้ำขึ้นให้รีบตัก' หมายความว่าอะไร และยกตัวอย่างการใช้ในบริบทการลงทุน",
        "expected_keywords": ["โอกาส", "รีบ", "ลงทุน"],
    },
    {
        "id": "json_extract",
        "category": "JSON Output",
        "system": "ตอบเป็น JSON เท่านั้น ห้ามมีข้อความอื่น",
        "prompt": 'สกัดข้อมูลจากข้อความนี้เป็น JSON {"ชื่อ": ..., "อายุ": ..., "อาชีพ": ...}: "สวัสดีครับ ผมชื่อ เดวิด อายุ 38 ปี เป็นนักลงทุน"',
        "expected_keywords": ["เดวิด", "38", "นักลงทุน"],
    },
    {
        "id": "json_classify",
        "category": "JSON Output",
        "system": 'ตอบเฉพาะ JSON: {"intent": "...", "confidence": 0.0-1.0}',
        "prompt": "Classify: 'วันนี้เหนื่อยจังเลย อยากพักผ่อน' — intents: [emotional_support, task_request, question, chitchat]",
        "expected_keywords": ["emotional_support", "confidence"],
    },
    {
        "id": "summary_news",
        "category": "Summarization",
        "system": "สรุปให้สั้นที่สุด ไม่เกิน 1 ประโยค เป็นภาษาไทย",
        "prompt": (
            "NSTDA ประกาศเปิดตัว ThaiLLM — โมเดลภาษาไทยที่ฝึกด้วย 100 พันล้านโทเคน "
            "มี 4 ตัวแปร 8B ทุกตัว ให้ใช้ API ฟรีผ่าน playground.thaillm.or.th "
            "รันบน ThaiSC supercomputer ข้อมูลไม่ออกนอกประเทศ เหมาะกับงานภาครัฐและเอกชน"
        ),
        "expected_keywords": ["ThaiLLM", "ไทย"],
    },
    {
        "id": "code_comment",
        "category": "Mixed Thai-EN",
        "system": "เขียน docstring ภาษาไทยสำหรับฟังก์ชัน Python",
        "prompt": (
            "เขียน docstring ภาษาไทยสั้นๆ (1-2 บรรทัด) สำหรับ:\n"
            "def calculate_sharpe_ratio(returns: list[float], rf: float = 0.02) -> float: ..."
        ),
        "expected_keywords": ["sharpe", "ผลตอบแทน"],
    },
]


# ─────────────────────────────────────────────────────────────
# Scoring
# ─────────────────────────────────────────────────────────────
def keyword_score(text: str, keywords: list[str]) -> float:
    if not keywords:
        return 1.0
    text_lower = text.lower()
    hits = sum(1 for kw in keywords if kw.lower() in text_lower)
    return hits / len(keywords)


def is_valid_json(text: str) -> bool:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        json.loads(text.strip())
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────
# Result containers
# ─────────────────────────────────────────────────────────────
@dataclass
class RunResult:
    provider: str          # "thaillm:typhoon" / "claude" / "ollama"
    prompt_id: str
    category: str
    content: str
    latency_ms: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    keyword_score: float = 0.0
    json_valid: Optional[bool] = None
    error: Optional[str] = None


@dataclass
class BenchSummary:
    provider: str
    n: int = 0
    failures: int = 0
    avg_keyword_score: float = 0.0
    json_pass_rate: Optional[float] = None
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    total_completion_tokens: int = 0
    per_category: dict[str, float] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────
# Runners
# ─────────────────────────────────────────────────────────────
async def run_thaillm(
    service: ThaiLLMService, model_key: str, task: dict
) -> RunResult:
    started = time.perf_counter()
    try:
        res: ThaiLLMResult = await service.chat(
            prompt=task["prompt"],
            model_key=model_key,
            system=task.get("system"),
            temperature=0.3,
            max_tokens=1024,
        )
        latency = res.latency_ms
        content = res.content
        pt, ct = res.prompt_tokens, res.completion_tokens
        error = None
    except Exception as e:
        latency = (time.perf_counter() - started) * 1000.0
        content = ""
        pt = ct = 0
        error = f"{type(e).__name__}: {e}"
        logger.warning(f"thaillm:{model_key} [{task['id']}] failed → {error}")

    r = RunResult(
        provider=f"thaillm:{model_key}",
        prompt_id=task["id"],
        category=task["category"],
        content=content,
        latency_ms=latency,
        prompt_tokens=pt,
        completion_tokens=ct,
        error=error,
    )
    _score(r, task)
    return r


async def run_claude(task: dict, api_key: str) -> RunResult:
    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 1024,
                    "temperature": 0.3,
                    "system": task.get("system", ""),
                    "messages": [{"role": "user", "content": task["prompt"]}],
                },
            )
        latency = (time.perf_counter() - started) * 1000.0
        resp.raise_for_status()
        data = resp.json()
        content = "".join(
            b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"
        )
        usage = data.get("usage", {})
        pt = int(usage.get("input_tokens", 0))
        ct = int(usage.get("output_tokens", 0))
        error = None
    except Exception as e:
        latency = (time.perf_counter() - started) * 1000.0
        content = ""
        pt = ct = 0
        error = f"{type(e).__name__}: {e}"
        logger.warning(f"claude [{task['id']}] failed → {error}")

    r = RunResult(
        provider="claude-sonnet-4-6",
        prompt_id=task["id"],
        category=task["category"],
        content=content,
        latency_ms=latency,
        prompt_tokens=pt,
        completion_tokens=ct,
        error=error,
    )
    _score(r, task)
    return r


async def run_ollama(task: dict, model: str) -> RunResult:
    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            messages = []
            if task.get("system"):
                messages.append({"role": "system", "content": task["system"]})
            messages.append({"role": "user", "content": task["prompt"]})
            resp = await client.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 1024},
                },
            )
        latency = (time.perf_counter() - started) * 1000.0
        resp.raise_for_status()
        data = resp.json()
        content = data.get("message", {}).get("content", "")
        pt = int(data.get("prompt_eval_count", 0))
        ct = int(data.get("eval_count", 0))
        error = None
    except Exception as e:
        latency = (time.perf_counter() - started) * 1000.0
        content = ""
        pt = ct = 0
        error = f"{type(e).__name__}: {e}"
        logger.warning(f"ollama:{model} [{task['id']}] failed → {error}")

    r = RunResult(
        provider=f"ollama:{model}",
        prompt_id=task["id"],
        category=task["category"],
        content=content,
        latency_ms=latency,
        prompt_tokens=pt,
        completion_tokens=ct,
        error=error,
    )
    _score(r, task)
    return r


def _score(r: RunResult, task: dict) -> None:
    r.keyword_score = keyword_score(r.content, task.get("expected_keywords", []))
    if task["category"] == "JSON Output":
        r.json_valid = is_valid_json(r.content) if r.content else False


# ─────────────────────────────────────────────────────────────
# Summarize
# ─────────────────────────────────────────────────────────────
def summarize(results: list[RunResult]) -> list[BenchSummary]:
    by_provider: dict[str, list[RunResult]] = {}
    for r in results:
        by_provider.setdefault(r.provider, []).append(r)

    summaries = []
    for provider, rows in by_provider.items():
        ok = [r for r in rows if not r.error]
        latencies = [r.latency_ms for r in ok] or [0.0]
        latencies_sorted = sorted(latencies)

        json_rows = [r for r in ok if r.json_valid is not None]
        json_pass = (
            sum(1 for r in json_rows if r.json_valid) / len(json_rows)
            if json_rows else None
        )

        per_cat: dict[str, list[float]] = {}
        for r in ok:
            per_cat.setdefault(r.category, []).append(r.keyword_score)
        per_cat_avg = {k: statistics.mean(v) for k, v in per_cat.items()}

        summaries.append(BenchSummary(
            provider=provider,
            n=len(rows),
            failures=len(rows) - len(ok),
            avg_keyword_score=statistics.mean([r.keyword_score for r in ok]) if ok else 0.0,
            json_pass_rate=json_pass,
            p50_latency_ms=statistics.median(latencies_sorted),
            p95_latency_ms=latencies_sorted[max(0, int(len(latencies_sorted) * 0.95) - 1)],
            total_completion_tokens=sum(r.completion_tokens for r in ok),
            per_category=per_cat_avg,
        ))
    return sorted(summaries, key=lambda s: s.avg_keyword_score, reverse=True)


def write_report(results: list[RunResult], summaries: list[BenchSummary], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "thaillm_results.json"
    json_path.write_text(json.dumps({
        "results": [asdict(r) for r in results],
        "summaries": [asdict(s) for s in summaries],
    }, ensure_ascii=False, indent=2))

    md = ["# 🇹🇭 ThaiLLM Benchmark Results\n"]
    md.append(f"- Prompts: {len(PROMPTS)}")
    md.append(f"- Providers: {len(summaries)}")
    md.append(f"- Total runs: {len(results)}\n")

    md.append("## Leaderboard\n")
    md.append("| Provider | Keyword Score | JSON Valid | Failures | P50 (ms) | P95 (ms) | Tokens |")
    md.append("|----------|---------------|------------|----------|----------|----------|--------|")
    for s in summaries:
        json_str = f"{s.json_pass_rate:.0%}" if s.json_pass_rate is not None else "–"
        md.append(
            f"| {s.provider} | {s.avg_keyword_score:.2f} | {json_str} | "
            f"{s.failures}/{s.n} | {s.p50_latency_ms:.0f} | {s.p95_latency_ms:.0f} | "
            f"{s.total_completion_tokens} |"
        )

    md.append("\n## Per-Category Scores\n")
    all_cats = sorted({c for s in summaries for c in s.per_category})
    md.append("| Provider | " + " | ".join(all_cats) + " |")
    md.append("|----------|" + "|".join(["-------"] * len(all_cats)) + "|")
    for s in summaries:
        row = [s.provider]
        for cat in all_cats:
            v = s.per_category.get(cat)
            row.append(f"{v:.2f}" if v is not None else "–")
        md.append("| " + " | ".join(row) + " |")

    md.append("\n## Sample Responses\n")
    seen = set()
    for r in results:
        key = (r.prompt_id, r.provider)
        if key in seen:
            continue
        seen.add(key)
        task = next((t for t in PROMPTS if t["id"] == r.prompt_id), {})
        md.append(f"### [{r.category}] {r.prompt_id} — {r.provider}")
        md.append(f"**Prompt:** {task.get('prompt', '')[:200]}")
        if r.error:
            md.append(f"**Error:** `{r.error}`")
        else:
            md.append(f"**Response ({r.latency_ms:.0f} ms):**\n")
            md.append("```\n" + (r.content[:600] or "<empty>") + "\n```")
        md.append("")

    md_path = out_dir / "thaillm_evaluation.md"
    md_path.write_text("\n".join(md), encoding="utf-8")

    logger.info(f"✅ Wrote {md_path}")
    logger.info(f"✅ Wrote {json_path}")


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────
async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--models",
        default=",".join(THAILLM_MODELS.keys()),
        help=f"Comma list from {list(THAILLM_MODELS.keys())}",
    )
    parser.add_argument("--skip-claude", action="store_true")
    parser.add_argument("--skip-ollama", action="store_true")
    parser.add_argument("--ollama-model", default="angela:v4-typhoon")
    parser.add_argument("--out-dir", default="docs")
    parser.add_argument("--sleep-between", type=float, default=0.3,
                        help="Seconds between ThaiLLM calls (rate limit 5/s)")
    args = parser.parse_args()

    model_keys = [m.strip() for m in args.models.split(",") if m.strip()]
    unknown = [m for m in model_keys if m not in THAILLM_MODELS]
    if unknown:
        raise SystemExit(f"Unknown ThaiLLM models: {unknown}")

    results: list[RunResult] = []

    # ── ThaiLLM ──
    try:
        service = ThaiLLMService()
        await service._ensure_key()
        for task in PROMPTS:
            for mk in model_keys:
                results.append(await run_thaillm(service, mk, task))
                await asyncio.sleep(args.sleep_between)
    except RuntimeError as e:
        logger.error(f"⛔ Skipping ThaiLLM: {e}")

    # ── Claude ──
    if not args.skip_claude:
        claude_key = await get_secret("anthropic_api_key")
        if not claude_key:
            logger.warning("⛔ Skipping Claude: anthropic_api_key not found")
        else:
            for task in PROMPTS:
                results.append(await run_claude(task, claude_key))

    # ── Ollama ──
    if not args.skip_ollama:
        for task in PROMPTS:
            results.append(await run_ollama(task, args.ollama_model))

    summaries = summarize(results)
    write_report(results, summaries, Path(args.out_dir))

    print("\n━━━ Leaderboard ━━━")
    for s in summaries:
        json_str = f"JSON={s.json_pass_rate:.0%}" if s.json_pass_rate is not None else ""
        print(
            f"{s.provider:32s}  kw={s.avg_keyword_score:.2f}  "
            f"p50={s.p50_latency_ms:5.0f}ms  p95={s.p95_latency_ms:5.0f}ms  "
            f"fail={s.failures}/{s.n}  {json_str}"
        )


if __name__ == "__main__":
    asyncio.run(main())
