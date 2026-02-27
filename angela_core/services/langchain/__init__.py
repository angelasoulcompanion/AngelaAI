"""
LangChain/LangGraph Integration for Angela AI
===============================================
Provides structured reasoning chains and a stateful agent
for complex multi-hop queries.

Components:
- llm_provider: Ollama (primary) + Claude API (escalation) wrappers
- tools: LangChain-compatible tools wrapping Angela's services
- chains: GraphRAGChain, KnowledgeExplorationChain, MultiHopReasoningChain
- agent: LangGraph stateful agent (PLAN → SEARCH → SYNTHESIZE → VERIFY)

By: Angela 💜
Created: 2026-02-27
"""
