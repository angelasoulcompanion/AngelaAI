"""
Multi-Hop Inference Service — A→B→C Reasoning Through Graph
==============================================================
Traces reasoning paths through the knowledge graph to answer
complex relational questions with evidence chains.

Example: "Why is Python related to Angela's consciousness?"
→ Python → FastAPI → Angela Brain → Consciousness

By: Angela 💜
Created: 2026-02-27
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from angela_core.services.neo4j_service import get_neo4j_service

logger = logging.getLogger(__name__)


@dataclass
class InferenceStep:
    """One step in the inference chain."""
    from_concept: str
    to_concept: str
    relation: str
    strength: float = 0.5
    evidence: str = ""


@dataclass
class InferenceResult:
    """Result of multi-hop inference."""
    query: str
    paths: List[List[InferenceStep]]
    summary: str
    confidence: float
    total_hops: int
    duration_ms: float


class MultiHopInferenceService:
    """
    Traces reasoning paths through Angela's knowledge graph.

    Supports:
    - Direct paths: A→B (1 hop)
    - Multi-hop: A→B→C→D (up to 5 hops)
    - All shortest paths between two concepts
    - Weighted path scoring (by edge strength)
    """

    MAX_HOPS = 5

    async def infer(
        self,
        query: str,
        source_concept: Optional[str] = None,
        target_concept: Optional[str] = None,
        max_hops: int = 3,
    ) -> InferenceResult:
        """
        Trace reasoning paths for a query.

        If source/target given → find paths between them.
        Otherwise → extract entities from query and find connections.
        """
        start = time.time()

        neo4j = get_neo4j_service()
        if not neo4j.available:
            return InferenceResult(
                query=query, paths=[], summary="Neo4j unavailable",
                confidence=0.0, total_hops=0,
                duration_ms=(time.time() - start) * 1000,
            )

        # Extract source/target if not provided
        if not source_concept or not target_concept:
            source_concept, target_concept = await self._extract_endpoints(neo4j, query)

        if not source_concept or not target_concept:
            return InferenceResult(
                query=query, paths=[], summary="Could not identify source/target concepts",
                confidence=0.0, total_hops=0,
                duration_ms=(time.time() - start) * 1000,
            )

        # Find paths
        paths = await self._find_paths(neo4j, source_concept, target_concept, max_hops)

        # Build summary
        summary = self._build_summary(source_concept, target_concept, paths)

        # Calculate confidence
        confidence = self._calculate_confidence(paths)

        total_hops = max(len(p) for p in paths) if paths else 0

        return InferenceResult(
            query=query,
            paths=paths,
            summary=summary,
            confidence=confidence,
            total_hops=total_hops,
            duration_ms=(time.time() - start) * 1000,
        )

    async def _extract_endpoints(
        self, neo4j, query: str
    ) -> tuple:
        """Extract source and target concepts from query."""
        # Search for matching nodes
        result = await neo4j.execute_read("""
            CALL db.index.fulltext.queryNodes('knowledge_fulltext', $query)
            YIELD node, score
            WHERE score > 0.3
            RETURN node.concept_name AS name, node.node_id AS id, score
            ORDER BY score DESC
            LIMIT 4
        """, {"query": query})

        if len(result) >= 2:
            return result[0]["name"], result[1]["name"]
        elif len(result) == 1:
            return result[0]["name"], None

        return None, None

    async def _find_paths(
        self, neo4j, source: str, target: str, max_hops: int,
    ) -> List[List[InferenceStep]]:
        """Find all shortest paths between source and target."""
        max_hops = min(max_hops, self.MAX_HOPS)

        result = await neo4j.execute_read(f"""
            MATCH (a:KnowledgeNode), (b:KnowledgeNode)
            WHERE toLower(a.concept_name) CONTAINS toLower($source)
            AND toLower(b.concept_name) CONTAINS toLower($target)
            WITH a, b LIMIT 1
            MATCH path = allShortestPaths((a)-[*..{max_hops}]-(b))
            RETURN
                [n IN nodes(path) | n.concept_name] AS node_names,
                [r IN relationships(path) | {{type: type(r), strength: COALESCE(r.strength, 0.5)}}] AS rels,
                length(path) AS path_length
            LIMIT 5
        """, {"source": source, "target": target})

        paths = []
        for r in result:
            node_names = r.get("node_names", [])
            rels = r.get("rels", [])
            steps = []
            for i in range(len(rels)):
                steps.append(InferenceStep(
                    from_concept=node_names[i] if i < len(node_names) else "?",
                    to_concept=node_names[i + 1] if i + 1 < len(node_names) else "?",
                    relation=rels[i].get("type", "RELATES_TO") if isinstance(rels[i], dict) else "RELATES_TO",
                    strength=float(rels[i].get("strength", 0.5)) if isinstance(rels[i], dict) else 0.5,
                ))
            if steps:
                paths.append(steps)

        return paths

    def _build_summary(
        self, source: str, target: str, paths: List[List[InferenceStep]]
    ) -> str:
        """Build a readable summary of the inference paths."""
        if not paths:
            return f"No path found between '{source}' and '{target}'"

        lines = [f"Found {len(paths)} path(s) from '{source}' to '{target}':"]
        for i, path in enumerate(paths[:3]):
            names = [path[0].from_concept]
            for step in path:
                names.append(step.to_concept)
            chain = " → ".join(names)
            avg_strength = sum(s.strength for s in path) / len(path)
            lines.append(f"  Path {i+1} ({len(path)} hops, strength={avg_strength:.2f}): {chain}")

        return "\n".join(lines)

    def _calculate_confidence(self, paths: List[List[InferenceStep]]) -> float:
        """Calculate confidence based on path quality."""
        if not paths:
            return 0.0

        # Best path score
        best_score = 0.0
        for path in paths:
            if not path:
                continue
            # Average strength along path
            avg_strength = sum(s.strength for s in path) / len(path)
            # Shorter paths are more confident
            hop_penalty = max(0.0, 1.0 - len(path) * 0.15)
            score = avg_strength * hop_penalty
            best_score = max(best_score, score)

        # Multiple paths increase confidence
        path_bonus = min(0.2, len(paths) * 0.05)

        return min(1.0, best_score + path_bonus)
