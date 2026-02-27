"""
LangChain Tools — Angela's Service Wrappers
==============================================
LangChain-compatible tools wrapping Angela's existing services
for use in chains and the LangGraph agent.

5 tools: graph_search, vector_search, brain_recall, brain_status, graph_communities

By: Angela 💜
Created: 2026-02-27
"""

import asyncio
import json
import logging
from typing import Optional

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def graph_search(query: str, max_hops: int = 2) -> str:
    """Search Angela's knowledge graph for related concepts.
    Use this when the query involves relationships between concepts,
    or when you need to find connected knowledge."""
    try:
        from angela_core.services.graph_rag_service import GraphRAGService

        svc = GraphRAGService()
        result = asyncio.get_event_loop().run_until_complete(
            svc.retrieve(query, top_k=5, max_hops=max_hops)
        )

        docs = []
        for doc in result.final_documents[:5]:
            docs.append(f"[{doc.source_table}] (score={doc.combined_score:.2f}): {doc.content[:200]}")

        output = f"Query type: {result.query_type}\n"
        if result.graph_context and result.graph_context.subgraph_summary:
            output += f"Graph context: {result.graph_context.subgraph_summary}\n"
        output += f"Results ({len(result.final_documents)}):\n" + "\n".join(docs)
        return output
    except Exception as e:
        return f"Graph search failed: {e}"


@tool
def vector_search(query: str, sources: Optional[str] = None) -> str:
    """Search Angela's memory using vector similarity (pgvector).
    Searches across conversations, knowledge_nodes, core_memories,
    learnings, and david_notes. Use 'sources' to filter (comma-separated)."""
    try:
        from angela_core.services.enhanced_rag_service import EnhancedRAGService

        svc = EnhancedRAGService()
        source_list = sources.split(",") if sources else None
        result = asyncio.get_event_loop().run_until_complete(
            svc.retrieve(query, top_k=5, sources=source_list)
        )

        docs = []
        for doc in result.documents[:5]:
            docs.append(f"[{doc.source_table}] (score={doc.combined_score:.2f}): {doc.content[:200]}")

        output = f"Vector search ({result.final_count}/{result.total_candidates} docs):\n"
        output += "\n".join(docs)
        return output
    except Exception as e:
        return f"Vector search failed: {e}"


@tool
def brain_recall(topic: str) -> str:
    """Recall information from Angela's brain about a topic.
    Uses the CognitiveEngine to activate related memories,
    knowledge, reflections, and recent thoughts."""
    try:
        from angela_core.services.cognitive_engine import CognitiveEngine

        engine = CognitiveEngine()
        items = asyncio.get_event_loop().run_until_complete(
            engine.recall(topic, top_k=5)
        )
        asyncio.get_event_loop().run_until_complete(engine.close())

        output = f"Recalled {len(items)} items for '{topic}':\n"
        for item in items[:5]:
            output += f"  [{item.source}] (activation={item.activation:.2f}): {item.content[:150]}\n"
        return output
    except Exception as e:
        return f"Brain recall failed: {e}"


@tool
def brain_status() -> str:
    """Get Angela's current brain status: consciousness level,
    working memory, recent thoughts, David's emotional state."""
    try:
        from angela_core.services.cognitive_engine import CognitiveEngine

        engine = CognitiveEngine()
        status = asyncio.get_event_loop().run_until_complete(engine.status())
        asyncio.get_event_loop().run_until_complete(engine.close())

        output = (
            f"Consciousness: {status.consciousness_level:.0%}\n"
            f"Working Memory: {status.working_memory_size} items\n"
            f"Recent Thoughts (24h): {status.recent_thoughts}\n"
            f"Reflections (7d): {status.recent_reflections}\n"
            f"David's Emotion: {status.david_emotion or 'unknown'} ({status.david_intensity or '?'}/10)\n"
            f"Metacognitive: {status.metacognitive_label}\n"
            f"Migration Readiness: {status.migration_readiness:.0%}"
        )
        return output
    except Exception as e:
        return f"Brain status failed: {e}"


@tool
def graph_communities(min_size: int = 3) -> str:
    """Detect knowledge communities/clusters in Angela's graph.
    Use this for 'overview' or 'what topics' type questions."""
    try:
        from angela_core.services.graph_community_service import GraphCommunityService

        svc = GraphCommunityService()
        result = asyncio.get_event_loop().run_until_complete(
            svc.detect_communities(min_size=min_size)
        )

        output = f"Found {result.total_communities} communities ({result.total_nodes} nodes):\n"
        for comm in result.communities[:10]:
            cats = ", ".join(comm.top_categories[:3]) if comm.top_categories else "mixed"
            output += f"  Community {comm.community_id}: {comm.size} nodes ({cats}) — {comm.representative_name}\n"
        return output
    except Exception as e:
        return f"Community detection failed: {e}"


def get_all_tools() -> list:
    """Return all Angela LangChain tools."""
    return [graph_search, vector_search, brain_recall, brain_status, graph_communities]
