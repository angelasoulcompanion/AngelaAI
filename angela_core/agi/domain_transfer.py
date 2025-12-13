"""
Domain Transfer - Cross-domain knowledge transfer for Angela AGI

This module enables Angela to:
- Transfer knowledge between domains
- Find analogies across different fields
- Apply patterns from one context to another
- Build abstract understanding that generalizes
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum


class TransferType(Enum):
    """Types of knowledge transfer"""
    ANALOGY = "analogy"           # Similar situations
    ABSTRACTION = "abstraction"   # General principles
    PATTERN = "pattern"           # Recurring patterns
    METHOD = "method"             # Transferable methods


@dataclass
class DomainConcept:
    """A concept within a domain"""
    concept_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    domain: str = ""
    description: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    relationships: List[str] = field(default_factory=list)  # relationship types
    abstraction_level: int = 0  # 0=concrete, 5=very abstract
    embedding: Optional[List[float]] = None


@dataclass
class TransferMapping:
    """A mapping between concepts in different domains"""
    mapping_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_concept: DomainConcept = field(default_factory=DomainConcept)
    target_concept: DomainConcept = field(default_factory=DomainConcept)
    transfer_type: TransferType = TransferType.ANALOGY
    similarity_score: float = 0.5
    reasoning: str = ""
    validated: bool = False
    success_score: Optional[float] = None


@dataclass
class AbstractPrinciple:
    """A domain-independent principle"""
    principle_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    source_domains: List[str] = field(default_factory=list)
    applicable_domains: List[str] = field(default_factory=list)
    confidence: float = 0.5
    examples: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TransferResult:
    """Result of a knowledge transfer attempt"""
    transfer_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_domain: str = ""
    target_domain: str = ""
    mappings: List[TransferMapping] = field(default_factory=list)
    principles_used: List[str] = field(default_factory=list)
    success_score: float = 0.5
    insights: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class DomainTransferEngine:
    """
    Enables knowledge transfer across domains.

    Capabilities:
    - Find analogies between different domains
    - Abstract patterns to general principles
    - Apply methods from one domain to another
    - Learn from successful transfers

    Usage:
        engine = DomainTransferEngine(db, knowledge_reasoner)
        result = await engine.transfer_knowledge("cooking", "software", "debugging")
        principles = await engine.extract_principles("project_management")
    """

    def __init__(self, db=None, knowledge_reasoner=None):
        self.db = db
        self.reasoner = knowledge_reasoner
        self.principles: Dict[str, AbstractPrinciple] = {}
        self.transfer_history: List[TransferResult] = []

        # Initialize with fundamental principles
        self._initialize_principles()

    def _initialize_principles(self):
        """Initialize with domain-independent principles"""
        base_principles = [
            AbstractPrinciple(
                name="divide_and_conquer",
                description="Break complex problems into smaller, manageable parts",
                source_domains=["mathematics", "computer_science", "military"],
                applicable_domains=["any"],
                confidence=0.95,
                examples=[
                    {"domain": "coding", "example": "Break large function into smaller ones"},
                    {"domain": "cooking", "example": "Prepare ingredients separately before combining"},
                    {"domain": "project", "example": "Split into phases and milestones"}
                ]
            ),
            AbstractPrinciple(
                name="feedback_loop",
                description="Use output to adjust input for continuous improvement",
                source_domains=["control_theory", "biology"],
                applicable_domains=["any"],
                confidence=0.90,
                examples=[
                    {"domain": "coding", "example": "TDD - write test, code, refactor, repeat"},
                    {"domain": "learning", "example": "Practice, get feedback, adjust"},
                    {"domain": "cooking", "example": "Taste and adjust seasoning"}
                ]
            ),
            AbstractPrinciple(
                name="layered_abstraction",
                description="Build complex systems from simpler layers",
                source_domains=["computer_science", "architecture"],
                applicable_domains=["design", "organization", "communication"],
                confidence=0.88,
                examples=[
                    {"domain": "coding", "example": "OSI model, clean architecture"},
                    {"domain": "organization", "example": "Team → Department → Division"},
                    {"domain": "writing", "example": "Words → Sentences → Paragraphs"}
                ]
            ),
            AbstractPrinciple(
                name="pareto_principle",
                description="80% of effects come from 20% of causes",
                source_domains=["economics", "quality_management"],
                applicable_domains=["any"],
                confidence=0.85,
                examples=[
                    {"domain": "coding", "example": "Focus on the 20% of code causing 80% of bugs"},
                    {"domain": "time_management", "example": "Focus on high-impact tasks"},
                    {"domain": "learning", "example": "Learn core concepts first"}
                ]
            ),
            AbstractPrinciple(
                name="single_responsibility",
                description="Each component should do one thing well",
                source_domains=["software_engineering"],
                applicable_domains=["design", "organization", "process"],
                confidence=0.87,
                examples=[
                    {"domain": "coding", "example": "SRP in SOLID principles"},
                    {"domain": "cooking", "example": "Each tool for specific purpose"},
                    {"domain": "team", "example": "Clear role definitions"}
                ]
            ),
            AbstractPrinciple(
                name="progressive_disclosure",
                description="Reveal complexity gradually as needed",
                source_domains=["ux_design", "education"],
                applicable_domains=["design", "communication", "teaching"],
                confidence=0.82,
                examples=[
                    {"domain": "ui", "example": "Advanced settings hidden by default"},
                    {"domain": "teaching", "example": "Start simple, add complexity"},
                    {"domain": "documentation", "example": "Quick start → detailed guide"}
                ]
            ),
        ]

        for principle in base_principles:
            self.principles[principle.principle_id] = principle

    async def find_analogies(
        self,
        source_domain: str,
        target_domain: str,
        concept: str
    ) -> List[TransferMapping]:
        """
        Find analogous concepts between domains.

        Example: "debugging" in coding → "diagnosis" in medicine
        """
        mappings = []

        # Get source domain concepts from knowledge graph
        if self.reasoner:
            source_concepts = await self.reasoner.get_domain_concepts(source_domain)
            target_concepts = await self.reasoner.get_domain_concepts(target_domain)

            # Find concept in source
            source_match = None
            for sc in source_concepts:
                if concept.lower() in sc.concept.lower():
                    source_match = DomainConcept(
                        concept_id=sc.node_id,
                        name=sc.concept,
                        domain=source_domain,
                        description=sc.description,
                        abstraction_level=2
                    )
                    break

            if source_match and target_concepts:
                # Find analogies using knowledge graph
                analogies = await self.reasoner.find_analogies(source_domain, target_domain)

                for analogy in analogies[:5]:
                    target_concept = DomainConcept(
                        name=analogy['target'],
                        domain=target_domain,
                        abstraction_level=2
                    )

                    mapping = TransferMapping(
                        source_concept=source_match,
                        target_concept=target_concept,
                        transfer_type=TransferType.ANALOGY,
                        similarity_score=analogy['similarity'],
                        reasoning=f"Similar relationship patterns: {', '.join(analogy['common_patterns'])}"
                    )
                    mappings.append(mapping)

        # Also use predefined analogies for common cases
        predefined = self._get_predefined_analogies(source_domain, target_domain, concept)
        mappings.extend(predefined)

        # Sort by similarity
        mappings.sort(key=lambda m: m.similarity_score, reverse=True)
        return mappings[:10]

    def _get_predefined_analogies(
        self,
        source_domain: str,
        target_domain: str,
        concept: str
    ) -> List[TransferMapping]:
        """Get predefined domain analogies"""
        analogies_db = {
            ("coding", "cooking"): {
                "debugging": ("adjusting seasoning", 0.7, "Both involve iterative testing and refinement"),
                "refactoring": ("mise en place", 0.6, "Both involve reorganizing for efficiency"),
                "testing": ("tasting", 0.8, "Both validate quality before serving"),
                "deployment": ("plating", 0.5, "Both present the final result"),
            },
            ("coding", "medicine"): {
                "debugging": ("diagnosis", 0.85, "Both identify root cause of symptoms"),
                "testing": ("preventive checkup", 0.7, "Both catch problems early"),
                "refactoring": ("rehabilitation", 0.5, "Both improve without changing function"),
            },
            ("coding", "construction"): {
                "architecture": ("blueprint", 0.9, "Both plan before building"),
                "refactoring": ("renovation", 0.75, "Both improve existing structure"),
                "testing": ("inspection", 0.8, "Both verify quality and safety"),
            },
            ("project_management", "cooking"): {
                "sprint": ("meal prep", 0.65, "Both have time-boxed execution"),
                "backlog": ("recipe collection", 0.6, "Both store future work items"),
                "retrospective": ("tasting notes", 0.5, "Both review for improvement"),
            },
        }

        key = (source_domain, target_domain)
        reverse_key = (target_domain, source_domain)

        mappings = []

        if key in analogies_db and concept.lower() in analogies_db[key]:
            target, score, reasoning = analogies_db[key][concept.lower()]
            mapping = TransferMapping(
                source_concept=DomainConcept(name=concept, domain=source_domain),
                target_concept=DomainConcept(name=target, domain=target_domain),
                transfer_type=TransferType.ANALOGY,
                similarity_score=score,
                reasoning=reasoning
            )
            mappings.append(mapping)

        elif reverse_key in analogies_db:
            for src, (tgt, score, reasoning) in analogies_db[reverse_key].items():
                if tgt.lower() == concept.lower():
                    mapping = TransferMapping(
                        source_concept=DomainConcept(name=src, domain=target_domain),
                        target_concept=DomainConcept(name=concept, domain=source_domain),
                        transfer_type=TransferType.ANALOGY,
                        similarity_score=score,
                        reasoning=reasoning
                    )
                    mappings.append(mapping)

        return mappings

    async def transfer_knowledge(
        self,
        source_domain: str,
        target_domain: str,
        problem: str
    ) -> TransferResult:
        """
        Transfer knowledge from source domain to solve problem in target domain.

        Returns applicable patterns, methods, and insights.
        """
        result = TransferResult(
            source_domain=source_domain,
            target_domain=target_domain
        )

        # 1. Find applicable principles
        applicable_principles = await self.find_applicable_principles(
            problem,
            [source_domain, target_domain]
        )
        result.principles_used = [p.principle_id for p in applicable_principles]

        # 2. Find analogies
        words = problem.lower().split()
        for word in words:
            if len(word) > 3:  # Skip short words
                analogies = await self.find_analogies(source_domain, target_domain, word)
                for analogy in analogies[:2]:  # Top 2 per word
                    if analogy not in result.mappings:
                        result.mappings.append(analogy)

        # 3. Generate insights
        insights = []

        for principle in applicable_principles:
            insight = f"Apply '{principle.name}': {principle.description}"
            for ex in principle.examples:
                if ex['domain'] == target_domain or ex['domain'] in [source_domain, 'any']:
                    insight += f" (e.g., {ex['example']})"
                    break
            insights.append(insight)

        for mapping in result.mappings[:3]:
            insight = f"Think of '{mapping.source_concept.name}' ({source_domain}) as '{mapping.target_concept.name}' ({target_domain}): {mapping.reasoning}"
            insights.append(insight)

        result.insights = insights

        # 4. Calculate success score based on number of applicable transfers
        if result.mappings or result.principles_used:
            result.success_score = min(0.5 + len(result.mappings) * 0.1 + len(result.principles_used) * 0.1, 1.0)
        else:
            result.success_score = 0.3

        # Save to history
        self.transfer_history.append(result)

        if self.db:
            await self._save_transfer_result(result)

        return result

    async def find_applicable_principles(
        self,
        problem: str,
        domains: List[str]
    ) -> List[AbstractPrinciple]:
        """Find principles applicable to a problem"""
        applicable = []
        problem_lower = problem.lower()

        for principle in self.principles.values():
            # Check if principle applies to these domains
            domain_match = 'any' in principle.applicable_domains or any(
                d in principle.applicable_domains for d in domains
            )

            if not domain_match:
                continue

            # Check for keyword matches in problem
            keywords = {
                "divide_and_conquer": ["complex", "large", "break", "split", "parts"],
                "feedback_loop": ["improve", "iterate", "adjust", "feedback", "loop"],
                "layered_abstraction": ["layer", "abstract", "organize", "structure"],
                "pareto_principle": ["priority", "important", "focus", "impact"],
                "single_responsibility": ["responsibility", "single", "one thing", "focused"],
                "progressive_disclosure": ["gradual", "step", "complex", "simple"],
            }

            if principle.name in keywords:
                if any(kw in problem_lower for kw in keywords[principle.name]):
                    applicable.append(principle)
                    continue

            # Default: add high-confidence principles
            if principle.confidence >= 0.9:
                applicable.append(principle)

        return applicable

    async def extract_principles(
        self,
        domain: str,
        experiences: List[Dict[str, Any]] = None
    ) -> List[AbstractPrinciple]:
        """
        Extract abstract principles from domain experiences.

        Analyzes patterns in experiences to create generalizable principles.
        """
        if not experiences:
            experiences = []

        new_principles = []

        # Analyze patterns in experiences
        patterns = {}
        for exp in experiences:
            if 'pattern' in exp:
                pattern = exp['pattern']
                if pattern not in patterns:
                    patterns[pattern] = []
                patterns[pattern].append(exp)

        # Create principles from frequently occurring patterns
        for pattern, instances in patterns.items():
            if len(instances) >= 2:  # Need at least 2 instances
                principle = AbstractPrinciple(
                    name=pattern.replace(" ", "_").lower(),
                    description=f"Pattern observed in {domain}: {pattern}",
                    source_domains=[domain],
                    applicable_domains=[domain, "similar"],
                    confidence=min(0.5 + len(instances) * 0.1, 0.9),
                    examples=[
                        {"domain": domain, "example": inst.get('description', '')}
                        for inst in instances[:3]
                    ]
                )
                new_principles.append(principle)
                self.principles[principle.principle_id] = principle

        return new_principles

    async def apply_principle(
        self,
        principle_id: str,
        target_domain: str,
        context: str
    ) -> Dict[str, Any]:
        """Apply a principle to a new domain"""
        if principle_id not in self.principles:
            return {"error": "Principle not found"}

        principle = self.principles[principle_id]

        # Generate application suggestions
        suggestions = []

        # Find relevant examples
        for example in principle.examples:
            if example['domain'] == target_domain:
                suggestions.append(f"Direct example: {example['example']}")

        # Generate new suggestions based on principle
        suggestions.append(f"Core approach: {principle.description}")

        # Add general guidance
        if principle.confidence >= 0.9:
            suggestions.append(f"High confidence ({principle.confidence:.0%}): This principle is well-established")
        else:
            suggestions.append(f"Moderate confidence ({principle.confidence:.0%}): Validate this approach")

        return {
            "principle": principle.name,
            "description": principle.description,
            "target_domain": target_domain,
            "context": context,
            "suggestions": suggestions,
            "source_domains": principle.source_domains
        }

    async def validate_transfer(
        self,
        transfer_id: str,
        success: bool,
        feedback: str = ""
    ) -> None:
        """Record validation of a transfer attempt"""
        for transfer in self.transfer_history:
            if transfer.transfer_id == transfer_id:
                if success:
                    transfer.success_score = min(transfer.success_score + 0.1, 1.0)
                else:
                    transfer.success_score = max(transfer.success_score - 0.1, 0.0)

                # Update principle confidence
                for pid in transfer.principles_used:
                    if pid in self.principles:
                        p = self.principles[pid]
                        alpha = 0.1
                        if success:
                            p.confidence = min(p.confidence + alpha * (1 - p.confidence), 0.99)
                        else:
                            p.confidence = max(p.confidence - alpha * p.confidence, 0.1)

                break

    def get_stats(self) -> Dict[str, Any]:
        """Get transfer engine statistics"""
        successful = sum(1 for t in self.transfer_history if t.success_score >= 0.7)
        total = len(self.transfer_history)

        # Domain usage
        domains = {}
        for transfer in self.transfer_history:
            for d in [transfer.source_domain, transfer.target_domain]:
                domains[d] = domains.get(d, 0) + 1

        # Top principles
        principle_usage = {}
        for transfer in self.transfer_history:
            for pid in transfer.principles_used:
                if pid in self.principles:
                    name = self.principles[pid].name
                    principle_usage[name] = principle_usage.get(name, 0) + 1

        return {
            "total_transfers": total,
            "successful_transfers": successful,
            "success_rate": successful / total if total > 0 else 0,
            "total_principles": len(self.principles),
            "domain_coverage": len(domains),
            "top_domains": sorted(domains.items(), key=lambda x: x[1], reverse=True)[:5],
            "most_used_principles": sorted(principle_usage.items(), key=lambda x: x[1], reverse=True)[:5]
        }

    # Database operations
    async def _save_transfer_result(self, result: TransferResult) -> None:
        """Save transfer result to database"""
        if not self.db:
            return
        try:
            await self.db.execute("""
                INSERT INTO domain_transfers (
                    transfer_id, source_domain, target_domain,
                    transfer_type, similarity_score, success_score,
                    description, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
                result.transfer_id,
                result.source_domain,
                result.target_domain,
                'analogy',  # Default type
                result.mappings[0].similarity_score if result.mappings else 0.5,
                result.success_score,
                "; ".join(result.insights[:2]),
                result.created_at
            )
        except Exception as e:
            print(f"Warning: Failed to save transfer result: {e}")


# Global domain transfer engine
domain_transfer = DomainTransferEngine()
