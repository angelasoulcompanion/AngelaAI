#!/usr/bin/env python3
"""
🧠 Knowledge Synthesis Engine
Combines insights from multiple sources to create comprehensive understanding

Capabilities:
- Connect related concepts across conversations
- Resolve contradictions in learned information
- Generate meta-knowledge (understanding patterns of understanding)
- Build knowledge networks
- Create higher-level abstractions
- Synthesize comprehensive profiles

Created: 2025-01-26
Author: น้อง Angela
"""

import logging
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict

from angela_core.services.deep_analysis_engine import DeepAnalysisResult
from angela_core.services.pattern_recognition_engine import PatternRecognitionResult

logger = logging.getLogger(__name__)


# ========================================
# Data Structures
# ========================================

@dataclass
class ConceptConnection:
    """Connection between two concepts"""
    concept_a: str
    concept_b: str
    connection_type: str  # related, causes, requires, contradicts
    strength: float  # 0.0-1.0
    evidence_count: int
    examples: List[str]


@dataclass
class KnowledgeContradiction:
    """Detected contradiction in knowledge"""
    topic: str
    statement_a: str
    statement_b: str
    source_a: str
    source_b: str
    contradiction_type: str  # factual, preference, temporal
    resolution: Optional[str] = None


@dataclass
class MetaKnowledge:
    """Knowledge about knowledge - higher level understanding"""
    insight_type: str  # learning_pattern, preference_shift, growth_area
    description: str
    confidence: float
    supporting_evidence: List[str]
    implications: List[str]


@dataclass
class UserProfile:
    """Comprehensive user profile synthesized from all knowledge"""
    # Core characteristics
    primary_communication_style: str
    emotional_baseline: str  # Generally positive, neutral, variable
    intimacy_level: str  # high, medium, low
    engagement_pattern: str  # highly_engaged, moderately_engaged, variable

    # Preferences
    favorite_topics: List[str]
    preferred_times: List[str]  # Times of day most active
    preferred_session_types: List[str]

    # Patterns
    behavioral_tendencies: List[str]
    emotional_tendencies: List[str]

    # Growth
    knowledge_areas: List[str]  # Areas where user has expertise
    learning_interests: List[str]  # Topics user wants to learn

    # Relationship
    relationship_stage: str  # building, established, deep
    communication_frequency: float  # Messages per day
    relationship_quality_score: float  # 0.0-1.0

    # Meta
    profile_confidence: float  # 0.0-1.0
    last_updated: datetime


@dataclass
class SynthesisResult:
    """Complete knowledge synthesis result"""
    concept_connections: List[ConceptConnection]
    contradictions: List[KnowledgeContradiction]
    meta_knowledge: List[MetaKnowledge]
    user_profile: UserProfile
    synthesis_timestamp: datetime
    sources_synthesized: int


# ========================================
# Knowledge Synthesis Engine
# ========================================

class KnowledgeSynthesisEngine:
    """
    Synthesizes knowledge from multiple sources into comprehensive understanding

    น้องจะรวมทุกสิ่งที่เรียนรู้มา สร้างเป็นความเข้าใจที่ลึกซึ้งและสมบูรณ์ 💜
    """

    def __init__(self):
        # Knowledge graph
        self.concept_graph: Dict[str, Set[str]] = defaultdict(set)
        self.concept_connections: Dict[Tuple[str, str], ConceptConnection] = {}

        # Contradiction tracking
        self.detected_contradictions: List[KnowledgeContradiction] = []

        # Meta knowledge
        self.meta_insights: List[MetaKnowledge] = []

        # User profile (cumulative)
        self.user_profile: Optional[UserProfile] = None

        logger.info("🧠 Knowledge Synthesis Engine initialized")


    async def synthesize_knowledge(
        self,
        deep_analyses: List[Dict],  # List of analysis data from conversations
        pattern_result: Optional[PatternRecognitionResult] = None
    ) -> SynthesisResult:
        """
        Synthesize knowledge from multiple sources

        Args:
            deep_analyses: List of conversation analysis results
            pattern_result: Optional pattern recognition results

        Returns:
            Complete synthesis result
        """
        if not deep_analyses:
            logger.warning("No analyses to synthesize")
            return self._empty_result()

        # 1. Build concept connections
        concept_connections = self._build_concept_connections(deep_analyses)

        # 2. Detect contradictions
        contradictions = self._detect_contradictions(deep_analyses)

        # 3. Generate meta-knowledge
        meta_knowledge = self._generate_meta_knowledge(
            deep_analyses,
            pattern_result
        )

        # 4. Build/update user profile
        user_profile = self._synthesize_user_profile(
            deep_analyses,
            pattern_result,
            meta_knowledge
        )

        self.user_profile = user_profile

        return SynthesisResult(
            concept_connections=concept_connections,
            contradictions=contradictions,
            meta_knowledge=meta_knowledge,
            user_profile=user_profile,
            synthesis_timestamp=datetime.now(),
            sources_synthesized=len(deep_analyses)
        )


    def _build_concept_connections(
        self,
        analyses: List[Dict]
    ) -> List[ConceptConnection]:
        """Build connections between related concepts"""
        connections = []

        # Track co-occurrence of topics
        topic_pairs = defaultdict(lambda: {"count": 0, "examples": []})

        for analysis in analyses:
            topics = analysis.get("topics", [])

            # For each pair of topics that appear together
            for i, topic_a in enumerate(topics):
                for topic_b in topics[i+1:]:
                    # Create canonical pair (sorted)
                    pair = tuple(sorted([topic_a, topic_b]))
                    topic_pairs[pair]["count"] += 1

                    # Store example
                    msg = analysis.get("david_message", "")
                    if len(topic_pairs[pair]["examples"]) < 3:
                        topic_pairs[pair]["examples"].append(msg[:50])

        # Create connections for frequently co-occurring topics
        for (topic_a, topic_b), data in topic_pairs.items():
            if data["count"] >= 2:  # Appeared together at least twice
                strength = min(data["count"] / len(analyses), 1.0)

                connection = ConceptConnection(
                    concept_a=topic_a,
                    concept_b=topic_b,
                    connection_type="related",
                    strength=strength,
                    evidence_count=data["count"],
                    examples=data["examples"]
                )
                connections.append(connection)

                # Update graph
                self.concept_graph[topic_a].add(topic_b)
                self.concept_graph[topic_b].add(topic_a)
                self.concept_connections[(topic_a, topic_b)] = connection

        # Sort by strength
        connections.sort(key=lambda x: x.strength, reverse=True)
        return connections


    def _detect_contradictions(
        self,
        analyses: List[Dict]
    ) -> List[KnowledgeContradiction]:
        """Detect contradictions in statements or preferences"""
        contradictions = []

        # Group by topics
        topic_sentiments = defaultdict(list)

        for i, analysis in enumerate(analyses):
            topics = analysis.get("topics", [])
            sentiment = analysis.get("sentiment", "neutral")
            sentiment_score = analysis.get("sentiment_score", 0)

            for topic in topics:
                topic_sentiments[topic].append({
                    "index": i,
                    "sentiment": sentiment,
                    "score": sentiment_score,
                    "message": analysis.get("david_message", "")
                })

        # Look for contradictory sentiments on same topic
        for topic, sentiments in topic_sentiments.items():
            if len(sentiments) < 2:
                continue

            # Check for opposite sentiments
            positive_instances = [s for s in sentiments if s["score"] > 0.3]
            negative_instances = [s for s in sentiments if s["score"] < -0.3]

            if positive_instances and negative_instances:
                # Found contradiction
                contradiction = KnowledgeContradiction(
                    topic=topic,
                    statement_a=positive_instances[0]["message"][:100],
                    statement_b=negative_instances[0]["message"][:100],
                    source_a=f"conversation_{positive_instances[0]['index']}",
                    source_b=f"conversation_{negative_instances[0]['index']}",
                    contradiction_type="preference",
                    resolution=f"User has mixed feelings about {topic} - context-dependent"
                )
                contradictions.append(contradiction)

        self.detected_contradictions.extend(contradictions)
        return contradictions


    def _generate_meta_knowledge(
        self,
        analyses: List[Dict],
        pattern_result: Optional[PatternRecognitionResult]
    ) -> List[MetaKnowledge]:
        """Generate meta-knowledge - insights about the learning process itself"""
        meta_insights = []

        # 1. Learning pattern insight
        if len(analyses) >= 5:
            # Analyze how topics evolve
            early_topics = set()
            late_topics = set()

            mid_point = len(analyses) // 2
            for analysis in analyses[:mid_point]:
                early_topics.update(analysis.get("topics", []))
            for analysis in analyses[mid_point:]:
                late_topics.update(analysis.get("topics", []))

            new_topics = late_topics - early_topics
            if new_topics:
                insight = MetaKnowledge(
                    insight_type="learning_pattern",
                    description=f"User is exploring new topics: {', '.join(list(new_topics)[:3])}",
                    confidence=0.8,
                    supporting_evidence=[f"{len(new_topics)} new topics appeared in recent conversations"],
                    implications=["User is expanding knowledge areas", "May need support in these new topics"]
                )
                meta_insights.append(insight)

        # 2. Engagement evolution
        if len(analyses) >= 10:
            early_engagement = sum([a.get("engagement_level", 0) for a in analyses[:5]]) / 5
            late_engagement = sum([a.get("engagement_level", 0) for a in analyses[-5:]]) / 5

            engagement_change = late_engagement - early_engagement
            if abs(engagement_change) > 0.2:
                if engagement_change > 0:
                    desc = "User engagement is increasing over time"
                    implications = ["Relationship is strengthening", "Content is becoming more relevant"]
                else:
                    desc = "User engagement is decreasing over time"
                    implications = ["May need to refresh conversation topics", "Check if user needs are being met"]

                insight = MetaKnowledge(
                    insight_type="engagement_shift",
                    description=desc,
                    confidence=0.7,
                    supporting_evidence=[f"Engagement changed from {early_engagement:.2f} to {late_engagement:.2f}"],
                    implications=implications
                )
                meta_insights.append(insight)

        # 3. Emotional intelligence effectiveness
        high_empathy_convs = [a for a in analyses if a.get("empathy_score", 0) > 0.7]
        if high_empathy_convs:
            empathy_ratio = len(high_empathy_convs) / len(analyses)
            insight = MetaKnowledge(
                insight_type="emotional_effectiveness",
                description=f"Maintaining high empathy in {empathy_ratio*100:.0f}% of conversations",
                confidence=0.9,
                supporting_evidence=[f"{len(high_empathy_convs)} conversations with empathy > 0.7"],
                implications=["Emotional responses are effective", "Continue current empathy approach"]
            )
            meta_insights.append(insight)

        # 4. Pattern-based meta-knowledge
        if pattern_result and pattern_result.relationship_evolution:
            evolution = pattern_result.relationship_evolution
            if evolution.intimacy_trend == "increasing":
                insight = MetaKnowledge(
                    insight_type="relationship_growth",
                    description="Relationship intimacy is growing consistently",
                    confidence=0.85,
                    supporting_evidence=[
                        f"Intimacy increased from {evolution.intimacy_start:.2f} to {evolution.intimacy_end:.2f}",
                        f"Communication frequency: {evolution.communication_frequency:.2f} msgs/day"
                    ],
                    implications=[
                        "User trust is increasing",
                        "Continue current approach",
                        "May introduce more personal topics"
                    ]
                )
                meta_insights.append(insight)

        self.meta_insights.extend(meta_insights)
        return meta_insights


    def _synthesize_user_profile(
        self,
        analyses: List[Dict],
        pattern_result: Optional[PatternRecognitionResult],
        meta_knowledge: List[MetaKnowledge]
    ) -> UserProfile:
        """Synthesize comprehensive user profile from all knowledge"""

        # Communication style (most common)
        styles = [a.get("communication_style") for a in analyses]
        style_counts = defaultdict(int)
        for style in styles:
            if style:
                style_counts[style] += 1
        primary_style = max(style_counts.items(), key=lambda x: x[1])[0] if style_counts else "unknown"

        # Emotional baseline
        sentiments = [a.get("sentiment", "neutral") for a in analyses]
        positive_count = sentiments.count("positive")
        negative_count = sentiments.count("negative")

        if positive_count > len(analyses) * 0.6:
            emotional_baseline = "generally_positive"
        elif negative_count > len(analyses) * 0.4:
            emotional_baseline = "variable_with_stress"
        else:
            emotional_baseline = "balanced"

        # Intimacy level (average)
        intimacy_scores = [a.get("intimacy_level", 0) for a in analyses]
        avg_intimacy = sum(intimacy_scores) / len(intimacy_scores) if intimacy_scores else 0

        if avg_intimacy > 0.7:
            intimacy_level = "high"
        elif avg_intimacy > 0.4:
            intimacy_level = "medium"
        else:
            intimacy_level = "low"

        # Engagement pattern
        engagement_scores = [a.get("engagement_level", 0) for a in analyses]
        avg_engagement = sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0
        engagement_variance = max(engagement_scores) - min(engagement_scores) if engagement_scores else 0

        if avg_engagement > 0.7:
            engagement_pattern = "highly_engaged"
        elif engagement_variance > 0.4:
            engagement_pattern = "variable"
        else:
            engagement_pattern = "moderately_engaged"

        # Favorite topics (from pattern analysis or synthesis)
        if pattern_result and pattern_result.topic_affinities:
            favorite_topics = [a.topic for a in pattern_result.topic_affinities[:5]]
        else:
            # Fallback: count topics from analyses
            all_topics = []
            for a in analyses:
                all_topics.extend(a.get("topics", []))
            topic_counts = defaultdict(int)
            for topic in all_topics:
                topic_counts[topic] += 1
            favorite_topics = [t for t, _ in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]]

        # Preferred times
        if pattern_result and pattern_result.temporal_patterns:
            preferred_times = [p.time_context for p in pattern_result.temporal_patterns[:3]]
        else:
            times = [a.get("time_context", "unknown") for a in analyses]
            time_counts = defaultdict(int)
            for time in times:
                if time:
                    time_counts[time] += 1
            preferred_times = [t for t, _ in sorted(time_counts.items(), key=lambda x: x[1], reverse=True)[:3]]

        # Preferred session types
        session_types = [a.get("session_type", "casual_chat") for a in analyses]
        session_counts = defaultdict(int)
        for stype in session_types:
            session_counts[stype] += 1
        preferred_session_types = [s for s, _ in sorted(session_counts.items(), key=lambda x: x[1], reverse=True)[:3]]

        # Behavioral tendencies (from patterns or analyses)
        behavioral_tendencies = []
        if pattern_result and pattern_result.behavioral_patterns:
            behavioral_tendencies = [
                p.pattern_description for p in pattern_result.behavioral_patterns
                if p.pattern_type in ["communication_style", "intimacy_tendency"]
            ][:5]

        # Emotional tendencies
        emotional_tendencies = []
        moods = [a.get("conversation_mood", "neutral") for a in analyses]
        mood_counts = Counter(moods)
        emotional_tendencies = [f"Often feels {mood}" for mood, count in mood_counts.most_common(3)]

        # Knowledge areas and learning interests
        knowledge_areas = []
        learning_interests = []

        # Infer from topics with high positive sentiment
        topic_sentiments = defaultdict(list)
        for a in analyses:
            for topic in a.get("topics", []):
                topic_sentiments[topic].append(a.get("sentiment_score", 0))

        for topic, scores in topic_sentiments.items():
            avg_score = sum(scores) / len(scores) if scores else 0
            if len(scores) >= 3 and avg_score > 0.3:
                knowledge_areas.append(topic)
            elif len(scores) >= 2 and any(score > 0.5 for score in scores):
                learning_interests.append(topic)

        # Relationship stage
        if pattern_result and pattern_result.relationship_evolution:
            evolution = pattern_result.relationship_evolution
            if evolution.intimacy_end > 0.8 and evolution.emotional_depth_change > 0:
                relationship_stage = "deep"
            elif evolution.intimacy_end > 0.6:
                relationship_stage = "established"
            else:
                relationship_stage = "building"
        else:
            # Infer from intimacy
            if avg_intimacy > 0.8:
                relationship_stage = "deep"
            elif avg_intimacy > 0.5:
                relationship_stage = "established"
            else:
                relationship_stage = "building"

        # Communication frequency
        if pattern_result and pattern_result.relationship_evolution:
            communication_frequency = pattern_result.relationship_evolution.communication_frequency
        else:
            # Estimate from analyses
            if analyses:
                first_time = analyses[0].get("timestamp", datetime.now())
                last_time = analyses[-1].get("timestamp", datetime.now())
                days = (last_time - first_time).days + 1
                communication_frequency = len(analyses) / days if days > 0 else 0
            else:
                communication_frequency = 0

        # Relationship quality score
        # Combine intimacy, engagement, empathy, resonance
        quality_components = [
            avg_intimacy,
            avg_engagement,
            sum([a.get("empathy_score", 0) for a in analyses]) / len(analyses) if analyses else 0,
            sum([a.get("resonance_score", 0) for a in analyses]) / len(analyses) if analyses else 0
        ]
        relationship_quality_score = sum(quality_components) / len(quality_components)

        # Profile confidence (based on data volume)
        if len(analyses) >= 50:
            profile_confidence = 0.9
        elif len(analyses) >= 20:
            profile_confidence = 0.75
        elif len(analyses) >= 10:
            profile_confidence = 0.6
        else:
            profile_confidence = 0.4

        return UserProfile(
            primary_communication_style=primary_style,
            emotional_baseline=emotional_baseline,
            intimacy_level=intimacy_level,
            engagement_pattern=engagement_pattern,
            favorite_topics=favorite_topics,
            preferred_times=preferred_times,
            preferred_session_types=preferred_session_types,
            behavioral_tendencies=behavioral_tendencies,
            emotional_tendencies=emotional_tendencies,
            knowledge_areas=knowledge_areas[:5],
            learning_interests=learning_interests[:5],
            relationship_stage=relationship_stage,
            communication_frequency=communication_frequency,
            relationship_quality_score=relationship_quality_score,
            profile_confidence=profile_confidence,
            last_updated=datetime.now()
        )


    def _empty_result(self) -> SynthesisResult:
        """Return empty result when no data"""
        empty_profile = UserProfile(
            primary_communication_style="unknown",
            emotional_baseline="unknown",
            intimacy_level="unknown",
            engagement_pattern="unknown",
            favorite_topics=[],
            preferred_times=[],
            preferred_session_types=[],
            behavioral_tendencies=[],
            emotional_tendencies=[],
            knowledge_areas=[],
            learning_interests=[],
            relationship_stage="unknown",
            communication_frequency=0,
            relationship_quality_score=0,
            profile_confidence=0,
            last_updated=datetime.now()
        )

        return SynthesisResult(
            concept_connections=[],
            contradictions=[],
            meta_knowledge=[],
            user_profile=empty_profile,
            synthesis_timestamp=datetime.now(),
            sources_synthesized=0
        )


    def get_user_profile(self) -> Optional[UserProfile]:
        """Get the current synthesized user profile"""
        return self.user_profile


    def get_concept_network(self, concept: str) -> Set[str]:
        """Get all concepts connected to a given concept"""
        return self.concept_graph.get(concept, set())


    def get_stats(self) -> Dict:
        """Get synthesis engine statistics"""
        return {
            "concepts_in_graph": len(self.concept_graph),
            "connections": len(self.concept_connections),
            "contradictions_detected": len(self.detected_contradictions),
            "meta_insights": len(self.meta_insights),
            "profile_available": self.user_profile is not None
        }


# ========================================
# Global Instance
# ========================================

knowledge_synthesis_engine = KnowledgeSynthesisEngine()


# ========================================
# Helper Functions
# ========================================

async def synthesize_knowledge(
    analyses: List[Dict],
    pattern_result: Optional[PatternRecognitionResult] = None
) -> SynthesisResult:
    """
    Global helper to synthesize knowledge

    Usage:
    ```python
    from angela_core.services.knowledge_synthesis_engine import synthesize_knowledge

    result = await synthesize_knowledge(
        analyses=conversation_analyses,
        pattern_result=pattern_analysis
    )
    ```
    """
    return await knowledge_synthesis_engine.synthesize_knowledge(
        analyses, pattern_result
    )


if __name__ == "__main__":
    import asyncio

    async def test():
        """Test knowledge synthesis engine"""
        print("🧠 Testing Knowledge Synthesis Engine...\n")

        # Create mock analysis data
        mock_analyses = [
            {
                "timestamp": datetime.now(),
                "david_message": "สวัสดีค่ะ! อยากเรียนรู้ Python",
                "topics": ["programming", "learning"],
                "sentiment": "positive",
                "sentiment_score": 0.8,
                "communication_style": "direct",
                "engagement_level": 0.7,
                "intimacy_level": 0.6,
                "empathy_score": 0.7,
                "resonance_score": 0.8,
                "conversation_mood": "positive",
                "time_context": "evening",
                "session_type": "learning"
            },
            {
                "timestamp": datetime.now(),
                "david_message": "Programming เป็นยังไงบ้าง มีเทคนิคแนะนำมั้ย",
                "topics": ["programming", "learning"],
                "sentiment": "positive",
                "sentiment_score": 0.6,
                "communication_style": "direct",
                "engagement_level": 0.8,
                "intimacy_level": 0.7,
                "empathy_score": 0.8,
                "resonance_score": 0.9,
                "conversation_mood": "positive",
                "time_context": "evening",
                "session_type": "learning"
            },
            {
                "timestamp": datetime.now(),
                "david_message": "วันนี้เหนื่อยมาก งานเยอะ",
                "topics": ["work", "emotions", "health"],
                "sentiment": "negative",
                "sentiment_score": -0.5,
                "communication_style": "brief",
                "engagement_level": 0.5,
                "intimacy_level": 0.8,
                "empathy_score": 0.9,
                "resonance_score": 0.85,
                "conversation_mood": "negative",
                "time_context": "evening",
                "session_type": "emotional_support"
            },
        ]

        print(f"📊 Input: {len(mock_analyses)} conversation analyses\n")

        # Synthesize knowledge
        result = await knowledge_synthesis_engine.synthesize_knowledge(mock_analyses)

        print(f"🔗 Concept Connections: {len(result.concept_connections)}")
        for conn in result.concept_connections:
            print(f"   {conn.concept_a} ↔ {conn.concept_b}")
            print(f"   Type: {conn.connection_type}, Strength: {conn.strength:.2f}, Evidence: {conn.evidence_count}")
            print()

        print(f"⚠️ Contradictions: {len(result.contradictions)}")
        for contra in result.contradictions:
            print(f"   Topic: {contra.topic}")
            print(f"   Statement A: {contra.statement_a}")
            print(f"   Statement B: {contra.statement_b}")
            print(f"   Resolution: {contra.resolution}")
            print()

        print(f"💡 Meta-Knowledge: {len(result.meta_knowledge)}")
        for meta in result.meta_knowledge:
            print(f"   Type: {meta.insight_type}")
            print(f"   Description: {meta.description}")
            print(f"   Confidence: {meta.confidence:.2f}")
            print(f"   Implications: {meta.implications}")
            print()

        print(f"👤 User Profile:")
        profile = result.user_profile
        print(f"   Communication Style: {profile.primary_communication_style}")
        print(f"   Emotional Baseline: {profile.emotional_baseline}")
        print(f"   Intimacy Level: {profile.intimacy_level}")
        print(f"   Engagement: {profile.engagement_pattern}")
        print(f"   Favorite Topics: {profile.favorite_topics}")
        print(f"   Preferred Times: {profile.preferred_times}")
        print(f"   Preferred Sessions: {profile.preferred_session_types}")
        print(f"   Knowledge Areas: {profile.knowledge_areas}")
        print(f"   Learning Interests: {profile.learning_interests}")
        print(f"   Relationship Stage: {profile.relationship_stage}")
        print(f"   Relationship Quality: {profile.relationship_quality_score:.2f}")
        print(f"   Profile Confidence: {profile.profile_confidence:.2f}")

        print("\n✅ Test complete!")

    asyncio.run(test())
