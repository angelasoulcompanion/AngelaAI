#!/bin/bash
# UserPromptSubmit hook — when a prompt looks like a domain question that
# Angela's rag_* corpora cover, remind her to RETRIEVE (rag_search.py auto)
# before answering, then answer FROM the chunks with citations. This is the
# enforcement arm of the CLAUDE.md MUST rule on RAG grounding.
#
# It only nudges (adds context); Angela still judges whether to retrieve.
# Output: hookSpecificOutput.additionalContext
# Refs: rag_retrieval_capability.md, CLAUDE.md MUST, /rag

prompt=$(cat | python3 -c "import sys,json; print(json.load(sys.stdin).get('prompt','').lower())" 2>/dev/null)

domain=""
if echo "$prompt" | grep -qE "quant|derivative|option pricing|black.?scholes|\bxva\b|\bcva\b|\bdva\b|\bfva\b|hedg|volatilit|wilmott|\bhull\b|\bcqf\b|fixed income|martingale|monte carlo|value at risk|\bgreeks\b"; then
    domain="quant"
elif echo "$prompt" | grep -qE "machine learning|deep learning|neural net|transformer|\bllm\b|\brag\b|embedding|fine.?tun|backprop|pytorch|tensorflow|scikit|raschka|géron|geron|chip huyen|agentic|re-?rank|retrieval augmented"; then
    domain="ai"
elif echo "$prompt" | grep -qE "bible|scripture|\bverse\b|gospel|psalm|\bkjv\b|พระคัมภีร์|พระเยซู|พระธรรม"; then
    domain="bible"
elif echo "$prompt" | grep -qE "\bwine\b|vintage|tannin|cabernet|merlot|pinot|chardonnay|sommelier|ไวน์"; then
    domain="wine"
elif echo "$prompt" | grep -qE "photograph|\bcamera\b|fujifilm|fuji |x-?e5|film simulation|aperture|shutter speed|\blens\b|ถ่ายภาพ|กล้อง"; then
    domain="photo"
fi

if [ -n "$domain" ]; then
    python3 - "$domain" <<'PYEOF'
import json, sys
d = sys.argv[1]
msg = (
    f"🔎 RAG nudge: this prompt looks like a '{d}' question Angela's rag_* corpus covers. "
    f"Per CLAUDE.md MUST — run `python3 angela_core/scripts/rag_search.py auto \"<rewritten query>\" -k 6` "
    f"(or domain `{d}`) BEFORE answering, then answer FROM the retrieved chunks and cite source/page. "
    f"If top similarity ≲ 0.55, say the corpus doesn't cover it — do NOT answer from training memory and claim a source. "
    f"(Infra/meta talk about RAG itself doesn't need retrieval — use judgment.) ref: rag_retrieval_capability.md, /rag"
)
print(json.dumps({
    "hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": msg}
}, ensure_ascii=False))
PYEOF
fi

exit 0
