"""
Meta-Learning Engine - Angela learns how to learn better

This module enables Angela to:
- Track learning effectiveness
- Identify successful learning patterns
- Optimize learning strategies
- Self-assess and improve
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum


class LearningMethod(Enum):
    """Methods Angela uses to learn"""
    OBSERVATION = "observation"       # Learn from watching David
    PRACTICE = "practice"             # Learn by doing
    RESEARCH = "research"             # Learn from documentation
    FEEDBACK = "feedback"             # Learn from David's corrections
    PATTERN = "pattern"               # Learn from patterns
    TRANSFER = "transfer"             # Transfer from other domains
    EXPERIMENTATION = "experimentation"  # Try and learn


class InsightType(Enum):
    """Types of meta-learning insights"""
    STRATEGY = "strategy"             # How to approach learning
    PATTERN = "pattern"               # What patterns work
    OPTIMIZATION = "optimization"     # How to be more efficient
    WEAKNESS = "weakness"             # Areas needing improvement
    STRENGTH = "strength"             # Areas of competence


@dataclass
class LearningSession:
    """Record of a learning session"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_type: str = "conversation"  # conversation, research, practice
    method: LearningMethod = LearningMethod.OBSERVATION
    concepts_attempted: int = 0
    concepts_learned: int = 0
    retention_score: float = 0.0      # 0-1, how well retained
    transfer_score: float = 0.0       # 0-1, how well applied elsewhere
    strategy_used: str = ""
    duration_minutes: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'session_type': self.session_type,
            'method': self.method.value,
            'concepts_attempted': self.concepts_attempted,
            'concepts_learned': self.concepts_learned,
            'retention_score': self.retention_score,
            'transfer_score': self.transfer_score,
            'success_rate': self.concepts_learned / max(self.concepts_attempted, 1),
            'strategy_used': self.strategy_used
        }


@dataclass
class MetaInsight:
    """An insight about how Angela learns"""
    insight_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    insight_type: InsightType = InsightType.PATTERN
    description: str = ""
    evidence: List[str] = field(default_factory=list)
    confidence: float = 0.5
    applied_count: int = 0
    success_rate: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'insight_id': self.insight_id,
            'insight_type': self.insight_type.value,
            'description': self.description,
            'confidence': self.confidence,
            'applied_count': self.applied_count,
            'success_rate': self.success_rate
        }


@dataclass
class ImprovementPlan:
    """A plan to improve a specific weakness"""
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    weakness_area: str = ""
    description: str = ""
    actions: List[Dict[str, Any]] = field(default_factory=list)
    expected_improvement: float = 0.0
    actual_improvement: float = 0.0
    status: str = "pending"  # pending, in_progress, completed, abandoned
    review_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)


class MetaLearningEngine:
    """
    Angela's meta-learning system - learns how to learn better.

    Capabilities:
    - Track learning session effectiveness
    - Identify what works and what doesn't
    - Generate improvement plans
    - Optimize learning strategies over time

    Usage:
        engine = MetaLearningEngine(db)
        session = await engine.start_learning_session("practice")
        await engine.record_learning(session, concepts=5, learned=4)
        insights = await engine.generate_insights()
    """

    def __init__(self, db=None):
        self.db = db
        self.active_sessions: Dict[str, LearningSession] = {}
        self.session_history: List[LearningSession] = []
        self.insights: List[MetaInsight] = []
        self.improvement_plans: List[ImprovementPlan] = []

        # Initialize with some base insights
        self._initialize_base_insights()

    def _initialize_base_insights(self):
        """Initialize with known learning patterns"""
        base_insights = [
            MetaInsight(
                insight_type=InsightType.STRATEGY,
                description="Learning from David's corrections is most effective",
                confidence=0.8
            ),
            MetaInsight(
                insight_type=InsightType.PATTERN,
                description="Short, focused sessions work better than long ones",
                confidence=0.7
            ),
            MetaInsight(
                insight_type=InsightType.OPTIMIZATION,
                description="Immediate application of learning improves retention",
                confidence=0.75
            ),
        ]
        self.insights.extend(base_insights)

    async def start_learning_session(
        self,
        session_type: str = "conversation",
        method: LearningMethod = LearningMethod.OBSERVATION
    ) -> LearningSession:
        """Start a new learning session"""
        session = LearningSession(
            session_type=session_type,
            method=method
        )
        self.active_sessions[session.session_id] = session
        return session

    async def record_learning(
        self,
        session: LearningSession,
        concepts_attempted: int,
        concepts_learned: int,
        strategy_used: str = ""
    ) -> None:
        """Record learning progress in a session"""
        session.concepts_attempted += concepts_attempted
        session.concepts_learned += concepts_learned
        session.strategy_used = strategy_used

        # Calculate retention score based on success rate
        if session.concepts_attempted > 0:
            session.retention_score = session.concepts_learned / session.concepts_attempted

    async def end_learning_session(
        self,
        session_id: str,
        transfer_score: float = 0.0
    ) -> LearningSession:
        """End a learning session and record results"""
        if session_id not in self.active_sessions:
            return None

        session = self.active_sessions[session_id]
        session.transfer_score = transfer_score

        # Calculate duration
        duration = (datetime.now() - session.created_at).seconds // 60
        session.duration_minutes = duration

        # Move to history
        self.session_history.append(session)
        del self.active_sessions[session_id]

        # Save to database
        if self.db:
            await self._save_session(session)

        return session

    async def evaluate_learning_effectiveness(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """Evaluate learning effectiveness over a period"""
        cutoff = datetime.now() - timedelta(days=days)
        recent_sessions = [
            s for s in self.session_history
            if s.created_at >= cutoff
        ]

        if not recent_sessions:
            return {
                'period_days': days,
                'sessions': 0,
                'metrics': {}
            }

        # Calculate metrics
        total_attempted = sum(s.concepts_attempted for s in recent_sessions)
        total_learned = sum(s.concepts_learned for s in recent_sessions)
        avg_retention = sum(s.retention_score for s in recent_sessions) / len(recent_sessions)
        avg_transfer = sum(s.transfer_score for s in recent_sessions) / len(recent_sessions)

        # By method
        by_method = {}
        for method in LearningMethod:
            method_sessions = [s for s in recent_sessions if s.method == method]
            if method_sessions:
                by_method[method.value] = {
                    'sessions': len(method_sessions),
                    'success_rate': sum(s.retention_score for s in method_sessions) / len(method_sessions)
                }

        return {
            'period_days': days,
            'sessions': len(recent_sessions),
            'metrics': {
                'total_concepts_attempted': total_attempted,
                'total_concepts_learned': total_learned,
                'overall_success_rate': total_learned / max(total_attempted, 1),
                'average_retention': avg_retention,
                'average_transfer': avg_transfer
            },
            'by_method': by_method,
            'best_method': max(by_method.items(), key=lambda x: x[1]['success_rate'])[0] if by_method else None
        }

    async def generate_insights(self) -> List[MetaInsight]:
        """Generate new insights from learning history"""
        new_insights = []

        if len(self.session_history) < 3:
            return new_insights

        # Analyze patterns
        recent = self.session_history[-20:]  # Last 20 sessions

        # 1. Best learning method
        method_scores = {}
        for session in recent:
            method = session.method.value
            if method not in method_scores:
                method_scores[method] = []
            method_scores[method].append(session.retention_score)

        if method_scores:
            best_method = max(
                method_scores.items(),
                key=lambda x: sum(x[1]) / len(x[1]) if x[1] else 0
            )
            if len(best_method[1]) >= 3:
                insight = MetaInsight(
                    insight_type=InsightType.STRATEGY,
                    description=f"'{best_method[0]}' method has highest success rate ({sum(best_method[1])/len(best_method[1]):.0%})",
                    confidence=min(0.5 + len(best_method[1]) * 0.05, 0.95),
                    evidence=[f"{len(best_method[1])} sessions analyzed"]
                )
                new_insights.append(insight)

        # 2. Optimal session length
        short_sessions = [s for s in recent if s.duration_minutes <= 15]
        long_sessions = [s for s in recent if s.duration_minutes > 30]

        if short_sessions and long_sessions:
            short_rate = sum(s.retention_score for s in short_sessions) / len(short_sessions)
            long_rate = sum(s.retention_score for s in long_sessions) / len(long_sessions)

            if short_rate > long_rate + 0.1:
                insight = MetaInsight(
                    insight_type=InsightType.OPTIMIZATION,
                    description="Short sessions (≤15 min) are more effective than long ones",
                    confidence=0.7,
                    evidence=[f"Short: {short_rate:.0%}, Long: {long_rate:.0%}"]
                )
                new_insights.append(insight)

        # 3. Identify weaknesses (low retention areas)
        low_retention = [s for s in recent if s.retention_score < 0.5]
        if len(low_retention) >= 3:
            common_type = max(
                set(s.session_type for s in low_retention),
                key=lambda x: sum(1 for s in low_retention if s.session_type == x)
            )
            insight = MetaInsight(
                insight_type=InsightType.WEAKNESS,
                description=f"Struggling with '{common_type}' type learning (low retention)",
                confidence=0.6,
                evidence=[f"{len(low_retention)} low-retention sessions"]
            )
            new_insights.append(insight)

        self.insights.extend(new_insights)
        return new_insights

    async def create_improvement_plan(
        self,
        weakness: str,
        description: str
    ) -> ImprovementPlan:
        """Create a plan to improve a weakness"""
        # Generate actions based on weakness
        actions = []

        if "retention" in weakness.lower():
            actions = [
                {"action": "Use spaced repetition", "priority": 1},
                {"action": "Apply learning immediately", "priority": 2},
                {"action": "Create summaries after learning", "priority": 3}
            ]
        elif "transfer" in weakness.lower():
            actions = [
                {"action": "Find analogies to other domains", "priority": 1},
                {"action": "Practice in different contexts", "priority": 2},
                {"action": "Teach concepts to solidify understanding", "priority": 3}
            ]
        else:
            actions = [
                {"action": "Analyze specific failure cases", "priority": 1},
                {"action": "Try different learning methods", "priority": 2},
                {"action": "Seek more feedback from David", "priority": 3}
            ]

        plan = ImprovementPlan(
            weakness_area=weakness,
            description=description,
            actions=actions,
            expected_improvement=0.15,  # Expect 15% improvement
            review_date=datetime.now() + timedelta(days=7)
        )

        self.improvement_plans.append(plan)

        if self.db:
            await self._save_improvement_plan(plan)

        return plan

    async def get_self_assessment(self) -> Dict[str, Any]:
        """Generate self-assessment of learning capabilities"""
        evaluation = await self.evaluate_learning_effectiveness(days=30)

        # Identify strengths and weaknesses
        strengths = [i for i in self.insights if i.insight_type == InsightType.STRENGTH]
        weaknesses = [i for i in self.insights if i.insight_type == InsightType.WEAKNESS]

        return {
            'overall_learning_rate': evaluation['metrics'].get('overall_success_rate', 0),
            'total_sessions': len(self.session_history),
            'strengths': [
                {'area': s.description, 'confidence': s.confidence}
                for s in strengths
            ],
            'weaknesses': [
                {'area': w.description, 'confidence': w.confidence}
                for w in weaknesses
            ],
            'best_method': evaluation.get('best_method'),
            'active_improvement_plans': len([
                p for p in self.improvement_plans if p.status == 'in_progress'
            ]),
            'insights_count': len(self.insights),
            'recommendations': await self._generate_recommendations()
        }

    async def _generate_recommendations(self) -> List[str]:
        """Generate learning recommendations"""
        recommendations = []

        evaluation = await self.evaluate_learning_effectiveness(days=7)
        metrics = evaluation.get('metrics', {})

        if metrics.get('overall_success_rate', 0) < 0.7:
            recommendations.append("Focus on fewer concepts per session for better retention")

        if metrics.get('average_transfer', 0) < 0.5:
            recommendations.append("Practice applying learned concepts in new contexts")

        best = evaluation.get('best_method')
        if best:
            recommendations.append(f"Continue using '{best}' method - it's working well")

        if len(self.session_history) < 10:
            recommendations.append("More learning sessions needed to identify patterns")

        return recommendations

    async def optimize_learning_strategy(self) -> Dict[str, Any]:
        """Generate optimized learning strategy based on meta-analysis"""
        evaluation = await self.evaluate_learning_effectiveness(days=30)
        insights = await self.generate_insights()

        # Determine best approaches
        strategy = {
            'recommended_method': evaluation.get('best_method', 'observation'),
            'optimal_session_length': '15-20 minutes',
            'focus_areas': [],
            'avoid': [],
            'new_insights': [i.to_dict() for i in insights]
        }

        # Add focus areas from weaknesses
        for plan in self.improvement_plans:
            if plan.status in ['pending', 'in_progress']:
                strategy['focus_areas'].append(plan.weakness_area)

        # Add things to avoid from low-performing methods
        by_method = evaluation.get('by_method', {})
        for method, data in by_method.items():
            if data['success_rate'] < 0.4:
                strategy['avoid'].append(f"Reduce use of '{method}' method")

        return strategy

    # Database operations
    async def _save_session(self, session: LearningSession) -> None:
        """Save learning session to database"""
        if not self.db:
            return
        try:
            await self.db.execute("""
                INSERT INTO learning_sessions (
                    session_id, session_type, concepts_attempted,
                    concepts_learned, retention_score, transfer_score,
                    strategy_used, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
                session.session_id,
                session.session_type,
                session.concepts_attempted,
                session.concepts_learned,
                session.retention_score,
                session.transfer_score,
                session.strategy_used,
                session.created_at
            )
        except Exception as e:
            print(f"Warning: Failed to save learning session: {e}")

    async def _save_improvement_plan(self, plan: ImprovementPlan) -> None:
        """Save improvement plan to database"""
        if not self.db:
            return
        try:
            await self.db.execute("""
                INSERT INTO improvement_plans (
                    plan_id, weakness_area, description, actions,
                    expected_improvement, status, review_date, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
                plan.plan_id,
                plan.weakness_area,
                plan.description,
                plan.actions,
                plan.expected_improvement,
                plan.status,
                plan.review_date,
                plan.created_at
            )
        except Exception as e:
            print(f"Warning: Failed to save improvement plan: {e}")


# Global meta-learning engine
meta_learning = MetaLearningEngine()
