"""
Knowledge Reasoner - Knowledge Graph powered reasoning for Angela AGI

This module enables Angela to:
- Use knowledge graph for reasoning
- Find connections between concepts
- Transfer knowledge across domains
- Make inferences from relationships
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum


class RelationshipType(Enum):
    """Types of relationships between concepts"""
    IS_A = "is_a"                   # Taxonomy
    PART_OF = "part_of"             # Composition
    CAUSES = "causes"               # Causation
    RELATED_TO = "related_to"       # General relation
    REQUIRES = "requires"           # Dependency
    SIMILAR_TO = "similar_to"       # Similarity
    OPPOSITE_OF = "opposite_of"     # Opposition
    USED_BY = "used_by"             # Usage
    EXAMPLE_OF = "example_of"       # Instance


@dataclass
class KnowledgeNode:
    """A node in the knowledge graph"""
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    concept: str = ""
    category: str = ""
    description: str = ""
    understanding_level: float = 0.5  # 0-1
    times_referenced: int = 0
    last_used: Optional[datetime] = None
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'node_id': self.node_id,
            'concept': self.concept,
            'category': self.category,
            'understanding_level': self.understanding_level,
            'times_referenced': self.times_referenced
        }


@dataclass
class KnowledgeRelationship:
    """A relationship between two knowledge nodes"""
    relationship_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_node_id: str = ""
    to_node_id: str = ""
    relationship_type: RelationshipType = RelationshipType.RELATED_TO
    strength: float = 0.5  # 0-1
    evidence: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Inference:
    """An inference made from knowledge"""
    inference_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    statement: str = ""
    confidence: float = 0.5
    reasoning_path: List[str] = field(default_factory=list)
    supporting_nodes: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ReasoningContext:
    """Context for reasoning about a query"""
    query: str = ""
    direct_concepts: List[KnowledgeNode] = field(default_factory=list)
    related_concepts: List[KnowledgeNode] = field(default_factory=list)
    relationships: List[KnowledgeRelationship] = field(default_factory=list)
    inferences: List[Inference] = field(default_factory=list)


class KnowledgeReasoner:
    """
    Uses knowledge graph for reasoning and inference.

    Capabilities:
    - Semantic search for relevant concepts
    - Path finding between concepts
    - Inference generation
    - Cross-domain knowledge transfer

    Usage:
        reasoner = KnowledgeReasoner(db)
        context = await reasoner.get_reasoning_context("How does X relate to Y?")
        inferences = await reasoner.make_inferences(context)
    """

    def __init__(self, db=None):
        self.db = db
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.relationships: List[KnowledgeRelationship] = []
        self.inference_cache: Dict[str, List[Inference]] = {}

    async def load_knowledge_graph(self) -> int:
        """Load knowledge graph from database"""
        if not self.db:
            return 0

        try:
            # Load nodes
            nodes = await self.db.fetch("""
                SELECT node_id, concept, category, understanding_level,
                       times_referenced, last_used
                FROM knowledge_nodes
                LIMIT 1000
            """)

            for row in nodes:
                node = KnowledgeNode(
                    node_id=str(row['node_id']),
                    concept=row['concept'],
                    category=row['category'] or '',
                    understanding_level=row['understanding_level'] or 0.5,
                    times_referenced=row['times_referenced'] or 0,
                    last_used=row['last_used']
                )
                self.nodes[node.node_id] = node

            # Load relationships
            rels = await self.db.fetch("""
                SELECT relationship_id, from_node_id, to_node_id,
                       relationship_type, strength
                FROM knowledge_relationships
                LIMIT 2000
            """)

            for row in rels:
                try:
                    rel_type = RelationshipType(row['relationship_type'])
                except ValueError:
                    rel_type = RelationshipType.RELATED_TO

                rel = KnowledgeRelationship(
                    relationship_id=str(row['relationship_id']),
                    from_node_id=str(row['from_node_id']),
                    to_node_id=str(row['to_node_id']),
                    relationship_type=rel_type,
                    strength=row['strength'] or 0.5
                )
                self.relationships.append(rel)

            return len(self.nodes)

        except Exception as e:
            print(f"Warning: Failed to load knowledge graph: {e}")
            return 0

    async def get_reasoning_context(self, query: str) -> ReasoningContext:
        """
        Build reasoning context for a query.

        Finds:
        - Directly relevant concepts
        - Related concepts via relationships
        - Potential inference paths
        """
        context = ReasoningContext(query=query)

        # 1. Find directly relevant concepts (simple text matching for now)
        query_lower = query.lower()
        direct = []
        for node in self.nodes.values():
            if node.concept.lower() in query_lower or query_lower in node.concept.lower():
                direct.append(node)
                node.times_referenced += 1

        context.direct_concepts = direct[:10]  # Limit to 10

        # 2. Find related concepts through relationships
        related_ids = set()
        for node in context.direct_concepts:
            for rel in self.relationships:
                if rel.from_node_id == node.node_id:
                    related_ids.add(rel.to_node_id)
                    context.relationships.append(rel)
                elif rel.to_node_id == node.node_id:
                    related_ids.add(rel.from_node_id)
                    context.relationships.append(rel)

        # Get related nodes
        for node_id in related_ids:
            if node_id in self.nodes and node_id not in [n.node_id for n in context.direct_concepts]:
                context.related_concepts.append(self.nodes[node_id])

        context.related_concepts = context.related_concepts[:20]  # Limit

        return context

    async def find_path(
        self,
        from_concept: str,
        to_concept: str,
        max_depth: int = 4
    ) -> List[List[str]]:
        """
        Find paths between two concepts in the knowledge graph.

        Uses BFS to find all paths up to max_depth.
        """
        # Find source and target nodes
        source_nodes = [n for n in self.nodes.values() if from_concept.lower() in n.concept.lower()]
        target_nodes = [n for n in self.nodes.values() if to_concept.lower() in n.concept.lower()]

        if not source_nodes or not target_nodes:
            return []

        source_id = source_nodes[0].node_id
        target_ids = {n.node_id for n in target_nodes}

        # BFS for paths
        paths = []
        queue = [(source_id, [source_id])]
        visited = set()

        while queue and len(paths) < 5:  # Limit to 5 paths
            current, path = queue.pop(0)

            if current in target_ids:
                # Convert IDs to concept names
                concept_path = [self.nodes[nid].concept for nid in path if nid in self.nodes]
                paths.append(concept_path)
                continue

            if len(path) >= max_depth:
                continue

            if current in visited:
                continue
            visited.add(current)

            # Find neighbors
            for rel in self.relationships:
                if rel.from_node_id == current and rel.to_node_id not in path:
                    queue.append((rel.to_node_id, path + [rel.to_node_id]))
                elif rel.to_node_id == current and rel.from_node_id not in path:
                    queue.append((rel.from_node_id, path + [rel.from_node_id]))

        return paths

    async def make_inferences(self, context: ReasoningContext) -> List[Inference]:
        """
        Make inferences from the reasoning context.

        Uses relationships to generate logical conclusions.
        """
        inferences = []

        # 1. Direct relationship inferences
        for rel in context.relationships:
            if rel.from_node_id in self.nodes and rel.to_node_id in self.nodes:
                from_node = self.nodes[rel.from_node_id]
                to_node = self.nodes[rel.to_node_id]

                statement = self._generate_inference_statement(from_node, to_node, rel)
                if statement:
                    inference = Inference(
                        statement=statement,
                        confidence=rel.strength * 0.8,
                        reasoning_path=[from_node.concept, rel.relationship_type.value, to_node.concept],
                        supporting_nodes=[rel.from_node_id, rel.to_node_id]
                    )
                    inferences.append(inference)

        # 2. Transitive inferences (A->B->C implies A->C for certain relations)
        transitive_types = {RelationshipType.IS_A, RelationshipType.PART_OF, RelationshipType.CAUSES}

        for rel1 in context.relationships:
            if rel1.relationship_type not in transitive_types:
                continue

            for rel2 in context.relationships:
                if rel2.relationship_type != rel1.relationship_type:
                    continue

                if rel1.to_node_id == rel2.from_node_id:
                    # Transitive: A->B->C
                    if rel1.from_node_id in self.nodes and rel2.to_node_id in self.nodes:
                        from_node = self.nodes[rel1.from_node_id]
                        to_node = self.nodes[rel2.to_node_id]

                        statement = f"Through transitivity: {from_node.concept} {rel1.relationship_type.value} {to_node.concept}"
                        inference = Inference(
                            statement=statement,
                            confidence=rel1.strength * rel2.strength * 0.7,
                            reasoning_path=[
                                from_node.concept,
                                "->", self.nodes[rel1.to_node_id].concept if rel1.to_node_id in self.nodes else "?",
                                "->", to_node.concept
                            ],
                            supporting_nodes=[rel1.from_node_id, rel1.to_node_id, rel2.to_node_id]
                        )
                        inferences.append(inference)

        # Sort by confidence
        inferences.sort(key=lambda i: i.confidence, reverse=True)

        context.inferences = inferences[:10]  # Top 10
        return context.inferences

    def _generate_inference_statement(
        self,
        from_node: KnowledgeNode,
        to_node: KnowledgeNode,
        rel: KnowledgeRelationship
    ) -> str:
        """Generate human-readable inference statement"""
        templates = {
            RelationshipType.IS_A: f"{from_node.concept} is a type of {to_node.concept}",
            RelationshipType.PART_OF: f"{from_node.concept} is part of {to_node.concept}",
            RelationshipType.CAUSES: f"{from_node.concept} causes {to_node.concept}",
            RelationshipType.REQUIRES: f"{from_node.concept} requires {to_node.concept}",
            RelationshipType.SIMILAR_TO: f"{from_node.concept} is similar to {to_node.concept}",
            RelationshipType.USED_BY: f"{from_node.concept} is used by {to_node.concept}",
            RelationshipType.EXAMPLE_OF: f"{from_node.concept} is an example of {to_node.concept}",
            RelationshipType.RELATED_TO: f"{from_node.concept} relates to {to_node.concept}",
            RelationshipType.OPPOSITE_OF: f"{from_node.concept} is opposite of {to_node.concept}",
        }
        return templates.get(rel.relationship_type, "")

    async def get_related_concepts(
        self,
        concept: str,
        depth: int = 1
    ) -> List[Dict[str, Any]]:
        """Get concepts related to a given concept"""
        # Find the concept node
        source_nodes = [n for n in self.nodes.values() if concept.lower() in n.concept.lower()]
        if not source_nodes:
            return []

        source = source_nodes[0]
        related = []

        # Find direct relationships
        for rel in self.relationships:
            other_id = None
            direction = ""

            if rel.from_node_id == source.node_id:
                other_id = rel.to_node_id
                direction = "outgoing"
            elif rel.to_node_id == source.node_id:
                other_id = rel.from_node_id
                direction = "incoming"

            if other_id and other_id in self.nodes:
                other = self.nodes[other_id]
                related.append({
                    'concept': other.concept,
                    'category': other.category,
                    'relationship': rel.relationship_type.value,
                    'direction': direction,
                    'strength': rel.strength
                })

        return related

    async def get_domain_concepts(self, domain: str) -> List[KnowledgeNode]:
        """Get all concepts in a domain/category"""
        return [
            node for node in self.nodes.values()
            if node.category and domain.lower() in node.category.lower()
        ]

    async def find_analogies(
        self,
        source_domain: str,
        target_domain: str
    ) -> List[Dict[str, Any]]:
        """
        Find analogous patterns between two domains.

        Looks for similar relationship structures.
        """
        # Get nodes from each domain
        source_nodes = await self.get_domain_concepts(source_domain)
        target_nodes = await self.get_domain_concepts(target_domain)

        if not source_nodes or not target_nodes:
            return []

        analogies = []

        # Find relationship patterns in source
        source_patterns = {}
        for node in source_nodes:
            patterns = []
            for rel in self.relationships:
                if rel.from_node_id == node.node_id:
                    patterns.append(('out', rel.relationship_type))
                elif rel.to_node_id == node.node_id:
                    patterns.append(('in', rel.relationship_type))
            if patterns:
                source_patterns[node.node_id] = patterns

        # Find matching patterns in target
        for t_node in target_nodes:
            t_patterns = []
            for rel in self.relationships:
                if rel.from_node_id == t_node.node_id:
                    t_patterns.append(('out', rel.relationship_type))
                elif rel.to_node_id == t_node.node_id:
                    t_patterns.append(('in', rel.relationship_type))

            # Compare with source patterns
            for s_node_id, s_patterns in source_patterns.items():
                if s_node_id in self.nodes:
                    s_node = self.nodes[s_node_id]
                    # Simple pattern matching
                    common = set(s_patterns) & set(t_patterns)
                    if common:
                        similarity = len(common) / max(len(s_patterns), len(t_patterns))
                        if similarity >= 0.3:
                            analogies.append({
                                'source': s_node.concept,
                                'source_domain': source_domain,
                                'target': t_node.concept,
                                'target_domain': target_domain,
                                'similarity': similarity,
                                'common_patterns': [p[1].value for p in common]
                            })

        # Sort by similarity
        analogies.sort(key=lambda a: a['similarity'], reverse=True)
        return analogies[:10]

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics"""
        categories = {}
        for node in self.nodes.values():
            cat = node.category or "uncategorized"
            categories[cat] = categories.get(cat, 0) + 1

        rel_types = {}
        for rel in self.relationships:
            t = rel.relationship_type.value
            rel_types[t] = rel_types.get(t, 0) + 1

        return {
            'total_nodes': len(self.nodes),
            'total_relationships': len(self.relationships),
            'categories': categories,
            'relationship_types': rel_types,
            'avg_understanding': sum(n.understanding_level for n in self.nodes.values()) / max(len(self.nodes), 1)
        }


# Global knowledge reasoner
knowledge_reasoner = KnowledgeReasoner()
