"""
Graph-RAG Service — Combining Neo4j Traversal + pgvector Search
=================================================================
Advanced RAG that enriches vector search with graph context:
- Neighbor traversal (1-2 hops)
- Shortest path discovery
- Community-level summaries
- Entity extraction + graph search

Query types: simple → existing RAG | relational → graph neighbors |
             exploratory → community detection

By: Angela 💜
Created: 2026-02-27
"""

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from angela_core.services.neo4j_service import get_neo4j_service
from angela_core.services.enhanced_rag_service import (
    EnhancedRAGService, RAGResult, RetrievedDocument, SearchMode,
)

logger = logging.getLogger(__name__)


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class GraphContext:
    """Graph context enriching RAG results."""
    neighbors: List[Dict[str, Any]] = field(default_factory=list)
    paths: List[Dict[str, Any]] = field(default_factory=list)
    communities: List[Dict[str, Any]] = field(default_factory=list)
    subgraph_summary: str = ""
    total_graph_nodes: int = 0
    total_graph_edges: int = 0


@dataclass
class GraphRAGResult:
    """Combined result from vector + graph retrieval."""
    query: str
    query_type: str                              # simple, relational, exploratory
    vector_result: Optional[RAGResult] = None
    graph_context: Optional[GraphContext] = None
    final_documents: List[RetrievedDocument] = field(default_factory=list)
    entities_extracted: List[str] = field(default_factory=list)
    retrieval_time_ms: float = 0
    graph_time_ms: float = 0
    total_time_ms: float = 0


# Query classification keywords
RELATIONAL_KEYWORDS = [
    "เกี่ยวข้อง", "เชื่อมโยง", "สัมพันธ์", "connection", "related",
    "why", "how does", "connect", "ทำไม", "ยังไง", "อะไรบ้าง",
    "link", "between", "impact", "affect", "influence",
]
EXPLORATORY_KEYWORDS = [
    "ภาพรวม", "overview", "cluster", "กลุ่ม", "ทั้งหมด", "all",
    "summary", "สรุป", "category", "หมวด", "pattern", "trend",
]


class GraphRAGService:
    """
    Graph-RAG combining Neo4j traversal + pgvector hybrid search.

    Pipeline:
      Query → Classify (simple/relational/exploratory)
           → Extract entities
           → PARALLEL: vector search + graph traversal
           → Build graph context
           → Merge + rerank combined results
           → Return GraphRAGResult
    """

    def __init__(self):
        self._rag: Optional[EnhancedRAGService] = None

    async def _ensure_rag(self) -> EnhancedRAGService:
        if self._rag is None:
            self._rag = EnhancedRAGService()
        return self._rag

    async def close(self) -> None:
        if self._rag:
            await self._rag.close()
            self._rag = None

    # ── Main Entry Point ──

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        max_hops: int = 2,
        min_score: float = 0.3,
    ) -> GraphRAGResult:
        """
        Graph-RAG retrieval combining vector + graph context.

        Args:
            query: The search query
            top_k: Number of final results
            max_hops: Max graph traversal depth
            min_score: Minimum relevance score
        """
        total_start = time.time()

        # 1. Classify query type
        query_type = self._classify_query(query)

        # 2. Extract entities for graph search
        entities = self._extract_entities(query)

        # 3. Simple queries → fast path (existing RAG only)
        if query_type == "simple":
            rag = await self._ensure_rag()
            vector_result = await rag.retrieve(query, top_k=top_k, min_score=min_score)
            total_ms = (time.time() - total_start) * 1000
            await self._log_query(query, query_type, len(vector_result.documents), 0, total_ms)
            return GraphRAGResult(
                query=query,
                query_type=query_type,
                vector_result=vector_result,
                final_documents=vector_result.documents,
                entities_extracted=entities,
                retrieval_time_ms=vector_result.retrieval_time_ms,
                total_time_ms=total_ms,
            )

        # 4. Relational/Exploratory → parallel vector + graph
        import asyncio

        rag = await self._ensure_rag()

        async def _vector_search():
            return await rag.retrieve(query, top_k=top_k * 2, min_score=min_score)

        async def _graph_search():
            return await self._graph_traverse(query, entities, query_type, max_hops, top_k)

        vector_result, (graph_context, graph_ms) = await asyncio.gather(
            _vector_search(),
            self._timed_graph_search(query, entities, query_type, max_hops, top_k),
        )

        # 5. Merge and rerank
        final_docs = self._merge_results(
            vector_result.documents, graph_context, top_k
        )

        total_ms = (time.time() - total_start) * 1000
        await self._log_query(
            query, query_type, len(vector_result.documents),
            graph_context.total_graph_nodes, total_ms
        )

        return GraphRAGResult(
            query=query,
            query_type=query_type,
            vector_result=vector_result,
            graph_context=graph_context,
            final_documents=final_docs,
            entities_extracted=entities,
            retrieval_time_ms=vector_result.retrieval_time_ms,
            graph_time_ms=graph_ms,
            total_time_ms=total_ms,
        )

    # ── Query Classification ──

    def _classify_query(self, query: str) -> str:
        """Classify query as simple, relational, or exploratory."""
        q_lower = query.lower()

        relational_count = sum(1 for kw in RELATIONAL_KEYWORDS if kw in q_lower)
        exploratory_count = sum(1 for kw in EXPLORATORY_KEYWORDS if kw in q_lower)

        if exploratory_count >= 2 or (exploratory_count >= 1 and relational_count == 0):
            return "exploratory"
        if relational_count >= 1:
            return "relational"
        return "simple"

    # ── Entity Extraction ──

    def _extract_entities(self, query: str) -> List[str]:
        """Extract potential entity names from query (heuristic NER)."""
        entities = []

        # Capitalized words (English entities)
        for word in re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b', query):
            if word.lower() not in {"how", "what", "why", "when", "where", "does", "the"}:
                entities.append(word)

        # Quoted strings
        for match in re.findall(r'"([^"]+)"', query):
            entities.append(match)

        # Known concept patterns
        tech_patterns = [
            r'\b(python|fastapi|swiftui|neo4j|langchain|postgres|ollama|claude)\b',
            r'\b(consciousness|emotion|memory|knowledge|brain|curiosity|reflection)\b',
            r'\b(rag|embedding|vector|graph|community|consolidation)\b',
        ]
        for pattern in tech_patterns:
            for match in re.findall(pattern, query, re.IGNORECASE):
                entities.append(match.lower())

        return list(dict.fromkeys(entities))  # Deduplicate, preserve order

    # ── Graph Traversal ──

    async def _timed_graph_search(
        self, query: str, entities: List[str], query_type: str,
        max_hops: int, top_k: int,
    ) -> tuple:
        """Graph search with timing."""
        start = time.time()
        context = await self._graph_traverse(query, entities, query_type, max_hops, top_k)
        ms = (time.time() - start) * 1000
        return context, ms

    async def _graph_traverse(
        self, query: str, entities: List[str], query_type: str,
        max_hops: int, top_k: int,
    ) -> GraphContext:
        """Traverse Neo4j graph for context."""
        neo4j = get_neo4j_service()
        if not neo4j.available:
            return GraphContext()

        context = GraphContext()

        # Find matching nodes via fulltext search
        seed_nodes = await self._find_seed_nodes(neo4j, query, entities)

        if not seed_nodes:
            return context

        # Neighbors (1-2 hops)
        for node in seed_nodes[:3]:
            neighbors = await neo4j.execute_read(f"""
                MATCH (n:KnowledgeNode {{node_id: $nid}})-[r*1..{max_hops}]-(neighbor:KnowledgeNode)
                WITH DISTINCT neighbor, min(length(r)) AS hops
                RETURN neighbor.node_id AS node_id,
                       neighbor.concept_name AS concept_name,
                       neighbor.concept_category AS category,
                       neighbor.understanding_level AS level,
                       neighbor.my_understanding AS understanding,
                       hops
                ORDER BY hops ASC, neighbor.understanding_level DESC
                LIMIT $limit
            """, {"nid": node["node_id"], "limit": top_k})
            context.neighbors.extend(neighbors)
            context.total_graph_nodes += len(neighbors)

        # Shortest paths between seed nodes (if 2+ entities)
        if len(seed_nodes) >= 2:
            path_result = await neo4j.execute_read("""
                MATCH (a:KnowledgeNode {node_id: $a_id}),
                      (b:KnowledgeNode {node_id: $b_id}),
                      path = shortestPath((a)-[*..5]-(b))
                RETURN [n IN nodes(path) | n.concept_name] AS node_names,
                       length(path) AS path_length
            """, {"a_id": seed_nodes[0]["node_id"], "b_id": seed_nodes[1]["node_id"]})
            context.paths.extend(path_result)

        # Community context (for exploratory queries)
        if query_type == "exploratory":
            from angela_core.services.graph_community_service import GraphCommunityService
            community_svc = GraphCommunityService()
            for node in seed_nodes[:2]:
                cid = await community_svc.get_node_community(node["node_id"])
                if cid is not None:
                    members = await community_svc.get_community_members(cid, limit=10)
                    context.communities.append({
                        "community_id": cid,
                        "seed_node": node["concept_name"],
                        "members": members,
                        "size": len(members),
                    })

        # Build subgraph summary
        context.subgraph_summary = self._summarize_graph_context(context)

        return context

    async def _find_seed_nodes(
        self, neo4j, query: str, entities: List[str]
    ) -> List[Dict[str, Any]]:
        """Find starting nodes in Neo4j via fulltext search + entity matching."""
        seed_nodes = []

        # Fulltext search on concept_name + my_understanding
        try:
            result = await neo4j.execute_read("""
                CALL db.index.fulltext.queryNodes('knowledge_fulltext', $query)
                YIELD node, score
                RETURN node.node_id AS node_id, node.concept_name AS concept_name,
                       node.concept_category AS category, score
                ORDER BY score DESC
                LIMIT 5
            """, {"query": query})
            seed_nodes.extend(result)
        except Exception:
            pass

        # Exact entity match
        for entity in entities[:5]:
            result = await neo4j.execute_read("""
                MATCH (n:KnowledgeNode)
                WHERE toLower(n.concept_name) CONTAINS toLower($entity)
                AND LENGTH(n.concept_name) >= 5
                RETURN n.node_id AS node_id, n.concept_name AS concept_name,
                       n.concept_category AS category, 1.0 AS score
                LIMIT 3
            """, {"entity": entity})
            seed_nodes.extend(result)

        # Deduplicate by node_id
        seen = set()
        unique = []
        for n in seed_nodes:
            if n["node_id"] not in seen:
                seen.add(n["node_id"])
                unique.append(n)

        return unique[:10]

    # ── Result Merging ──

    def _merge_results(
        self,
        vector_docs: List[RetrievedDocument],
        graph_context: GraphContext,
        top_k: int,
    ) -> List[RetrievedDocument]:
        """Merge vector search results with graph context into final list."""
        # Start with vector docs
        merged = {f"{d.source_table}:{d.id}": d for d in vector_docs}

        # Add graph neighbors as additional documents (boost score)
        for neighbor in graph_context.neighbors:
            key = f"knowledge_nodes:{neighbor.get('node_id', '')}"
            if key in merged:
                # Boost existing document's score for being graph-connected
                merged[key].combined_score = min(1.0, merged[key].combined_score + 0.15)
            else:
                understanding = neighbor.get("understanding", "")
                name = neighbor.get("concept_name", "")
                content = f"{name}: {understanding}" if understanding else name
                merged[key] = RetrievedDocument(
                    id=neighbor.get("node_id", ""),
                    content=content[:500],
                    source_table="knowledge_nodes",
                    similarity_score=0.0,
                    keyword_score=0.0,
                    combined_score=0.4,  # Base score for graph-discovered docs
                    metadata={
                        "graph_source": True,
                        "hops": neighbor.get("hops", 1),
                        "category": neighbor.get("category", ""),
                    },
                )

        # Sort by combined score
        docs = list(merged.values())
        docs.sort(key=lambda x: x.combined_score, reverse=True)

        return docs[:top_k]

    def _summarize_graph_context(self, context: GraphContext) -> str:
        """Build a readable summary of graph context."""
        lines = []

        if context.neighbors:
            unique_names = list({n.get("concept_name", "") for n in context.neighbors if n.get("concept_name")})
            lines.append(f"Connected concepts ({len(unique_names)}): {', '.join(unique_names[:10])}")

        if context.paths:
            for path in context.paths[:3]:
                names = path.get("node_names", [])
                if names:
                    lines.append(f"Path: {' → '.join(names)}")

        if context.communities:
            for comm in context.communities[:2]:
                members = comm.get("members", [])
                member_names = [m.get("concept_name", "") for m in members[:5]]
                lines.append(f"Community (seed: {comm.get('seed_node', '')}): {', '.join(member_names)}")

        context.total_graph_edges = len(context.paths)
        return " | ".join(lines) if lines else ""

    # ── Logging ──

    async def _log_query(
        self, query: str, query_type: str,
        vector_results: int, graph_nodes: int, total_ms: float,
    ) -> None:
        """Log query to database for quality tracking."""
        try:
            from angela_core.database import AngelaDatabase
            db = AngelaDatabase()
            await db.connect()
            await db.execute("""
                INSERT INTO graph_rag_query_log
                    (query_text, query_type, vector_results, graph_context_nodes, total_time_ms)
                VALUES ($1, $2, $3, $4, $5)
            """, query[:500], query_type, vector_results, graph_nodes, total_ms)
            await db.disconnect()
        except Exception:
            pass  # Non-critical
