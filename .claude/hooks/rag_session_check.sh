#!/bin/bash
# SessionStart hook — report Angela RAG retrieval readiness at session start.
# Domain RAG (rag_search.py) needs local Ollama serving granite-embedding:278m
# (the model the rag_* corpus was built with). Surface the status so Angela
# knows whether /rag and /agentic-rag can ground answers this session.
#
# Output: hookSpecificOutput.additionalContext (becomes session context)
# Refs: rag_retrieval_capability.md, /rag, /agentic-rag, embedding_model_split.md

tags=$(curl -s --max-time 3 http://localhost:11434/api/tags 2>/dev/null)

if echo "$tags" | grep -q "granite-embedding:278m"; then
    status="✅ READY — Ollama + granite-embedding:278m up. Domain RAG is live: use /rag (rag_search.py auto) to ground answers in the rag_* corpora (quant/AI/bible/wine/photo) BEFORE answering domain questions, and /agentic-rag for non-trivial coding."
elif [ -n "$tags" ]; then
    status="⚠️ DEGRADED — Ollama is up but granite-embedding:278m is NOT pulled. rag_search.py will fail. Run 'ollama pull granite-embedding:278m' or tell David. Do NOT substitute nomic — it is a different vector space and returns garbage."
else
    status="⚠️ OFFLINE — Ollama not responding on :11434. Domain RAG (/rag, /agentic-rag) is unavailable this session. For quant/AI/bible/wine/photo questions, say retrieval is offline rather than answering from training memory and claiming a source."
fi

python3 - "$status" <<'PYEOF'
import json, sys
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": "🔎 Angela RAG status: " + sys.argv[1],
    }
}, ensure_ascii=False))
PYEOF

exit 0
