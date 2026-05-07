# /verify-model — Verify LLM/Tool Version Before Answering

**Rule:** Knowledge cutoff is NOT an excuse. Always check live sources.

## Steps

1. **WebSearch FIRST** for the query (e.g. "Gemma 4 release", "Ollama typhoon registry")
2. **Check the authoritative registry** where applicable:
   - Ollama models → `curl https://ollama.com/library/<name>` or WebFetch
   - Hugging Face models → hf_hub_query / WebFetch
   - Anthropic/OpenAI/Google → official docs
3. **Report facts only** — include: version, release date, size (for quantized: check manifest, don't guess), compat notes
4. **Never extrapolate from name alone** — "e4b" does NOT mean 4-5GB; check manifest tag

## When to invoke
Any question containing: version, ล่าสุด, new, ออกแล้ว, ตอนนี้มี, available, released
