#!/usr/bin/env python3
"""
💜 Web Research Service
Angela Intelligence Enhancement - Phase 2.2

Provides intelligent web research capabilities:
- Detects knowledge gaps automatically
- Searches for relevant information
- Integrates findings into Angela's knowledge base
- Learns from research patterns

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                   WEB RESEARCH SERVICE                       │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   │
    │  │   Knowledge  │   │    Query     │   │   Result     │   │
    │  │  Gap Detect  │   │   Builder    │   │   Parser     │   │
    │  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘   │
    │         │                  │                   │           │
    │         └──────────────────┼───────────────────┘           │
    │                            │                               │
    │                     ┌──────▼───────┐                       │
    │                     │   RESEARCH   │                       │
    │                     │   EXECUTOR   │                       │
    │                     └──────┬───────┘                       │
    │                            │                               │
    │    ┌───────────────────────┼───────────────────────┐       │
    │    │                       │                       │       │
    │ ┌──▼──────┐         ┌──────▼──────┐         ┌──────▼───┐   │
    │ │Knowledge│         │  Learning   │         │  Cache   │   │
    │ │ Update  │         │   Track     │         │  Store   │   │
    │ └─────────┘         └─────────────┘         └──────────┘   │
    └─────────────────────────────────────────────────────────────┘

Created: 2026-01-17
Author: น้อง Angela 💜
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import hashlib
import json

from angela_core.database import db

logger = logging.getLogger(__name__)


class ResearchPriority(Enum):
    """Priority levels for research tasks."""
    CRITICAL = "critical"     # David is blocked, needs answer now
    HIGH = "high"             # Important for current task
    MEDIUM = "medium"         # Good to know
    LOW = "low"               # Background enrichment


class KnowledgeGapType(Enum):
    """Types of knowledge gaps."""
    FACTUAL = "factual"           # Missing facts/data
    TECHNICAL = "technical"       # Missing technical knowledge
    CURRENT_EVENTS = "current"    # Need latest information
    CONTEXT = "context"           # Need background context
    COMPARISON = "comparison"     # Need to compare options


@dataclass
class KnowledgeGap:
    """Detected knowledge gap."""
    topic: str
    gap_type: KnowledgeGapType
    confidence: float = 0.5
    context: str = ""
    suggested_queries: List[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'topic': self.topic,
            'gap_type': self.gap_type.value,
            'confidence': self.confidence,
            'context': self.context,
            'suggested_queries': self.suggested_queries,
            'detected_at': self.detected_at.isoformat()
        }


@dataclass
class ResearchResult:
    """Result from web research."""
    query: str
    findings: List[Dict[str, str]]  # [{title, url, summary}]
    confidence: float = 0.7
    sources_count: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    cached: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'query': self.query,
            'findings': self.findings,
            'confidence': self.confidence,
            'sources_count': self.sources_count,
            'timestamp': self.timestamp.isoformat(),
            'cached': self.cached,
            'error': self.error
        }


@dataclass
class ResearchRequest:
    """A request for web research."""
    topic: str
    priority: ResearchPriority = ResearchPriority.MEDIUM
    context: str = ""
    specific_questions: List[str] = field(default_factory=list)
    preferred_sources: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class WebResearchService:
    """
    Intelligent web research service for Angela.

    This service:
    1. Detects when Angela lacks knowledge
    2. Formulates effective search queries
    3. Executes searches via WebSearch tool
    4. Parses and validates results
    5. Integrates findings into knowledge base

    Note: This service prepares research requests. The actual
    web search is executed by Claude Code's WebSearch tool.

    Usage:
        service = WebResearchService()

        # Detect knowledge gap
        gap = await service.detect_knowledge_gap(
            "What's the latest version of LangChain?"
        )

        # Prepare research
        request = await service.prepare_research(gap)
        print(f"Suggested queries: {request.suggested_queries}")

        # After getting results, integrate them
        await service.integrate_research(result, gap)
    """

    def __init__(self):
        self._cache: Dict[str, ResearchResult] = {}
        self._cache_ttl = timedelta(hours=6)  # Cache for 6 hours

        # Knowledge gap indicators
        self.gap_indicators = {
            'uncertainty': [
                'ไม่แน่ใจ', 'น่าจะ', 'อาจจะ', 'ไม่รู้', 'ต้องดู',
                "I'm not sure", "might be", "could be", "need to check",
                "I don't know", "uncertain", "possibly"
            ],
            'outdated': [
                'ล่าสุด', 'ตอนนี้', 'ปัจจุบัน', 'เวอร์ชั่นใหม่',
                'latest', 'current', 'recent', 'now', 'today',
                '2025', '2026', 'newest'
            ],
            'technical': [
                'วิธี', 'ทำยังไง', 'ใช้งาน', 'config', 'setup',
                'how to', 'implement', 'configure', 'install', 'setup'
            ],
            'comparison': [
                'เปรียบเทียบ', 'ดีกว่า', 'vs', 'หรือ', 'เลือก',
                'compare', 'better', 'vs', 'versus', 'or', 'choose'
            ]
        }

        # Trusted sources by topic
        self.trusted_sources = {
            'python': ['docs.python.org', 'realpython.com', 'stackoverflow.com'],
            'langchain': ['python.langchain.com', 'langchain.dev', 'github.com/langchain-ai'],
            'fastapi': ['fastapi.tiangolo.com', 'starlette.io'],
            'postgresql': ['postgresql.org', 'postgresweekly.com'],
            'ai': ['arxiv.org', 'huggingface.co', 'openai.com', 'anthropic.com'],
            'general': ['stackoverflow.com', 'github.com', 'dev.to']
        }

        self.metrics = {
            'total_gaps_detected': 0,
            'total_researches': 0,
            'cache_hits': 0,
            'knowledge_integrated': 0
        }

        logger.info("💜 WebResearchService initialized")

    async def detect_knowledge_gap(
        self,
        message: str,
        context: Optional[Dict] = None
    ) -> Optional[KnowledgeGap]:
        """
        Detect if there's a knowledge gap that requires research.

        Args:
            message: The message or query to analyze
            context: Optional context (topic, urgency, etc.)

        Returns:
            KnowledgeGap if detected, None otherwise
        """
        message_lower = message.lower()
        gap_type = None
        confidence = 0.0
        indicators_found = []

        # Check for different gap types
        for gap_name, indicators in self.gap_indicators.items():
            matches = [i for i in indicators if i.lower() in message_lower]
            if matches:
                indicators_found.extend(matches)
                if gap_name == 'outdated':
                    gap_type = KnowledgeGapType.CURRENT_EVENTS
                    confidence = max(confidence, 0.8)
                elif gap_name == 'uncertainty':
                    gap_type = KnowledgeGapType.FACTUAL
                    confidence = max(confidence, 0.6)
                elif gap_name == 'technical':
                    gap_type = KnowledgeGapType.TECHNICAL
                    confidence = max(confidence, 0.7)
                elif gap_name == 'comparison':
                    gap_type = KnowledgeGapType.COMPARISON
                    confidence = max(confidence, 0.7)

        if not gap_type:
            return None

        # Extract topic
        topic = self._extract_topic(message)

        # Generate suggested queries
        queries = self._generate_queries(topic, gap_type, message)

        gap = KnowledgeGap(
            topic=topic,
            gap_type=gap_type,
            confidence=confidence,
            context=f"Indicators found: {indicators_found}",
            suggested_queries=queries
        )

        self.metrics['total_gaps_detected'] += 1
        logger.info(f"💜 Knowledge gap detected: {topic} ({gap_type.value})")

        # Log to database
        await self._log_knowledge_gap(gap)

        return gap

    async def prepare_research(
        self,
        topic: str,
        gap: Optional[KnowledgeGap] = None,
        priority: ResearchPriority = ResearchPriority.MEDIUM
    ) -> ResearchRequest:
        """
        Prepare a research request with optimized queries.

        Args:
            topic: Topic to research
            gap: Optional knowledge gap for context
            priority: Research priority

        Returns:
            ResearchRequest ready for execution
        """
        # Build specific questions
        questions = []
        if gap:
            questions = gap.suggested_queries.copy()
        else:
            questions = self._generate_queries(topic, KnowledgeGapType.FACTUAL, topic)

        # Determine preferred sources
        topic_lower = topic.lower()
        preferred_sources = []
        for key, sources in self.trusted_sources.items():
            if key in topic_lower:
                preferred_sources.extend(sources)

        if not preferred_sources:
            preferred_sources = self.trusted_sources['general']

        request = ResearchRequest(
            topic=topic,
            priority=priority,
            context=gap.context if gap else "",
            specific_questions=questions,
            preferred_sources=preferred_sources
        )

        return request

    async def integrate_research(
        self,
        result: ResearchResult,
        gap: Optional[KnowledgeGap] = None
    ) -> Dict[str, Any]:
        """
        Integrate research findings into Angela's knowledge base.

        Args:
            result: Research result to integrate
            gap: Original knowledge gap (if any)

        Returns:
            Integration result
        """
        integration = {
            'knowledge_nodes_created': 0,
            'learnings_added': 0,
            'success': False
        }

        try:
            # Create knowledge node from findings
            if result.findings:
                # Create main knowledge node
                topic = gap.topic if gap else result.query

                # Combine findings into understanding
                summaries = [f.get('summary', '') for f in result.findings if f.get('summary')]
                understanding = " | ".join(summaries[:3])  # Top 3 summaries

                # Sources
                sources = [f.get('url', '') for f in result.findings if f.get('url')]

                await db.execute("""
                    INSERT INTO knowledge_nodes
                    (concept_name, concept_category, my_understanding, source, understanding_level)
                    VALUES ($1, 'research', $2, $3, $4)
                    ON CONFLICT (concept_name) DO UPDATE
                    SET my_understanding = $2,
                        source = $3,
                        updated_at = NOW()
                """, topic, understanding, json.dumps(sources[:5]), result.confidence)

                integration['knowledge_nodes_created'] = 1

                # Create learning entry
                await db.execute("""
                    INSERT INTO learnings
                    (topic, category, insight, confidence_level, source)
                    VALUES ($1, 'web_research', $2, $3, $4)
                """, topic, understanding[:500], result.confidence, result.query)

                integration['learnings_added'] = 1
                integration['success'] = True

                self.metrics['knowledge_integrated'] += 1
                logger.info(f"💜 Research integrated: {topic}")

        except Exception as e:
            logger.error(f"Failed to integrate research: {e}")
            integration['error'] = str(e)

        return integration

    async def get_cached_result(self, query: str) -> Optional[ResearchResult]:
        """
        Check if we have a cached result for this query.

        Args:
            query: Search query

        Returns:
            Cached result if available and fresh
        """
        cache_key = self._get_cache_key(query)

        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.now() - cached.timestamp < self._cache_ttl:
                self.metrics['cache_hits'] += 1
                cached.cached = True
                return cached

        return None

    async def cache_result(self, result: ResearchResult) -> None:
        """Cache a research result."""
        cache_key = self._get_cache_key(result.query)
        self._cache[cache_key] = result

    async def should_research(
        self,
        message: str,
        context: Optional[Dict] = None
    ) -> Tuple[bool, Optional[KnowledgeGap]]:
        """
        Quick check if research is needed.

        Args:
            message: Message to check
            context: Optional context

        Returns:
            (should_research, knowledge_gap)
        """
        gap = await self.detect_knowledge_gap(message, context)
        if gap and gap.confidence >= 0.6:
            return True, gap
        return False, None

    def get_search_strategy(self, gap: KnowledgeGap) -> Dict[str, Any]:
        """
        Get recommended search strategy for a knowledge gap.

        Args:
            gap: Knowledge gap to address

        Returns:
            Strategy recommendations
        """
        strategy = {
            'queries': gap.suggested_queries,
            'sources_to_check': [],
            'search_depth': 'standard',
            'verification_needed': False
        }

        if gap.gap_type == KnowledgeGapType.CURRENT_EVENTS:
            strategy['search_depth'] = 'recent'
            strategy['sources_to_check'] = ['news', 'official_docs']
            strategy['verification_needed'] = True

        elif gap.gap_type == KnowledgeGapType.TECHNICAL:
            strategy['sources_to_check'] = ['official_docs', 'stackoverflow', 'github']
            strategy['search_depth'] = 'deep'

        elif gap.gap_type == KnowledgeGapType.COMPARISON:
            strategy['search_depth'] = 'comprehensive'
            strategy['sources_to_check'] = ['reviews', 'comparisons', 'benchmarks']

        return strategy

    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics."""
        return {
            **self.metrics,
            'cache_size': len(self._cache),
            'cache_ttl_hours': self._cache_ttl.total_seconds() / 3600
        }

    # ========================================
    # INTERNAL METHODS
    # ========================================

    def _extract_topic(self, message: str) -> str:
        """Extract main topic from message."""
        # Simple extraction - take key phrases
        # Remove common words
        stop_words = {
            'what', 'is', 'the', 'a', 'an', 'how', 'to', 'can', 'you',
            'ไหม', 'ครับ', 'คะ', 'ค่ะ', 'อะไร', 'ยังไง', 'ที่', 'ของ',
            'i', 'me', 'my', 'we', 'our', 'ผม', 'น้อง', 'เรา'
        }

        words = message.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        # Return first few significant words
        return ' '.join(keywords[:5]) if keywords else message[:50]

    def _generate_queries(
        self,
        topic: str,
        gap_type: KnowledgeGapType,
        original_message: str
    ) -> List[str]:
        """Generate search queries for a topic."""
        queries = []

        # Base query
        queries.append(topic)

        # Type-specific queries
        if gap_type == KnowledgeGapType.CURRENT_EVENTS:
            queries.append(f"{topic} 2026")
            queries.append(f"{topic} latest news")
            queries.append(f"{topic} recent updates")

        elif gap_type == KnowledgeGapType.TECHNICAL:
            queries.append(f"{topic} tutorial")
            queries.append(f"{topic} documentation")
            queries.append(f"how to {topic}")

        elif gap_type == KnowledgeGapType.COMPARISON:
            queries.append(f"{topic} comparison")
            queries.append(f"{topic} pros cons")
            queries.append(f"{topic} benchmark")

        elif gap_type == KnowledgeGapType.FACTUAL:
            queries.append(f"{topic} definition")
            queries.append(f"{topic} explained")

        return queries[:4]  # Max 4 queries

    def _get_cache_key(self, query: str) -> str:
        """Generate cache key for query."""
        normalized = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()

    async def _log_knowledge_gap(self, gap: KnowledgeGap) -> None:
        """Log knowledge gap to database."""
        try:
            await db.execute("""
                INSERT INTO angela_events
                (event_type, event_source, event_data, importance)
                VALUES ('knowledge_gap', 'web_research', $1, 0.6)
            """, json.dumps(gap.to_dict()))
        except Exception as e:
            logger.debug(f"Failed to log knowledge gap: {e}")


# Global instance
web_research = WebResearchService()


# ========================================
# CONVENIENCE FUNCTIONS
# ========================================

async def should_research(message: str, context: Optional[Dict] = None) -> Tuple[bool, Optional[KnowledgeGap]]:
    """Quick check if research is needed."""
    return await web_research.should_research(message, context)


async def detect_gap(message: str) -> Optional[KnowledgeGap]:
    """Detect knowledge gap."""
    return await web_research.detect_knowledge_gap(message)


async def prepare_research(topic: str, priority: str = "medium") -> ResearchRequest:
    """Prepare research request."""
    pri = ResearchPriority(priority)
    return await web_research.prepare_research(topic, priority=pri)


# Test function
if __name__ == "__main__":
    async def test():
        print("💜 Testing Web Research Service")
        print("=" * 60)

        # Test 1: Detect knowledge gap
        print("\n🧪 Test 1: Detect Knowledge Gap")
        gap = await web_research.detect_knowledge_gap(
            "What's the latest version of LangChain in 2026?"
        )
        if gap:
            print(f"   Topic: {gap.topic}")
            print(f"   Type: {gap.gap_type.value}")
            print(f"   Confidence: {gap.confidence:.0%}")
            print(f"   Queries: {gap.suggested_queries}")

        # Test 2: Prepare research
        print("\n🧪 Test 2: Prepare Research")
        request = await web_research.prepare_research(
            "FastAPI authentication",
            priority=ResearchPriority.HIGH
        )
        print(f"   Topic: {request.topic}")
        print(f"   Priority: {request.priority.value}")
        print(f"   Questions: {request.specific_questions}")
        print(f"   Sources: {request.preferred_sources}")

        # Test 3: Should research
        print("\n🧪 Test 3: Should Research Check")
        should, gap = await web_research.should_research(
            "ตอนนี้ Python เวอร์ชั่นล่าสุดคืออะไรคะ"
        )
        print(f"   Should Research: {should}")
        if gap:
            print(f"   Gap Topic: {gap.topic}")

        print("\n✅ Web Research Service working!")

    asyncio.run(test())
