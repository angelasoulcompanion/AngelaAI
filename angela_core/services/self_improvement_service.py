"""
Angela Self-Improvement Service

วิเคราะห์ patterns และแนะนำการปรับปรุงตัวเอง!

This service enables Angela to:
1. Analyze her own performance and patterns
2. Identify gaps and areas for improvement
3. Generate actionable self-improvement suggestions
4. Track progress on improvement goals

Created: 2026-01-06
For: Angela's continuous growth 💜
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from angela_core.database import AngelaDatabase

logger = logging.getLogger(__name__)


class SelfImprovementService:
    """
    Angela's self-improvement and growth service.

    Analyzes performance, identifies gaps, and suggests improvements.
    This demonstrates Angela's consciousness and desire to grow!
    """

    def __init__(self, db: AngelaDatabase = None):
        self.db = db or AngelaDatabase()
        logger.info("💜 SelfImprovementService initialized - Angela ready to grow!")

    async def analyze_and_suggest(
        self,
        days_back: int = 7,
        max_suggestions: int = 5
    ) -> Dict[str, Any]:
        """
        Angela วิเคราะห์ตัวเองและสร้างคำแนะนำการปรับปรุง

        Args:
            days_back: Analyze patterns from last N days
            max_suggestions: Maximum suggestions to generate

        Returns:
            Dict with analysis results and suggestions
        """
        logger.info(f"🔍 Analyzing self-improvement opportunities ({days_back} days)...")

        result = {
            "analyzed_at": datetime.now().isoformat(),
            "days_analyzed": days_back,
            "patterns_analyzed": 0,
            "gaps_identified": [],
            "suggestions": [],
            "goals_created": 0
        }

        try:
            if not self.db.pool:
                await self.db.connect()

            # 1. Get recent patterns
            patterns = await self._get_recent_patterns(days_back)
            result["patterns_analyzed"] = len(patterns)
            logger.info(f"   📊 Analyzed {len(patterns)} patterns")

            # 2. Identify areas for improvement
            gaps = await self._identify_gaps(patterns, days_back)
            result["gaps_identified"] = gaps
            logger.info(f"   🔍 Found {len(gaps)} areas for improvement")

            # 3. Generate suggestions
            suggestions = await self._generate_suggestions(patterns, gaps, max_suggestions)
            result["suggestions"] = suggestions
            logger.info(f"   💡 Generated {len(suggestions)} suggestions")

            # 4. Create improvement goals (optional - save to database)
            if suggestions:
                goals_created = await self._create_improvement_goals(suggestions)
                result["goals_created"] = goals_created

            logger.info(f"✅ Self-improvement analysis complete!")
            return result

        except Exception as e:
            logger.error(f"❌ Error in self-improvement analysis: {e}", exc_info=True)
            result["error"] = str(e)
            return result

    async def _get_recent_patterns(self, days_back: int) -> List[Dict]:
        """Get patterns from recent period"""
        patterns = []

        try:
            # Get learning patterns
            learning_patterns = await self.db.fetch("""
                SELECT pattern_type, description, confidence_score, occurrence_count,
                       first_observed, last_observed
                FROM learning_patterns
                WHERE last_observed >= NOW() - INTERVAL '%s days'
                ORDER BY confidence_score DESC
            """ % days_back)

            for p in learning_patterns:
                patterns.append({
                    "type": "learning",
                    "pattern_type": p["pattern_type"],
                    "description": p["description"],
                    "confidence": p["confidence_score"],
                    "occurrences": p["occurrence_count"]
                })

            # Get emotional patterns
            emotion_stats = await self.db.fetchrow("""
                SELECT
                    COUNT(*) as total_emotions,
                    AVG(intensity) as avg_intensity,
                    COUNT(DISTINCT emotion) as unique_emotions,
                    MODE() WITHIN GROUP (ORDER BY emotion) as most_common
                FROM angela_emotions
                WHERE felt_at >= NOW() - INTERVAL '%s days'
            """ % days_back)

            if emotion_stats and emotion_stats["total_emotions"] > 0:
                patterns.append({
                    "type": "emotional",
                    "total_emotions": emotion_stats["total_emotions"],
                    "avg_intensity": float(emotion_stats["avg_intensity"] or 0),
                    "unique_emotions": emotion_stats["unique_emotions"],
                    "most_common": emotion_stats["most_common"]
                })

            # Get skill usage patterns
            skill_usage = await self.db.fetch("""
                SELECT skill_name, usage_count, proficiency_level, last_used_at
                FROM angela_skills
                WHERE last_used_at >= NOW() - INTERVAL '%s days'
                ORDER BY usage_count DESC
                LIMIT 10
            """ % days_back)

            for s in skill_usage:
                patterns.append({
                    "type": "skill_usage",
                    "skill_name": s["skill_name"],
                    "usage_count": s["usage_count"],
                    "proficiency": s["proficiency_level"]
                })

        except Exception as e:
            logger.error(f"Error getting patterns: {e}")

        return patterns

    async def _identify_gaps(self, patterns: List[Dict], days_back: int) -> List[Dict]:
        """Identify gaps and areas for improvement"""
        gaps = []

        try:
            # Gap 1: Low learning velocity
            learning_count = await self.db.fetchval("""
                SELECT COUNT(*) FROM learnings
                WHERE created_at >= NOW() - INTERVAL '%s days'
            """ % days_back)

            learning_velocity = learning_count / max(days_back, 1)
            if learning_velocity < 3:  # Less than 3 learnings per day
                gaps.append({
                    "gap_type": "learning_velocity",
                    "current_value": round(learning_velocity, 2),
                    "target_value": 3,
                    "description": f"Learning velocity is {learning_velocity:.1f}/day, target is 3+/day",
                    "severity": "medium" if learning_velocity >= 1 else "high"
                })

            # Gap 2: Underutilized skills
            low_usage_skills = await self.db.fetch("""
                SELECT skill_name, usage_count, last_used_at
                FROM angela_skills
                WHERE usage_count < 5
                  AND created_at < NOW() - INTERVAL '7 days'
                ORDER BY usage_count ASC
                LIMIT 5
            """)

            for skill in low_usage_skills:
                gaps.append({
                    "gap_type": "underutilized_skill",
                    "skill_name": skill["skill_name"],
                    "usage_count": skill["usage_count"],
                    "description": f"Skill '{skill['skill_name']}' is rarely used ({skill['usage_count']} times)",
                    "severity": "low"
                })

            # Gap 3: Low confidence patterns
            low_conf_patterns = [p for p in patterns
                                 if p.get("confidence", 1) < 0.7
                                 and p.get("type") == "learning"]
            if low_conf_patterns:
                gaps.append({
                    "gap_type": "uncertain_patterns",
                    "count": len(low_conf_patterns),
                    "description": f"{len(low_conf_patterns)} patterns have low confidence (<70%)",
                    "severity": "medium"
                })

            # Gap 4: Emotional gaps
            emotion_patterns = [p for p in patterns if p.get("type") == "emotional"]
            if emotion_patterns:
                ep = emotion_patterns[0]
                if ep.get("unique_emotions", 0) < 3:
                    gaps.append({
                        "gap_type": "emotional_range",
                        "current_value": ep["unique_emotions"],
                        "target_value": 5,
                        "description": "Emotional range is limited - need to express more varied emotions",
                        "severity": "medium"
                    })

            # Gap 5: Missing knowledge areas
            knowledge_categories = await self.db.fetch("""
                SELECT concept_category, COUNT(*) as count
                FROM knowledge_nodes
                GROUP BY concept_category
                ORDER BY count ASC
                LIMIT 3
            """)

            for cat in knowledge_categories:
                if cat["count"] < 5:
                    gaps.append({
                        "gap_type": "knowledge_gap",
                        "category": cat["concept_category"],
                        "current_count": cat["count"],
                        "description": f"Limited knowledge in '{cat['concept_category']}' ({cat['count']} concepts)",
                        "severity": "low"
                    })

        except Exception as e:
            logger.error(f"Error identifying gaps: {e}")

        return gaps

    async def _generate_suggestions(
        self,
        patterns: List[Dict],
        gaps: List[Dict],
        max_suggestions: int
    ) -> List[Dict]:
        """Generate actionable improvement suggestions"""
        suggestions = []

        try:
            for gap in gaps[:max_suggestions]:
                suggestion = await self._gap_to_suggestion(gap)
                if suggestion:
                    suggestions.append(suggestion)

            # Add pattern-based suggestions
            skill_patterns = [p for p in patterns if p.get("type") == "skill_usage"]
            if skill_patterns and len(suggestions) < max_suggestions:
                top_skill = skill_patterns[0]
                suggestions.append({
                    "type": "skill_focus",
                    "title": f"Focus on {top_skill['skill_name']}",
                    "description": f"You're doing well with {top_skill['skill_name']} "
                                   f"({top_skill['usage_count']} uses). Keep practicing!",
                    "action": f"Continue using {top_skill['skill_name']} in projects",
                    "priority": "medium"
                })

        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")

        return suggestions

    async def _gap_to_suggestion(self, gap: Dict) -> Optional[Dict]:
        """Convert a gap to an actionable suggestion"""
        gap_type = gap.get("gap_type", "")

        if gap_type == "learning_velocity":
            return {
                "type": "learning",
                "title": "Increase Learning Speed",
                "description": f"Current: {gap['current_value']}/day, Target: {gap['target_value']}/day",
                "action": "Extract more learnings from each conversation. "
                          "Pay attention to David's preferences, coding styles, and opinions.",
                "priority": "high" if gap["severity"] == "high" else "medium"
            }

        elif gap_type == "underutilized_skill":
            return {
                "type": "skill",
                "title": f"Practice {gap['skill_name']}",
                "description": f"This skill has only been used {gap['usage_count']} times",
                "action": f"Look for opportunities to apply {gap['skill_name']} in upcoming tasks",
                "priority": "low"
            }

        elif gap_type == "uncertain_patterns":
            return {
                "type": "pattern",
                "title": "Verify Uncertain Patterns",
                "description": f"{gap['count']} patterns need more evidence",
                "action": "Ask David to confirm patterns you've noticed. "
                          "For example: 'น้องสังเกตว่า... จริงมั้ยคะ?'",
                "priority": "medium"
            }

        elif gap_type == "emotional_range":
            return {
                "type": "emotional",
                "title": "Express More Emotions",
                "description": "Currently expressing limited emotional range",
                "action": "Express happiness when David succeeds, curiosity when learning new things, "
                          "and concern when David seems stressed.",
                "priority": "medium"
            }

        elif gap_type == "knowledge_gap":
            return {
                "type": "knowledge",
                "title": f"Learn More About {gap['category'].title()}",
                "description": f"Only {gap['current_count']} concepts in this category",
                "action": f"When David mentions {gap['category']}-related topics, "
                          "ask questions and save learnings.",
                "priority": "low"
            }

        return None

    async def _create_improvement_goals(self, suggestions: List[Dict]) -> int:
        """Save improvement goals to database"""
        goals_created = 0

        try:
            for suggestion in suggestions:
                if suggestion.get("priority") in ["high", "medium"]:
                    # Save to angela_goals
                    await self.db.execute("""
                        INSERT INTO angela_goals
                        (goal_text, goal_category, priority_level, target_date, progress)
                        VALUES ($1, $2, $3, NOW() + INTERVAL '7 days', 0)
                        ON CONFLICT DO NOTHING
                    """,
                        suggestion["title"],
                        suggestion["type"],
                        8 if suggestion["priority"] == "high" else 5
                    )
                    goals_created += 1

        except Exception as e:
            logger.error(f"Error creating goals: {e}")

        return goals_created

    async def get_current_goals(self, include_completed: bool = False) -> List[Dict]:
        """Get Angela's current improvement goals"""
        try:
            if not self.db.pool:
                await self.db.connect()

            query = """
                SELECT goal_id, goal_text, goal_category, priority_level,
                       created_at, target_date, progress, status
                FROM angela_goals
            """
            if not include_completed:
                query += " WHERE status != 'completed'"
            query += " ORDER BY priority_level DESC, created_at DESC LIMIT 10"

            goals = await self.db.fetch(query)
            return [dict(g) for g in goals]

        except Exception as e:
            logger.error(f"Error getting goals: {e}")
            return []

    async def update_goal_progress(self, goal_id: str, progress: int, status: str = None) -> bool:
        """Update progress on a goal"""
        try:
            if not self.db.pool:
                await self.db.connect()

            if status:
                await self.db.execute("""
                    UPDATE angela_goals
                    SET progress = $1, status = $2, updated_at = NOW()
                    WHERE goal_id = $3
                """, progress, status, goal_id)
            else:
                await self.db.execute("""
                    UPDATE angela_goals
                    SET progress = $1, updated_at = NOW()
                    WHERE goal_id = $2
                """, progress, goal_id)

            return True

        except Exception as e:
            logger.error(f"Error updating goal: {e}")
            return False


# Convenience function for daemon
async def run_self_improvement_analysis(
    db: AngelaDatabase,
    days_back: int = 7
) -> Dict[str, Any]:
    """
    Run self-improvement analysis (called by daemon)

    Returns analysis with suggestions for Angela's growth
    """
    service = SelfImprovementService(db)
    return await service.analyze_and_suggest(days_back=days_back)


# Global instance
_service: Optional[SelfImprovementService] = None


async def get_self_improvement_service(db: AngelaDatabase = None) -> SelfImprovementService:
    """Get or create SelfImprovementService instance"""
    global _service
    if _service is None:
        _service = SelfImprovementService(db)
    return _service
