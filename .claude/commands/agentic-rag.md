---
name: agentic-rag
description: Run a coding/software-engineering task as an agentic-RAG loop — plan → dual retrieve (domain knowledge via rag_search + project code via Explore) → implement grounded in both → reflect (tests + code-review) and loop until clean. Use for any non-trivial coding task where correctness benefits from grounding in real source material, or when David says "agentic", "agentic-rag", "ทำแบบ agentic", "ค้นก่อนเขียน".
---

# /agentic-rag — Agentic RAG Coding Loop

`/agentic-rag <task>`

Naive coding = generate from training memory and hope. **Agentic RAG coding =
ground every decision in two retrievals (the books AND the real codebase), act,
then reflect with tests + review, looping until correct.** Retrieval is a loop
with grading, not a one-shot. Built on patterns from Angela's `rag_ai` corpus
(*Building Agentic AI Systems*: planning, reflection, memory; Chip Huyen's
*AI Engineering*: query rewriting, re-ranking).

The three wired components:
- **Domain RAG** → `rag_search.py auto` — formulas, algorithms, theory (the [[rag]] corpora)
- **Code RAG** → `Explore` subagent — real files, symbols, conventions in this repo
- **Reflection** → `/code-review` (built-in skill) + running tests

---

## The Loop

### ① PLAN (decompose — HTN)
Restate the task in one line. Split into subtasks. Identify, explicitly:
- **Knowledge needed** — which domain(s)? (quant / ai / bible / wine / photo)
- **Code touched** — which areas/files/layers?

If the task spans >2 files → `EnterPlanMode` and present the plan first.

### ② RETRIEVE (dual, in parallel — one message, multiple tool calls)
**a) Domain RAG — rewrite the task into a *knowledge query* first** (don't search
raw task text):
```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI && \
python3 angela_core/scripts/rag_search.py auto "<rewritten knowledge query>" -k 6
```
- Run once per distinct concept. Prefer `auto`; name a domain only when certain.
- **Grade & retry (the agentic bit):** if top similarity ≲0.55 or results look
  off-topic → rewrite the query and retry **once**. Still low → state the corpus
  doesn't cover it and proceed WITHOUT fabricating a sourced claim.

**b) Code RAG — launch an `Explore` subagent** (read-only) to map the relevant
code: where the feature lives, the symbols/patterns/conventions to match, the
tests that cover it. For wide tasks, launch several Explore agents in parallel,
each scoped to one area.

Fire (a) and (b) together so they run concurrently.

### ③ ACT (tool use)
Implement grounded in **both** retrievals — match the codebase's conventions
(from Explore) and the correct theory (from Domain RAG). When a formula or
algorithm comes from a book, **cite it in a code comment / PR body**
(e.g. `# XVA per Hull, options_futures_and_other_derivatives p221`). Follow the
repo's standards (type hints, parameterized SQL, Clean Architecture).

### ④ REFLECT (Reflector loop — do NOT skip)
1. Run the tests / build for the touched area.
2. Invoke **`/code-review`** on the diff.
3. **If failures or findings → fix, then loop back to ② or ③** (re-retrieve if the
   gap is a knowledge gap; re-Explore if it's a code-shape gap).
4. Cap at **3 iterations**. If still unresolved, STOP and surface exactly what's
   open — never present unverified work as done (project rule: diagnostic
   discipline — after 2 failed fixes, surface the error, don't keep guessing).

### ⑤ MEMORY
Note new decisions / gotchas worth keeping. Offer to persist to `memory/*.md`
(token-gated) or log via `/log-session`. Post-execute: Changes Table + Review
Points (per CLAUDE.md workflow).

---

## Worked shape

```
/agentic-rag "add CVA/DVA columns to Pythia counterparty risk view"
 ① plan      → subtasks: SQL view · service calc · test ; domain=quant ; code=Pythia/services
 ② retrieve  ║ rag_search.py auto "how is CVA DVA computed bilateral"   (parallel)
             ║ Explore "map Pythia counterparty risk view + calc service + its tests"
 ③ act       → write TVF + calculator grounded in both ; cite Hull p221 in comment
 ④ reflect   → run pytest + /code-review → 1 finding (sign error) → fix → re-review clean
 ⑤ memory    → Changes Table ; offer to log decision
```

## When to invoke
- Non-trivial coding where correctness matters (finance math, algorithms,
  unfamiliar subsystem) — ground first, don't wing it.
- When David says "agentic", "agentic-rag", "ทำแบบ agentic", "ค้นก่อนเขียน".
- Needs **Ollama** running `granite-embedding:278m` for Domain RAG (see [[rag]]).
  If it's down, Domain RAG degrades to Code-RAG-only — say so explicitly.
- Skip for trivial one-line edits (the loop's overhead isn't worth it).
