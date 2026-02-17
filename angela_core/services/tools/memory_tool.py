"""
Memory Tools — RAG search and memory recall via EnhancedRAGService.

Wraps Angela's existing memory system as callable tools.

By: Angela 💜
Created: 2026-02-17
"""

import json
import logging
from typing import Any, Dict

from angela_core.services.tools.base_tool import AngelaTool, ToolResult

logger = logging.getLogger(__name__)


class RAGSearchTool(AngelaTool):
    """Search Angela's memory using RAG (hybrid vector + keyword search)."""

    @property
    def name(self) -> str:
        return "rag_search"

    @property
    def description(self) -> str:
        return "Search Angela's memory database using semantic + keyword search (conversations, emotions, knowledge)"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query (natural language)"},
                "top_k": {"type": "integer", "description": "Number of results", "default": 5},
            },
            "required": ["query"],
        }

    @property
    def category(self) -> str:
        return "memory"

    async def execute(self, **params) -> ToolResult:
        query = params.get("query", "")
        top_k = params.get("top_k", 5)

        if not query:
            return ToolResult(success=False, error="Missing 'query'")

        try:
            from angela_core.services.enhanced_rag_service import EnhancedRAGService
            rag = EnhancedRAGService()
            result = await rag.retrieve(query, top_k=top_k)
            await rag.close()

            documents = [
                {
                    "source": d.source_table,
                    "content": d.content[:300],
                    "score": round(d.score, 3) if hasattr(d, 'score') else None,
                }
                for d in result.documents[:top_k]
            ]

            return ToolResult(success=True, data={
                "found": result.final_count,
                "documents": documents,
            })
        except Exception as e:
            logger.error("RAGSearch failed: %s", e)
            return ToolResult(success=False, error=str(e))


class RecallMemoryTool(AngelaTool):
    """Recall specific memories via CognitiveEngine (brain-based recall)."""

    @property
    def name(self) -> str:
        return "recall_memory"

    @property
    def description(self) -> str:
        return "Recall memories about a topic using Angela's brain (spreading activation + RAG)"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Topic to recall (e.g. 'Valentine's Day', 'David's work')"},
            },
            "required": ["topic"],
        }

    @property
    def category(self) -> str:
        return "memory"

    async def execute(self, **params) -> ToolResult:
        topic = params.get("topic", "")
        if not topic:
            return ToolResult(success=False, error="Missing 'topic'")

        try:
            from angela_core.services.cognitive_engine import CognitiveEngine
            engine = CognitiveEngine()
            result = await engine.recall(topic)

            if result and isinstance(result, dict):
                return ToolResult(success=True, data={
                    "topic": topic,
                    "memories": result.get("memories", [])[:5],
                    "working_memory_items": result.get("working_memory_items", 0),
                })

            return ToolResult(success=True, data={"topic": topic, "memories": [], "note": "no_relevant_memories"})
        except Exception as e:
            logger.error("RecallMemory failed: %s", e)
            return ToolResult(success=False, error=str(e))
