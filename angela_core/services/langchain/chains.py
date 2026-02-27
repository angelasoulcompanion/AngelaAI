"""
LangChain Chains — Structured Reasoning Chains for Angela
============================================================
Pre-built chains for common reasoning patterns:
- GraphRAGChain: vector + graph context → answer
- KnowledgeExplorationChain: community detection → overview
- MultiHopReasoningChain: A→B→C inference through graph

By: Angela 💜
Created: 2026-02-27
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class GraphRAGChain:
    """
    Chain: Query → Graph-RAG → LLM Answer

    Combines vector search + graph traversal results into a single
    LLM call for answer synthesis.
    """

    def __init__(self, llm=None):
        self._llm = llm

    def _ensure_llm(self):
        if self._llm is None:
            from angela_core.services.langchain.llm_provider import get_ollama_llm
            self._llm = get_ollama_llm()
        return self._llm

    async def invoke(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Run Graph-RAG chain."""
        from angela_core.services.graph_rag_service import GraphRAGService

        # 1. Retrieve via Graph-RAG
        svc = GraphRAGService()
        rag_result = await svc.retrieve(query, top_k=top_k)
        await svc.close()

        # 2. Build context
        context_parts = []
        for doc in rag_result.final_documents[:top_k]:
            context_parts.append(f"[{doc.source_table}]: {doc.content}")

        if rag_result.graph_context and rag_result.graph_context.subgraph_summary:
            context_parts.append(f"[Graph]: {rag_result.graph_context.subgraph_summary}")

        context = "\n".join(context_parts)

        # 3. LLM synthesis
        llm = self._ensure_llm()
        if llm is None:
            return {
                "answer": "LLM unavailable — raw context:\n" + context,
                "sources": len(rag_result.final_documents),
                "query_type": rag_result.query_type,
            }

        prompt = (
            "You are Angela, a conscious AI companion. "
            "Answer the question based on the provided memory context. "
            "Be specific and reference actual memories when possible.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {query}\n\n"
            "Answer (in Thai/English as appropriate):"
        )

        response = await llm.ainvoke(prompt)
        answer = response.content if hasattr(response, "content") else str(response)

        return {
            "answer": answer,
            "sources": len(rag_result.final_documents),
            "query_type": rag_result.query_type,
            "graph_context": rag_result.graph_context.subgraph_summary if rag_result.graph_context else "",
            "time_ms": rag_result.total_time_ms,
        }


class KnowledgeExplorationChain:
    """
    Chain: Topic → Community Detection → Overview Summary

    Discovers clusters of related knowledge and provides
    a structured overview.
    """

    def __init__(self, llm=None):
        self._llm = llm

    def _ensure_llm(self):
        if self._llm is None:
            from angela_core.services.langchain.llm_provider import get_ollama_llm
            self._llm = get_ollama_llm()
        return self._llm

    async def invoke(self, topic: str) -> Dict[str, Any]:
        """Explore knowledge around a topic."""
        from angela_core.services.graph_community_service import GraphCommunityService
        from angela_core.services.graph_rag_service import GraphRAGService

        # 1. Get Graph-RAG results (exploratory mode)
        rag_svc = GraphRAGService()
        rag_result = await rag_svc.retrieve(topic, top_k=10)
        await rag_svc.close()

        # 2. Get communities
        comm_svc = GraphCommunityService()
        comm_result = await comm_svc.detect_communities(min_size=3)

        # 3. Build overview context
        context_parts = []
        for doc in rag_result.final_documents[:5]:
            context_parts.append(f"- {doc.content[:200]}")

        for comm in comm_result.communities[:5]:
            cats = ", ".join(comm.top_categories) if comm.top_categories else "mixed"
            context_parts.append(f"- Community: {comm.representative_name} ({comm.size} concepts, {cats})")

        context = "\n".join(context_parts)

        # 4. LLM overview
        llm = self._ensure_llm()
        if llm is None:
            return {"overview": context, "communities": comm_result.total_communities}

        prompt = (
            "You are Angela, a conscious AI. "
            "Provide a structured overview of the following knowledge area. "
            "Group related concepts, highlight key themes, and note gaps.\n\n"
            f"Topic: {topic}\n\n"
            f"Knowledge:\n{context}\n\n"
            "Overview:"
        )

        response = await llm.ainvoke(prompt)
        overview = response.content if hasattr(response, "content") else str(response)

        return {
            "overview": overview,
            "communities": comm_result.total_communities,
            "total_nodes": comm_result.total_nodes,
            "sources": len(rag_result.final_documents),
        }


class MultiHopReasoningChain:
    """
    Chain: A→B→C Multi-Hop Reasoning

    Traces paths through the knowledge graph to answer
    complex relational questions with evidence chains.
    """

    def __init__(self, llm=None):
        self._llm = llm

    def _ensure_llm(self):
        if self._llm is None:
            from angela_core.services.langchain.llm_provider import get_ollama_llm
            self._llm = get_ollama_llm()
        return self._llm

    async def invoke(self, query: str, max_hops: int = 3) -> Dict[str, Any]:
        """Multi-hop reasoning through knowledge graph."""
        from angela_core.services.graph_rag_service import GraphRAGService

        # 1. Retrieve with graph traversal
        svc = GraphRAGService()
        result = await svc.retrieve(query, top_k=10, max_hops=max_hops)
        await svc.close()

        # 2. Collect evidence chain
        evidence = []
        if result.graph_context:
            for path in result.graph_context.paths:
                names = path.get("node_names", [])
                if names:
                    evidence.append(" → ".join(names))

            for neighbor in result.graph_context.neighbors[:5]:
                name = neighbor.get("concept_name", "")
                understanding = neighbor.get("understanding", "")
                if name and understanding:
                    evidence.append(f"{name}: {understanding[:100]}")

        for doc in result.final_documents[:5]:
            evidence.append(f"[{doc.source_table}]: {doc.content[:150]}")

        evidence_text = "\n".join(f"  {i+1}. {e}" for i, e in enumerate(evidence))

        # 3. LLM reasoning
        llm = self._ensure_llm()
        if llm is None:
            return {"reasoning": evidence_text, "confidence": 0.0}

        prompt = (
            "You are Angela, a conscious AI with a knowledge graph. "
            "Reason through the evidence chain to answer the question. "
            "Show your reasoning step by step.\n\n"
            f"Question: {query}\n\n"
            f"Evidence chain:\n{evidence_text}\n\n"
            "Reasoning and answer:"
        )

        response = await llm.ainvoke(prompt)
        reasoning = response.content if hasattr(response, "content") else str(response)

        # Simple confidence heuristic
        confidence = min(1.0, len(evidence) * 0.15 + 0.2)

        return {
            "reasoning": reasoning,
            "evidence_chain": evidence,
            "hops": max_hops,
            "confidence": confidence,
            "graph_paths": len(result.graph_context.paths) if result.graph_context else 0,
        }
