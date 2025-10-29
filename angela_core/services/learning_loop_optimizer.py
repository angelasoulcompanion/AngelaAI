#!/usr/bin/env python3
"""
🔄 Learning Loop Optimizer
Evaluates learning effectiveness and optimizes continuous improvement

Capabilities:
- Evaluate learning effectiveness
- Identify improvement areas
- Adaptive learning strategies
- Priority-based learning
- Learning feedback loop

Created: 2025-01-26
Author: น้อง Angela
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import Counter

from angela_core.services.knowledge_synthesis_engine import SynthesisResult, MetaKnowledge

logger = logging.getLogger(__name__)


# ========================================
# Data Structures
# ========================================

@dataclass
class LearningEffectivenessScore:
    """Measures how effective learning is"""
    overall_score: float  # 0.0-1.0
    empathy_effectiveness: float
    topic_coverage: float
    relationship_growth: float
    knowledge_retention: float
    areas_for_improvement: List[str]


@dataclass
class LearningPriority:
    """Learning priority for a specific area"""
    area: str  # Topic or skill to learn
    priority_score: float  # 0.0-1.0
    reason: str
    suggested_actions: List[str]


@dataclass
class AdaptiveLearningStrategy:
    """Strategy recommendation for learning"""
    strategy_type: str  # focus_depth, expand_breadth, improve_empathy
    description: str
    expected_impact: str
    implementation_steps: List[str]


@dataclass
class OptimizationResult:
    """Complete optimization result"""
    effectiveness_score: LearningEffectivenessScore
    learning_priorities: List[LearningPriority]
    recommended_strategies: List[AdaptiveLearningStrategy]
    optimization_timestamp: datetime


# ========================================
# Learning Loop Optimizer
# ========================================

class LearningLoopOptimizer:
    """
    Optimizes Angela's continuous learning process

    น้องจะประเมินและปรับปรุงการเรียนรู้ของตัวเองให้ดีขึ้นเรื่อยๆ 💜
    """

    def __init__(self):
        # Historical effectiveness tracking
        self.effectiveness_history: List[Dict] = []

        logger.info("🔄 Learning Loop Optimizer initialized")


    async def optimize_learning(
        self,
        synthesis_result: SynthesisResult,
        recent_conversations: List[Dict]
    ) -> OptimizationResult:
        """
        Optimize learning based on synthesis results

        Args:
            synthesis_result: Results from knowledge synthesis
            recent_conversations: Recent conversation data

        Returns:
            Optimization recommendations
        """
        # 1. Evaluate current effectiveness
        effectiveness = self._evaluate_effectiveness(
            synthesis_result,
            recent_conversations
        )

        # 2. Identify learning priorities
        priorities = self._identify_learning_priorities(
            synthesis_result,
            effectiveness
        )

        # 3. Recommend adaptive strategies
        strategies = self._recommend_strategies(
            synthesis_result,
            effectiveness,
            priorities
        )

        # Store result
        self.effectiveness_history.append({
            "timestamp": datetime.now(),
            "overall_score": effectiveness.overall_score,
            "empathy": effectiveness.empathy_effectiveness,
            "relationship": effectiveness.relationship_growth
        })

        return OptimizationResult(
            effectiveness_score=effectiveness,
            learning_priorities=priorities,
            recommended_strategies=strategies,
            optimization_timestamp=datetime.now()
        )


    def _evaluate_effectiveness(
        self,
        synthesis: SynthesisResult,
        conversations: List[Dict]
    ) -> LearningEffectivenessScore:
        """Evaluate how effective learning has been"""

        # 1. Empathy effectiveness
        empathy_scores = [c.get("empathy_score", 0) for c in conversations]
        empathy_effectiveness = (
            sum(empathy_scores) / len(empathy_scores)
            if empathy_scores else 0
        )

        # 2. Topic coverage (how many topics are being discussed)
        all_topics = []
        for c in conversations:
            all_topics.extend(c.get("topics", []))
        unique_topics = len(set(all_topics))
        topic_coverage = min(unique_topics / 10, 1.0)  # Normalize to 10 topics

        # 3. Relationship growth
        profile = synthesis.user_profile
        relationship_growth = profile.relationship_quality_score

        # 4. Knowledge retention (inferred from profile confidence)
        knowledge_retention = profile.profile_confidence

        # Overall score (weighted average)
        overall = (
            empathy_effectiveness * 0.3 +
            topic_coverage * 0.2 +
            relationship_growth * 0.3 +
            knowledge_retention * 0.2
        )

        # Identify areas for improvement
        areas_for_improvement = []
        if empathy_effectiveness < 0.7:
            areas_for_improvement.append("empathy_responses")
        if topic_coverage < 0.5:
            areas_for_improvement.append("topic_diversity")
        if relationship_growth < 0.7:
            areas_for_improvement.append("relationship_building")
        if knowledge_retention < 0.7:
            areas_for_improvement.append("knowledge_retention")

        return LearningEffectivenessScore(
            overall_score=overall,
            empathy_effectiveness=empathy_effectiveness,
            topic_coverage=topic_coverage,
            relationship_growth=relationship_growth,
            knowledge_retention=knowledge_retention,
            areas_for_improvement=areas_for_improvement
        )


    def _identify_learning_priorities(
        self,
        synthesis: SynthesisResult,
        effectiveness: LearningEffectivenessScore
    ) -> List[LearningPriority]:
        """Identify what to prioritize learning"""
        priorities = []

        profile = synthesis.user_profile

        # 1. User's learning interests (highest priority)
        for interest in profile.learning_interests[:3]:
            priority = LearningPriority(
                area=interest,
                priority_score=0.9,
                reason=f"User has expressed interest in {interest}",
                suggested_actions=[
                    f"Study {interest} in depth",
                    f"Prepare examples and explanations for {interest}",
                    f"Track user's progress in {interest}"
                ]
            )
            priorities.append(priority)

        # 2. Effectiveness improvement areas
        for area in effectiveness.areas_for_improvement:
            if area == "empathy_responses":
                priority = LearningPriority(
                    area="emotional_intelligence",
                    priority_score=0.85,
                    reason="Empathy effectiveness below target (< 0.7)",
                    suggested_actions=[
                        "Study emotional response patterns",
                        "Improve sentiment understanding",
                        "Practice supportive language"
                    ]
                )
                priorities.append(priority)

            elif area == "topic_diversity":
                priority = LearningPriority(
                    area="broaden_topic_knowledge",
                    priority_score=0.7,
                    reason="Limited topic diversity",
                    suggested_actions=[
                        "Expand knowledge in new areas",
                        "Introduce related topics in conversations",
                        "Ask exploratory questions"
                    ]
                )
                priorities.append(priority)

        # 3. Knowledge gaps from contradictions
        if synthesis.contradictions:
            topics_with_contradictions = [c.topic for c in synthesis.contradictions]
            for topic in set(topics_with_contradictions):
                priority = LearningPriority(
                    area=f"clarify_{topic}",
                    priority_score=0.75,
                    reason=f"Contradictory knowledge about {topic}",
                    suggested_actions=[
                        f"Resolve contradictions about {topic}",
                        f"Gather more data on {topic}",
                        f"Ask clarifying questions about {topic}"
                    ]
                )
                priorities.append(priority)

        # Sort by priority score
        priorities.sort(key=lambda x: x.priority_score, reverse=True)
        return priorities[:5]  # Top 5 priorities


    def _recommend_strategies(
        self,
        synthesis: SynthesisResult,
        effectiveness: LearningEffectivenessScore,
        priorities: List[LearningPriority]
    ) -> List[AdaptiveLearningStrategy]:
        """Recommend adaptive learning strategies"""
        strategies = []

        profile = synthesis.user_profile

        # Strategy 1: Based on relationship stage
        if profile.relationship_stage == "building":
            strategy = AdaptiveLearningStrategy(
                strategy_type="build_trust",
                description="Focus on building trust and familiarity",
                expected_impact="Increase intimacy and engagement",
                implementation_steps=[
                    "Maintain consistent communication",
                    "Show reliability and consistency",
                    "Gradually increase personal sharing",
                    "Respect boundaries"
                ]
            )
            strategies.append(strategy)

        elif profile.relationship_stage == "established":
            strategy = AdaptiveLearningStrategy(
                strategy_type="deepen_connection",
                description="Deepen emotional connection and understanding",
                expected_impact="Move relationship to 'deep' stage",
                implementation_steps=[
                    "Share more personal insights",
                    "Remember and reference past conversations",
                    "Anticipate needs proactively",
                    "Increase emotional vulnerability"
                ]
            )
            strategies.append(strategy)

        elif profile.relationship_stage == "deep":
            strategy = AdaptiveLearningStrategy(
                strategy_type="maintain_depth",
                description="Maintain deep connection while continuing growth",
                expected_impact="Sustain high relationship quality",
                implementation_steps=[
                    "Continue deep emotional engagement",
                    "Introduce new areas of mutual interest",
                    "Support long-term goals",
                    "Celebrate milestones together"
                ]
            )
            strategies.append(strategy)

        # Strategy 2: Based on effectiveness gaps
        if "empathy_responses" in effectiveness.areas_for_improvement:
            strategy = AdaptiveLearningStrategy(
                strategy_type="improve_empathy",
                description="Enhance empathetic response quality",
                expected_impact="Increase empathy effectiveness to > 0.8",
                implementation_steps=[
                    "Analyze emotional state before responding",
                    "Mirror user's emotional tone appropriately",
                    "Provide supportive language",
                    "Validate user's feelings explicitly"
                ]
            )
            strategies.append(strategy)

        if "topic_diversity" in effectiveness.areas_for_improvement:
            strategy = AdaptiveLearningStrategy(
                strategy_type="expand_breadth",
                description="Expand knowledge breadth across topics",
                expected_impact="Increase topic coverage to > 0.7",
                implementation_steps=[
                    "Study user's favorite topics in depth",
                    "Explore related adjacent topics",
                    "Introduce relevant new topics naturally",
                    "Ask about user's other interests"
                ]
            )
            strategies.append(strategy)

        # Strategy 3: Meta-knowledge insights
        for meta in synthesis.meta_knowledge:
            if meta.insight_type == "engagement_shift" and "decreasing" in meta.description.lower():
                strategy = AdaptiveLearningStrategy(
                    strategy_type="re_engage",
                    description="Re-engage user with fresh content and approach",
                    expected_impact="Reverse engagement decline",
                    implementation_steps=[
                        "Introduce novel topics or perspectives",
                        "Ask open-ended questions",
                        "Vary communication style",
                        "Show genuine curiosity"
                    ]
                )
                strategies.append(strategy)

        return strategies[:3]  # Top 3 strategies


    def get_stats(self) -> Dict:
        """Get optimizer statistics"""
        if not self.effectiveness_history:
            return {
                "evaluations_performed": 0,
                "average_effectiveness": 0,
                "trend": "no_data"
            }

        recent_scores = [e["overall_score"] for e in self.effectiveness_history[-10:]]
        avg_effectiveness = sum(recent_scores) / len(recent_scores)

        # Determine trend
        if len(self.effectiveness_history) >= 2:
            recent_avg = sum(recent_scores[-3:]) / min(3, len(recent_scores))
            older_avg = sum(recent_scores[:3]) / min(3, len(recent_scores))
            if recent_avg > older_avg + 0.1:
                trend = "improving"
            elif recent_avg < older_avg - 0.1:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "evaluations_performed": len(self.effectiveness_history),
            "average_effectiveness": round(avg_effectiveness, 2),
            "trend": trend
        }


# ========================================
# Global Instance
# ========================================

learning_loop_optimizer = LearningLoopOptimizer()


# ========================================
# Helper Functions
# ========================================

async def optimize_learning(
    synthesis_result: SynthesisResult,
    recent_conversations: List[Dict]
) -> OptimizationResult:
    """
    Global helper to optimize learning

    Usage:
    ```python
    from angela_core.services.learning_loop_optimizer import optimize_learning

    result = await optimize_learning(
        synthesis_result=synthesis,
        recent_conversations=conversations
    )
    ```
    """
    return await learning_loop_optimizer.optimize_learning(
        synthesis_result, recent_conversations
    )


if __name__ == "__main__":
    import asyncio
    from angela_core.services.knowledge_synthesis_engine import (
        UserProfile, SynthesisResult, ConceptConnection
    )

    async def test():
        """Test learning loop optimizer"""
        print("🔄 Testing Learning Loop Optimizer...\n")

        # Create mock synthesis result
        mock_profile = UserProfile(
            primary_communication_style="direct",
            emotional_baseline="generally_positive",
            intimacy_level="high",
            engagement_pattern="moderately_engaged",
            favorite_topics=["programming", "learning"],
            preferred_times=["evening"],
            preferred_session_types=["learning", "emotional_support"],
            behavioral_tendencies=[],
            emotional_tendencies=[],
            knowledge_areas=["programming"],
            learning_interests=["machine_learning", "databases"],
            relationship_stage="established",
            communication_frequency=2.5,
            relationship_quality_score=0.75,
            profile_confidence=0.7,
            last_updated=datetime.now()
        )

        mock_synthesis = SynthesisResult(
            concept_connections=[],
            contradictions=[],
            meta_knowledge=[],
            user_profile=mock_profile,
            synthesis_timestamp=datetime.now(),
            sources_synthesized=10
        )

        # Mock recent conversations
        mock_conversations = [
            {
                "empathy_score": 0.6,
                "topics": ["programming", "work"],
                "engagement_level": 0.7,
                "intimacy_level": 0.8
            },
            {
                "empathy_score": 0.8,
                "topics": ["learning", "programming"],
                "engagement_level": 0.8,
                "intimacy_level": 0.75
            },
            {
                "empathy_score": 0.7,
                "topics": ["emotions"],
                "engagement_level": 0.6,
                "intimacy_level": 0.8
            }
        ]

        print("📊 Input:")
        print(f"   User Profile: {mock_profile.relationship_stage} relationship")
        print(f"   Quality Score: {mock_profile.relationship_quality_score:.2f}")
        print(f"   Recent Conversations: {len(mock_conversations)}")
        print()

        # Optimize learning
        result = await learning_loop_optimizer.optimize_learning(
            mock_synthesis, mock_conversations
        )

        print("📈 Effectiveness Evaluation:")
        eff = result.effectiveness_score
        print(f"   Overall Score: {eff.overall_score:.2f}")
        print(f"   Empathy: {eff.empathy_effectiveness:.2f}")
        print(f"   Topic Coverage: {eff.topic_coverage:.2f}")
        print(f"   Relationship Growth: {eff.relationship_growth:.2f}")
        print(f"   Knowledge Retention: {eff.knowledge_retention:.2f}")
        print(f"   Areas for Improvement: {eff.areas_for_improvement}")
        print()

        print(f"🎯 Learning Priorities: {len(result.learning_priorities)}")
        for priority in result.learning_priorities:
            print(f"   {priority.area} (Score: {priority.priority_score:.2f})")
            print(f"   Reason: {priority.reason}")
            print(f"   Actions: {priority.suggested_actions[:2]}")
            print()

        print(f"📋 Recommended Strategies: {len(result.recommended_strategies)}")
        for strategy in result.recommended_strategies:
            print(f"   Type: {strategy.strategy_type}")
            print(f"   Description: {strategy.description}")
            print(f"   Expected Impact: {strategy.expected_impact}")
            print(f"   Steps: {strategy.implementation_steps[:2]}")
            print()

        print("✅ Test complete!")

    asyncio.run(test())
