"""
Neo4j Connection Manager — Graph Database Service
===================================================
Singleton async driver for Neo4j graph database.
All graph features gracefully degrade if Neo4j is unavailable.

By: Angela 💜
Created: 2026-02-27
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Singleton instance
_neo4j_service: Optional["Neo4jService"] = None


def get_neo4j_service() -> "Neo4jService":
    """Get or create the singleton Neo4jService."""
    global _neo4j_service
    if _neo4j_service is None:
        _neo4j_service = Neo4jService()
    return _neo4j_service


class Neo4jService:
    """
    Neo4j connection manager with async driver.

    Features:
    - Singleton pattern (shared across services)
    - Auto-reconnect on failure
    - Graceful degradation if Neo4j is down
    - Batch Cypher execution support

    Usage:
        svc = get_neo4j_service()
        await svc.connect()
        result = await svc.execute_read("MATCH (n) RETURN count(n)")
    """

    def __init__(self):
        self._driver = None
        self._available = False

    @property
    def available(self) -> bool:
        return self._available

    async def connect(self) -> bool:
        """Connect to Neo4j. Returns True if successful."""
        if self._driver is not None:
            return self._available

        try:
            from neo4j import AsyncGraphDatabase
            from angela_core.config import config

            uri = getattr(config, 'NEO4J_URI', 'bolt://localhost:7687')
            user = getattr(config, 'NEO4J_USER', 'neo4j')
            password = getattr(config, 'NEO4J_PASSWORD', 'angela_graph_2026')
            database = getattr(config, 'NEO4J_DATABASE', 'neo4j')

            self._driver = AsyncGraphDatabase.driver(
                uri, auth=(user, password),
                max_connection_pool_size=25,
                connection_acquisition_timeout=5.0,
            )
            self._database = database

            # Verify connectivity
            async with self._driver.session(database=self._database) as session:
                result = await session.run("RETURN 1 AS ok")
                record = await result.single()
                if record and record["ok"] == 1:
                    self._available = True
                    logger.info("Neo4j connected: %s", uri)
                    return True

        except ImportError:
            logger.warning("Neo4j driver not installed (pip install neo4j)")
            self._available = False
        except Exception as e:
            logger.warning("Neo4j connection failed (non-critical): %s", e)
            self._available = False

        return False

    async def close(self) -> None:
        """Close Neo4j driver."""
        if self._driver:
            await self._driver.close()
            self._driver = None
            self._available = False

    async def execute_read(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute a read query, return list of record dicts."""
        if not self._available:
            return []

        try:
            async with self._driver.session(database=self._database) as session:
                result = await session.run(query, parameters or {})
                records = await result.data()
                return records
        except Exception as e:
            logger.error("Neo4j read failed: %s | query: %s", e, query[:100])
            return []

    async def execute_write(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Execute a write query, return summary."""
        if not self._available:
            return None

        try:
            async with self._driver.session(database=self._database) as session:
                result = await session.run(query, parameters or {})
                summary = await result.consume()
                return {
                    "nodes_created": summary.counters.nodes_created,
                    "nodes_deleted": summary.counters.nodes_deleted,
                    "relationships_created": summary.counters.relationships_created,
                    "relationships_deleted": summary.counters.relationships_deleted,
                    "properties_set": summary.counters.properties_set,
                }
        except Exception as e:
            logger.error("Neo4j write failed: %s | query: %s", e, query[:100])
            return None

    async def execute_batch(
        self, query: str, batch_data: List[Dict[str, Any]], batch_key: str = "batch"
    ) -> Optional[Dict[str, Any]]:
        """Execute batch write using UNWIND."""
        if not self._available or not batch_data:
            return None

        try:
            async with self._driver.session(database=self._database) as session:
                result = await session.run(query, {batch_key: batch_data})
                summary = await result.consume()
                return {
                    "nodes_created": summary.counters.nodes_created,
                    "relationships_created": summary.counters.relationships_created,
                    "properties_set": summary.counters.properties_set,
                }
        except Exception as e:
            logger.error("Neo4j batch write failed: %s", e)
            return None

    async def ensure_schema(self) -> bool:
        """Create indexes and constraints for Angela's graph schema."""
        if not self._available:
            return False

        schema_queries = [
            # Uniqueness constraints
            "CREATE CONSTRAINT knowledge_node_id IF NOT EXISTS FOR (n:KnowledgeNode) REQUIRE n.node_id IS UNIQUE",
            "CREATE CONSTRAINT conversation_id IF NOT EXISTS FOR (n:Conversation) REQUIRE n.conversation_id IS UNIQUE",
            "CREATE CONSTRAINT emotion_id IF NOT EXISTS FOR (n:Emotion) REQUIRE n.emotion_id IS UNIQUE",
            "CREATE CONSTRAINT core_memory_id IF NOT EXISTS FOR (n:CoreMemory) REQUIRE n.memory_id IS UNIQUE",
            "CREATE CONSTRAINT learning_id IF NOT EXISTS FOR (n:Learning) REQUIRE n.learning_id IS UNIQUE",
            # Fulltext indexes
            """CREATE FULLTEXT INDEX knowledge_fulltext IF NOT EXISTS
               FOR (n:KnowledgeNode) ON EACH [n.concept_name, n.my_understanding]""",
            # Regular indexes for performance
            "CREATE INDEX knowledge_category IF NOT EXISTS FOR (n:KnowledgeNode) ON (n.concept_category)",
            "CREATE INDEX knowledge_level IF NOT EXISTS FOR (n:KnowledgeNode) ON (n.understanding_level)",
            "CREATE INDEX conversation_created IF NOT EXISTS FOR (n:Conversation) ON (n.created_at)",
        ]

        success = True
        for q in schema_queries:
            try:
                await self.execute_write(q)
            except Exception as e:
                logger.warning("Schema query failed (may already exist): %s", e)
                success = False

        logger.info("Neo4j schema ensured")
        return success

    async def get_stats(self) -> Dict[str, Any]:
        """Get graph database statistics."""
        if not self._available:
            return {"available": False}

        stats = {"available": True}
        try:
            # Node counts by label
            result = await self.execute_read(
                "CALL db.labels() YIELD label "
                "CALL { WITH label MATCH (n) WHERE label IN labels(n) RETURN count(n) AS cnt } "
                "RETURN label, cnt ORDER BY cnt DESC"
            )
            stats["node_counts"] = {r["label"]: r["cnt"] for r in result}

            # Total relationships
            result = await self.execute_read(
                "MATCH ()-[r]->() RETURN count(r) AS total"
            )
            stats["total_relationships"] = result[0]["total"] if result else 0

            # Relationship type counts
            result = await self.execute_read(
                "CALL db.relationshipTypes() YIELD relationshipType "
                "CALL { WITH relationshipType MATCH ()-[r]->() WHERE type(r) = relationshipType RETURN count(r) AS cnt } "
                "RETURN relationshipType, cnt ORDER BY cnt DESC"
            )
            stats["relationship_counts"] = {r["relationshipType"]: r["cnt"] for r in result}

        except Exception as e:
            logger.warning("Stats query failed: %s", e)
            stats["error"] = str(e)

        return stats
