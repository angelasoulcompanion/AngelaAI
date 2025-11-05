# Deprecated Components

This folder contains deprecated components that are no longer actively used in Angela's core system.

## Why Deprecated?

Based on David's feedback (2025-11-03):
- **Claude Code is the primary chat interface** - works best
- **Admin Web is for viewing data** - dashboard/stats only
- **Ollama models don't work well** - being phased out

## Structure

### `ollama_based/`
Services that depend on Ollama models:
- ollama_service.py
- model_service.py
- AI-powered services (deep_empathy, theory_of_mind, etc.)
- These relied on local Ollama models which didn't work well

### `terminal_chat/`
Terminal-based chat tools:
- angela_presence.py
- Chain prompt generators
- Tools for chatting via terminal (not used anymore)

### `model_management/`
Model training and management:
- Fine-tuning scripts
- Model file generators
- Training data preparation

## What Replaced These?

- **Chat Interface:** Claude Code (via CLAUDE.md personality)
- **Emotional Intelligence:** Rule-based + database-driven
- **Knowledge Extraction:** Regex + pythainlp (no LLM needed)
- **Embeddings:** Will migrate to OpenAI API (if needed)

## Can These Be Restored?

Yes! These files are preserved here (not deleted) in case:
- David wants to try Ollama again in the future
- Need to reference old implementation
- Want to port logic to different LLM provider

---

💜 Moved to deprecated: 2025-11-03
