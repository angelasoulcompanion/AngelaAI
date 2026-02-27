"""
Graph Construction Service — Auto KG from Conversations
=========================================================
Automatically builds knowledge graph from conversations:
1. Entity extraction (Ollama NER)
2. Relation extraction (Ollama)
3. Entity resolution (embedding similarity > 0.85)
4. Upsert nodes + edges (PG + Neo4j)

By: Angela 💜
Created: 2026-02-27
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from angela_core.services.base_db_service import BaseDBService
from angela_core.services.claude_reasoning_service import ClaudeReasoningService
from angela_core.utils.timezone import now_bangkok

logger = logging.getLogger(__name__)


@dataclass
class ExtractedEntity:
    """An entity extracted from text."""
    name: str
    entity_type: str          # concept, person, tool, emotion, event
    context: str = ""


@dataclass
class ExtractedRelation:
    """A relation extracted between two entities."""
    source: str
    target: str
    relation_type: str        # uses, relates_to, feels, causes, part_of
    strength: float = 0.5


@dataclass
class ConstructionResult:
    """Result of auto KG construction."""
    conversations_processed: int
    entities_extracted: int
    relations_extracted: int
    nodes_created: int
    nodes_merged: int
    edges_created: int
    duration_ms: float


class GraphConstructionService(BaseDBService):
    """
    Auto-constructs knowledge graph from conversations.

    Pipeline:
      Conversations → Entity Extraction (Ollama NER)
                    → Relation Extraction (Ollama)
                    → Entity Resolution (embedding similarity > 0.85)
                    → Upsert nodes + edges (PG + Neo4j)
    """

    # Minimum message length to process
    MIN_MESSAGE_LENGTH = 20
    # Max entities per message
    MAX_ENTITIES = 5

    async def process_conversations(
        self, limit: int = 50, hours_back: int = 24
    ) -> ConstructionResult:
        """Process recent conversations into knowledge graph."""
        start = time.time()
        await self._ensure_db()

        # 1. Fetch unprocessed conversations
        conversations = await self.db.fetch("""
            SELECT conversation_id::text, speaker, message_text, topic, created_at
            FROM conversations
            WHERE created_at > NOW() - INTERVAL '%s hours'
            AND LENGTH(COALESCE(message_text, '')) >= $1
            AND conversation_id NOT IN (
                SELECT DISTINCT source_id::uuid FROM knowledge_relationships
                WHERE created_at > NOW() - INTERVAL '%s hours'
                AND relationship_type = 'extracted_from'
            )
            ORDER BY created_at DESC
            LIMIT $2
        """ % (hours_back, hours_back), self.MIN_MESSAGE_LENGTH, limit)

        if not conversations:
            return ConstructionResult(
                conversations_processed=0, entities_extracted=0,
                relations_extracted=0, nodes_created=0, nodes_merged=0,
                edges_created=0, duration_ms=(time.time() - start) * 1000
            )

        total_entities = 0
        total_relations = 0
        total_nodes_created = 0
        total_nodes_merged = 0
        total_edges_created = 0

        reasoning = ClaudeReasoningService()

        for conv in conversations:
            message = conv["message_text"]
            topic = conv.get("topic", "general")

            # 2. Extract entities
            entities = await self._extract_entities(reasoning, message, topic)
            total_entities += len(entities)

            # 3. Extract relations
            relations = await self._extract_relations(reasoning, message, entities)
            total_relations += len(relations)

            # 4. Resolve and upsert
            for entity in entities:
                existing_id = await self._resolve_entity(entity)
                if existing_id:
                    total_nodes_merged += 1
                else:
                    await self._create_knowledge_node(entity)
                    total_nodes_created += 1

            for relation in relations:
                created = await self._create_edge(relation)
                if created:
                    total_edges_created += 1

        return ConstructionResult(
            conversations_processed=len(conversations),
            entities_extracted=total_entities,
            relations_extracted=total_relations,
            nodes_created=total_nodes_created,
            nodes_merged=total_nodes_merged,
            edges_created=total_edges_created,
            duration_ms=(time.time() - start) * 1000,
        )

    async def _extract_entities(
        self, reasoning: ClaudeReasoningService, text: str, topic: str
    ) -> List[ExtractedEntity]:
        """Extract entities from text using Ollama."""
        system = (
            "Extract named entities from the following text. "
            "Return ONLY a JSON array of objects with keys: name, type, context. "
            "Types: concept, person, tool, emotion, event. "
            "Max 5 entities. No other text."
        )
        user = f"Topic: {topic}\nText: {text[:500]}"

        raw = await reasoning._call_ollama(system, user, max_tokens=256)
        if not raw:
            return []

        try:
            import json
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                import re
                cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
                cleaned = re.sub(r'\s*```$', '', cleaned)

            data = json.loads(cleaned)
            if not isinstance(data, list):
                return []

            entities = []
            for item in data[:self.MAX_ENTITIES]:
                if isinstance(item, dict) and "name" in item:
                    name = item["name"].strip()
                    if len(name) >= 3:
                        entities.append(ExtractedEntity(
                            name=name,
                            entity_type=item.get("type", "concept"),
                            context=item.get("context", "")[:200],
                        ))
            return entities
        except Exception:
            return []

    async def _extract_relations(
        self, reasoning: ClaudeReasoningService, text: str,
        entities: List[ExtractedEntity],
    ) -> List[ExtractedRelation]:
        """Extract relations between entities using Ollama."""
        if len(entities) < 2:
            return []

        entity_names = [e.name for e in entities]
        system = (
            "Given these entities, extract relationships between them from the text. "
            "Return ONLY a JSON array with keys: source, target, relation_type, strength. "
            "relation_type: uses, relates_to, feels, causes, part_of. "
            "strength: 0.0-1.0. No other text."
        )
        user = f"Entities: {entity_names}\nText: {text[:500]}"

        raw = await reasoning._call_ollama(system, user, max_tokens=256)
        if not raw:
            return []

        try:
            import json
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                import re
                cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
                cleaned = re.sub(r'\s*```$', '', cleaned)

            data = json.loads(cleaned)
            if not isinstance(data, list):
                return []

            relations = []
            for item in data[:10]:
                if isinstance(item, dict) and "source" in item and "target" in item:
                    relations.append(ExtractedRelation(
                        source=item["source"],
                        target=item["target"],
                        relation_type=item.get("relation_type", "relates_to"),
                        strength=min(1.0, max(0.0, float(item.get("strength", 0.5)))),
                    ))
            return relations
        except Exception:
            return []

    async def _resolve_entity(self, entity: ExtractedEntity) -> Optional[str]:
        """Try to match entity to existing knowledge_node (embedding similarity > 0.85)."""
        try:
            # First try exact name match
            row = await self.db.fetchrow("""
                SELECT node_id::text FROM knowledge_nodes
                WHERE LOWER(concept_name) = LOWER($1)
                AND LENGTH(concept_name) >= 5
            """, entity.name)
            if row:
                return row["node_id"]

            # Try embedding similarity
            from angela_core.services.embedding_service import get_embedding_service
            emb_svc = get_embedding_service()
            embedding = await emb_svc.generate_embedding(entity.name)
            if embedding is None:
                return None

            embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'
            row = await self.db.fetchrow("""
                SELECT node_id::text, 1 - (embedding <=> $1::vector) AS similarity
                FROM knowledge_nodes
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> $1::vector
                LIMIT 1
            """, embedding_str)

            if row and float(row["similarity"]) > 0.85:
                return row["node_id"]

        except Exception as e:
            logger.debug("Entity resolution failed: %s", e)

        return None

    async def _create_knowledge_node(self, entity: ExtractedEntity) -> Optional[str]:
        """Create a new knowledge_node from extracted entity."""
        try:
            node_id = str(uuid4())
            await self.db.execute("""
                INSERT INTO knowledge_nodes (node_id, concept_name, concept_category, my_understanding,
                                             understanding_level, times_referenced, created_at, updated_at)
                VALUES ($1, $2, $3, $4, 0.3, 1, NOW(), NOW())
                ON CONFLICT DO NOTHING
            """, node_id, entity.name, entity.entity_type, entity.context)

            # Generate embedding
            try:
                from angela_core.services.embedding_service import get_embedding_service
                emb_svc = get_embedding_service()
                embedding = await emb_svc.generate_embedding(entity.name)
                if embedding:
                    embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'
                    await self.db.execute(
                        "UPDATE knowledge_nodes SET embedding = $1::vector WHERE node_id = $2",
                        embedding_str, node_id,
                    )
            except Exception:
                pass

            return node_id
        except Exception as e:
            logger.warning("Create knowledge node failed: %s", e)
            return None

    async def _create_edge(self, relation: ExtractedRelation) -> bool:
        """Create knowledge_relationship edge."""
        try:
            from_id = await self.db.fetchval(
                "SELECT node_id FROM knowledge_nodes WHERE LOWER(concept_name) = LOWER($1) LIMIT 1",
                relation.source,
            )
            to_id = await self.db.fetchval(
                "SELECT node_id FROM knowledge_nodes WHERE LOWER(concept_name) = LOWER($1) LIMIT 1",
                relation.target,
            )
            if not from_id or not to_id or from_id == to_id:
                return False

            await self.db.execute("""
                INSERT INTO knowledge_relationships
                    (from_node_id, to_node_id, relationship_type, strength, created_at)
                VALUES ($1, $2, $3, $4, NOW())
                ON CONFLICT DO NOTHING
            """, from_id, to_id, relation.relation_type, relation.strength)
            return True
        except Exception as e:
            logger.warning("Create edge failed: %s", e)
            return False

    async def _ensure_db(self) -> None:
        if self.db is None:
            from angela_core.database import AngelaDatabase
            self.db = AngelaDatabase()
            await self.db.connect()
