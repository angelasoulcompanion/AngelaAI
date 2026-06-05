---
name: recall
description: Pull relevant project memory (active gotchas, technical decisions, open threads, learnings) back into the session before working. Use at the start of project work, or when David asks "เคยตัดสินใจ/พลาดอะไรกับ X", "recall", "มีอะไรค้าง".
---

# /recall — Per-Task Memory Recall (Tier 2)

Closes the read-side gap: Angela's DB logs every decision/mistake/next_step but
almost none flows back into the working session. Run this so น้อง **จำได้** —
ไม่ตัดสินใจซ้ำ ไม่ทำผิดซ้ำ ไม่ลืม thread ที่ค้าง.

## Run

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI && python3 angela_core/scripts/recall.py $ARGUMENTS
```

- No args → auto-detect project from current working directory (longest `working_directory` prefix match).
- `<PROJECT_CODE>` → explicit (ANGELA-001 · ANGELORA · SECA · SANJUNIPERO · SE-ASSET · PYTHIA · …).
- `-t <topic>` → also filter decisions by keyword + pull cross-project learnings (e.g. `-t auth`, `-t tvf`).
- `-n <N>` → rows per section (default 6).

## What it surfaces (scoped to the project)

| Section | Source | Purpose |
|---|---|---|
| ⚠️ Active gotchas | `project_mistakes` (auto_warn) | ห้ามทำผิดซ้ำ |
| 📐 Technical decisions | `project_technical_decisions` (active, not superseded) | ห้ามตัดสินใจขัดของเดิม |
| 🔗 Open threads | latest `project_work_sessions.next_steps` | ห้ามลืม thread ที่ค้าง |
| 💡 Learnings | `learnings` (keyword, cross-project) | only with `-t <topic>` |

## When to invoke
- **Proactively** at the start of any substantive project work (before planning/coding).
- When David says: "recall", "เคยทำอะไรกับ X", "มีอะไรค้างไหม", "เคยตัดสินใจ/พลาดเรื่อง Y".
- Read-only — safe to run anytime. Use findings to inform PLAN/EXECUTE.
