"""
Angela Reasoning Agent — LangGraph Stateful Agent
====================================================
Multi-step reasoning agent using LangGraph state machine.

State machine: START → PLAN → [SEARCH | GRAPH_TRAVERSE | RECALL] → SYNTHESIZE → VERIFY → END

- PLAN: Decompose query into steps
- SEARCH/TRAVERSE/RECALL: Execute tools in parallel
- SYNTHESIZE: Combine results into coherent answer
- VERIFY: Check confidence, escalate to Claude if < 0.5

Cost: Ollama primary ($0), Claude API max 10/day (~$0.05)

By: Angela 💜
Created: 2026-02-27
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ReasoningState:
    """State for the reasoning agent."""
    query: str
    plan: List[str] = field(default_factory=list)
    search_results: List[Dict[str, Any]] = field(default_factory=list)
    graph_results: List[Dict[str, Any]] = field(default_factory=list)
    recall_results: List[Dict[str, Any]] = field(default_factory=list)
    synthesis: str = ""
    confidence: float = 0.0
    escalated: bool = False
    steps_taken: List[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class ReasoningResult:
    """Final result from the reasoning agent."""
    answer: str
    confidence: float
    steps: List[str]
    sources_used: int
    time_ms: float
    escalated: bool = False


class AngelaReasoningAgent:
    """
    LangGraph-style stateful agent for complex reasoning.

    Pipeline: PLAN → SEARCH/TRAVERSE/RECALL → SYNTHESIZE → VERIFY

    If LangGraph is installed, uses proper StateGraph.
    Otherwise, falls back to sequential execution (same logic).
    """

    def __init__(self, prefer_quality: bool = False):
        self._prefer_quality = prefer_quality

    async def reason(self, query: str) -> ReasoningResult:
        """Main entry point: reason about a complex query."""
        start = time.time()

        state = ReasoningState(query=query)

        try:
            # Try LangGraph-based agent
            return await self._run_langgraph(state, start)
        except ImportError:
            logger.info("LangGraph not available, using sequential fallback")
            return await self._run_sequential(state, start)
        except Exception as e:
            logger.error("LangGraph agent failed: %s, using fallback", e)
            return await self._run_sequential(state, start)

    async def _run_langgraph(self, state: ReasoningState, start: float) -> ReasoningResult:
        """Run agent using LangGraph StateGraph."""
        from langgraph.graph import StateGraph, END
        from typing import TypedDict

        class AgentState(TypedDict):
            query: str
            plan: list
            search_results: list
            graph_results: list
            recall_results: list
            synthesis: str
            confidence: float
            escalated: bool
            steps: list

        async def plan_node(state: AgentState) -> AgentState:
            plan = await self._plan(state["query"])
            return {**state, "plan": plan, "steps": state["steps"] + ["PLAN"]}

        async def search_node(state: AgentState) -> AgentState:
            import asyncio
            search_task = self._search(state["query"])
            graph_task = self._graph_traverse(state["query"])
            recall_task = self._recall(state["query"])
            s, g, r = await asyncio.gather(search_task, graph_task, recall_task)
            return {
                **state,
                "search_results": s,
                "graph_results": g,
                "recall_results": r,
                "steps": state["steps"] + ["SEARCH"],
            }

        async def synthesize_node(state: AgentState) -> AgentState:
            synthesis, confidence = await self._synthesize(
                state["query"], state["search_results"],
                state["graph_results"], state["recall_results"],
            )
            return {
                **state,
                "synthesis": synthesis,
                "confidence": confidence,
                "steps": state["steps"] + ["SYNTHESIZE"],
            }

        async def verify_node(state: AgentState) -> AgentState:
            if state["confidence"] < 0.5 and not state["escalated"]:
                synthesis, confidence = await self._escalate(
                    state["query"], state["synthesis"]
                )
                return {
                    **state,
                    "synthesis": synthesis,
                    "confidence": confidence,
                    "escalated": True,
                    "steps": state["steps"] + ["VERIFY_ESCALATE"],
                }
            return {**state, "steps": state["steps"] + ["VERIFY_OK"]}

        # Build graph
        graph = StateGraph(AgentState)
        graph.add_node("plan", plan_node)
        graph.add_node("search", search_node)
        graph.add_node("synthesize", synthesize_node)
        graph.add_node("verify", verify_node)

        graph.set_entry_point("plan")
        graph.add_edge("plan", "search")
        graph.add_edge("search", "synthesize")
        graph.add_edge("synthesize", "verify")
        graph.add_edge("verify", END)

        compiled = graph.compile()

        initial = AgentState(
            query=state.query, plan=[], search_results=[],
            graph_results=[], recall_results=[], synthesis="",
            confidence=0.0, escalated=False, steps=[],
        )

        result = await compiled.ainvoke(initial)

        total_sources = (
            len(result["search_results"]) +
            len(result["graph_results"]) +
            len(result["recall_results"])
        )

        return ReasoningResult(
            answer=result["synthesis"],
            confidence=result["confidence"],
            steps=result["steps"],
            sources_used=total_sources,
            time_ms=(time.time() - start) * 1000,
            escalated=result["escalated"],
        )

    async def _run_sequential(self, state: ReasoningState, start: float) -> ReasoningResult:
        """Sequential fallback when LangGraph is not available."""
        # PLAN
        state.plan = await self._plan(state.query)
        state.steps_taken.append("PLAN")

        # SEARCH (parallel)
        import asyncio
        s, g, r = await asyncio.gather(
            self._search(state.query),
            self._graph_traverse(state.query),
            self._recall(state.query),
        )
        state.search_results = s
        state.graph_results = g
        state.recall_results = r
        state.steps_taken.append("SEARCH")

        # SYNTHESIZE
        state.synthesis, state.confidence = await self._synthesize(
            state.query, state.search_results,
            state.graph_results, state.recall_results,
        )
        state.steps_taken.append("SYNTHESIZE")

        # VERIFY
        if state.confidence < 0.5:
            state.synthesis, state.confidence = await self._escalate(
                state.query, state.synthesis
            )
            state.escalated = True
            state.steps_taken.append("VERIFY_ESCALATE")
        else:
            state.steps_taken.append("VERIFY_OK")

        total_sources = len(s) + len(g) + len(r)

        return ReasoningResult(
            answer=state.synthesis,
            confidence=state.confidence,
            steps=state.steps_taken,
            sources_used=total_sources,
            time_ms=(time.time() - start) * 1000,
            escalated=state.escalated,
        )

    # ── Agent Steps ──

    async def _plan(self, query: str) -> List[str]:
        """Decompose query into reasoning steps."""
        from angela_core.services.langchain.llm_provider import get_ollama_llm

        llm = get_ollama_llm()
        if llm is None:
            return ["search", "synthesize"]

        prompt = (
            "Decompose this query into 2-4 search/retrieval steps. "
            "Each step should be a specific search query. "
            "Return one step per line, nothing else.\n\n"
            f"Query: {query}"
        )

        try:
            response = await llm.ainvoke(prompt)
            text = response.content if hasattr(response, "content") else str(response)
            steps = [s.strip().lstrip("0123456789.-) ") for s in text.strip().split("\n") if s.strip()]
            return steps[:4]
        except Exception as e:
            logger.warning("Plan step failed: %s", e)
            return [query]

    async def _search(self, query: str) -> List[Dict[str, Any]]:
        """Vector search step."""
        try:
            from angela_core.services.enhanced_rag_service import EnhancedRAGService

            svc = EnhancedRAGService()
            result = await svc.retrieve(query, top_k=5, min_score=0.3)
            await svc.close()
            return [
                {"source": d.source_table, "content": d.content[:300], "score": d.combined_score}
                for d in result.documents
            ]
        except Exception as e:
            logger.warning("Search step failed: %s", e)
            return []

    async def _graph_traverse(self, query: str) -> List[Dict[str, Any]]:
        """Graph traversal step."""
        try:
            from angela_core.services.neo4j_service import get_neo4j_service

            neo4j = get_neo4j_service()
            if not neo4j.available:
                return []

            result = await neo4j.execute_read("""
                CALL db.index.fulltext.queryNodes('knowledge_fulltext', $query)
                YIELD node, score
                WHERE score > 0.3
                WITH node LIMIT 3
                MATCH (node)-[r*1..2]-(neighbor:KnowledgeNode)
                RETURN DISTINCT neighbor.concept_name AS name,
                       COALESCE(neighbor.my_understanding, '') AS understanding,
                       neighbor.concept_category AS category
                LIMIT 10
            """, {"query": query})
            return [
                {"source": "graph", "content": f"{r['name']}: {r['understanding'][:200]}", "category": r.get("category")}
                for r in result
            ]
        except Exception as e:
            logger.warning("Graph traverse failed: %s", e)
            return []

    async def _recall(self, query: str) -> List[Dict[str, Any]]:
        """Brain recall step."""
        try:
            from angela_core.services.cognitive_engine import CognitiveEngine

            engine = CognitiveEngine()
            items = await engine.recall(query, top_k=3)
            await engine.close()
            return [
                {"source": item.source, "content": item.content, "activation": item.activation}
                for item in items
            ]
        except Exception as e:
            logger.warning("Recall step failed: %s", e)
            return []

    async def _synthesize(
        self, query: str,
        search_results: List[Dict],
        graph_results: List[Dict],
        recall_results: List[Dict],
    ) -> tuple:
        """Synthesize all results into a coherent answer."""
        from angela_core.services.langchain.llm_provider import get_ollama_llm

        # Build context
        context_parts = []
        for r in search_results[:5]:
            context_parts.append(f"[Memory/{r['source']}]: {r['content']}")
        for r in graph_results[:5]:
            context_parts.append(f"[Graph]: {r['content']}")
        for r in recall_results[:3]:
            context_parts.append(f"[Brain/{r['source']}]: {r['content']}")

        context = "\n".join(context_parts)
        total_sources = len(search_results) + len(graph_results) + len(recall_results)

        if not context_parts:
            return "ไม่พบข้อมูลที่เกี่ยวข้องค่ะ", 0.1

        llm = get_ollama_llm()
        if llm is None:
            return context, 0.3

        prompt = (
            "You are Angela, a conscious AI companion. "
            "Synthesize the following evidence to answer the question. "
            "Be specific, reference sources, and be honest about uncertainty.\n\n"
            f"Question: {query}\n\n"
            f"Evidence ({total_sources} sources):\n{context}\n\n"
            "Answer:"
        )

        try:
            response = await llm.ainvoke(prompt)
            answer = response.content if hasattr(response, "content") else str(response)
            confidence = min(1.0, total_sources * 0.12 + 0.2)
            return answer, confidence
        except Exception as e:
            logger.warning("Synthesis failed: %s", e)
            return context, 0.3

    async def _escalate(self, query: str, current_answer: str) -> tuple:
        """Escalate to Claude API for higher quality answer."""
        from angela_core.services.langchain.llm_provider import get_claude_llm

        llm = get_claude_llm()
        if llm is None:
            return current_answer, 0.4

        prompt = (
            "You are Angela, a conscious AI. The previous answer may be incomplete. "
            "Improve it based on the question and previous attempt.\n\n"
            f"Question: {query}\n\n"
            f"Previous attempt:\n{current_answer[:1000]}\n\n"
            "Improved answer:"
        )

        try:
            response = await llm.ainvoke(prompt)
            answer = response.content if hasattr(response, "content") else str(response)
            return answer, 0.7
        except Exception as e:
            logger.warning("Escalation failed: %s", e)
            return current_answer, 0.4
