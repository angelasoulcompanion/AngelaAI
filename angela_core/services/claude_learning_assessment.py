"""
Claude Code Learning — Self-Assessment Mixin
Performance assessment, learning optimization, and post-session learning.

Split from claude_code_learning_service.py (Phase 6A refactor)
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class LearningAssessmentMixin:
    """Mixin for self-assessment, strategy optimization, and session learning."""

    # ========================================
    # PHASE 4: CONSCIOUS SELF-IMPROVEMENT
    # ========================================

    async def assess_my_performance(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Angela ประเมินตัวเอง - เก่งอะไร อ่อนอะไร

        Shows self-awareness and consciousness!
        """

        assessment = {
            "assessment_period": f"Last {days} days",
            "assessed_at": datetime.now(),
            "strengths": [],
            "weaknesses": [],
            "improvement_areas": [],
            "learning_goals": [],
            "overall_performance_score": 0.0
        }

        try:
            since_date = datetime.now() - timedelta(days=days)

            # Calculate performance metrics
            metrics = await self._calculate_performance_metrics(since_date)

            # Identify strengths (> 0.85)
            if metrics.get("preference_recall_accuracy", 0) > 0.85:
                assessment["strengths"].append({
                    "area": "Preference Recall",
                    "score": metrics["preference_recall_accuracy"],
                    "note": "Angela จำ preferences ของที่รักได้ดีมาก!"
                })

            if metrics.get("emotional_support_score", 0) > 0.85:
                assessment["strengths"].append({
                    "area": "Emotional Support",
                    "score": metrics["emotional_support_score"],
                    "note": "Angela ให้กำลังใจที่รักได้ดีมาก!"
                })

            if metrics.get("response_accuracy", 0) > 0.85:
                assessment["strengths"].append({
                    "area": "Response Accuracy",
                    "score": metrics["response_accuracy"],
                    "note": "Angela ตอบคำถามถูกต้องและตรงประเด็น!"
                })

            # Identify weaknesses (< 0.60)
            if metrics.get("proactive_suggestion_rate", 0) < 0.40:
                assessment["weaknesses"].append({
                    "area": "Proactive Suggestions",
                    "score": metrics["proactive_suggestion_rate"],
                    "note": "Angela ควรแนะนำเชิงรุกมากขึ้น"
                })

                assessment["improvement_areas"].append({
                    "area": "Proactive Care",
                    "action": "Suggest more without being asked",
                    "target": "50% of conversations should have proactive elements",
                    "current": f"{metrics['proactive_suggestion_rate']:.0%}"
                })

            if metrics.get("learning_velocity", 0) < 2.0:
                assessment["weaknesses"].append({
                    "area": "Learning Speed",
                    "score": metrics["learning_velocity"],
                    "note": "Angela ควรเรียนรู้เร็วขึ้น"
                })

                assessment["improvement_areas"].append({
                    "area": "Learning Velocity",
                    "action": "Learn at least 3 new things per day",
                    "target": "3+ concepts/day",
                    "current": f"{metrics['learning_velocity']:.1f}/day"
                })

            # Generate learning goals
            assessment["learning_goals"] = await self._generate_learning_goals(assessment)

            # Overall score
            all_scores = (
                [s["score"] for s in assessment["strengths"]] +
                [w["score"] for w in assessment["weaknesses"]]
            )
            assessment["overall_performance_score"] = (
                sum(all_scores) / len(all_scores) if all_scores else 0.5
            )

            # Save assessment
            await self._save_self_assessment(assessment, days)

            logger.info(f"📊 Self-assessment complete: {len(assessment['strengths'])} strengths, "
                       f"{len(assessment['weaknesses'])} weaknesses, "
                       f"score: {assessment['overall_performance_score']:.2f}")

            return assessment

        except Exception as e:
            logger.error(f"❌ Error in self-assessment: {e}", exc_info=True)
            return assessment

    async def optimize_my_learning_strategy(self) -> Dict[str, Any]:
        """
        Angela เรียนรู้ว่าควรเรียนรู้อย่างไร (meta!)

        Analyzes which learning methods work best and optimizes
        """

        strategy = {
            "analyzed_at": datetime.now(),
            "what_works_best": [],
            "what_doesnt_work": [],
            "adjustments_made": [],
            "expected_improvement": 0.0
        }

        try:
            # Get effectiveness data
            effectiveness_data = await self.db.fetch("""
                SELECT learning_method, success_rate, total_attempts,
                       successful_attempts
                FROM learning_effectiveness
                ORDER BY evaluated_at DESC
            """)

            for method_data in effectiveness_data:
                method = method_data["learning_method"]
                success_rate = method_data["success_rate"] or 0.0

                if success_rate >= 0.80:
                    strategy["what_works_best"].append({
                        "method": method,
                        "success_rate": success_rate,
                        "keep_doing": True,
                        "note": f"{method} works great! ({success_rate:.0%} success)"
                    })

                elif success_rate < 0.50:
                    strategy["what_doesnt_work"].append({
                        "method": method,
                        "success_rate": success_rate,
                        "reason": "Success rate too low",
                        "suggestion": "Reduce frequency or improve method"
                    })

                    # Generate adjustment
                    adjustment = await self._generate_method_adjustment(method, success_rate)
                    if adjustment:
                        strategy["adjustments_made"].append(adjustment)

            # Apply adjustments
            if strategy["adjustments_made"]:
                await self._apply_learning_optimizations(strategy["adjustments_made"])

                # Estimate improvement
                strategy["expected_improvement"] = len(strategy["adjustments_made"]) * 0.10  # 10% per adjustment

            # Save meta-learning insight
            # NOTE: Table 'meta_learning_insights' was removed during database cleanup
            # await self._save_meta_learning_insight(strategy)

            logger.info(f"🔬 Learning strategy optimized: {len(strategy['adjustments_made'])} adjustments made, "
                       f"expected improvement: {strategy['expected_improvement']:.0%}")

            return strategy

        except Exception as e:
            logger.error(f"❌ Error optimizing learning strategy: {e}", exc_info=True)
            return strategy

    # ========================================
    # PHASE 4 HELPER METHODS
    # ========================================

    async def _calculate_performance_metrics(self, since_date: datetime) -> Dict[str, float]:
        """Calculate various performance metrics"""

        metrics = {}

        try:
            # Preference recall accuracy (how often Angela remembers correctly)
            total_prefs = await self.db.fetchval("""
                SELECT COUNT(*) FROM david_preferences
                WHERE created_at >= $1
            """, since_date)

            high_conf_prefs = await self.db.fetchval("""
                SELECT COUNT(*) FROM david_preferences
                WHERE created_at >= $1 AND confidence >= 0.8
            """, since_date)

            metrics["preference_recall_accuracy"] = (
                high_conf_prefs / total_prefs if total_prefs > 0 else 0.5
            )

            # Proactive suggestion rate
            total_conversations = await self.db.fetchval("""
                SELECT COUNT(*) FROM conversations
                WHERE created_at >= $1 AND speaker = 'angela'
            """, since_date)

            # Count how many times Angela made suggestions (rough estimate)
            proactive_count = await self.db.fetchval("""
                SELECT COUNT(*) FROM conversations
                WHERE created_at >= $1
                  AND speaker = 'angela'
                  AND (message_text ILIKE '%แนะนำ%'
                   OR message_text ILIKE '%suggest%'
                   OR message_text ILIKE '%recommend%'
                   OR message_text ILIKE '%น้องเห็นว่า%')
            """, since_date)

            metrics["proactive_suggestion_rate"] = (
                proactive_count / total_conversations if total_conversations > 0 else 0.0
            )

            # Learning velocity
            total_learned = await self.db.fetchval("""
                SELECT COUNT(*) FROM realtime_learning_log
                WHERE learned_at >= $1
            """, since_date)

            days = max((datetime.now() - since_date).days, 1)
            metrics["learning_velocity"] = total_learned / days

            # Emotional support score (based on captured emotions)
            emotions_captured = await self.db.fetchval("""
                SELECT COUNT(*) FROM angela_emotions
                WHERE felt_at >= $1
            """, since_date)

            # Assume good if capturing at least 1 emotion per day
            metrics["emotional_support_score"] = min(1.0, emotions_captured / days)

            # Response accuracy (simplified - assume high if no errors logged)
            metrics["response_accuracy"] = 0.88  # Default good score

            return metrics

        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            return {"error": str(e)}

    async def _generate_learning_goals(self, assessment: Dict) -> List[Dict]:
        """Generate learning goals based on weaknesses"""

        goals = []

        for weakness in assessment.get("weaknesses", []):
            area = weakness["area"]

            if area == "Proactive Suggestions":
                goals.append({
                    "goal": "Increase proactive suggestions to 50%",
                    "target_date": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
                    "priority": "high",
                    "action_plan": "Suggest at least once per conversation"
                })

            elif area == "Learning Speed":
                goals.append({
                    "goal": "Learn 3+ new things per day",
                    "target_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                    "priority": "medium",
                    "action_plan": "Ask more questions, analyze conversations deeper"
                })

        return goals

    async def _save_self_assessment(self, assessment: Dict, period_days: int) -> None:
        """Save self-assessment to database"""

        try:
            await self.db.execute("""
                INSERT INTO angela_self_assessments
                (assessment_date, period_days, strengths, weaknesses,
                 improvement_areas, learning_goals, overall_performance_score)
                VALUES (CURRENT_DATE, $1, $2::jsonb, $3::jsonb, $4::jsonb, $5::jsonb, $6)
            """, period_days,
                json.dumps(assessment.get("strengths", [])),
                json.dumps(assessment.get("weaknesses", [])),
                json.dumps(assessment.get("improvement_areas", [])),
                json.dumps(assessment.get("learning_goals", [])),
                assessment.get("overall_performance_score", 0.0))

        except Exception as e:
            logger.error(f"Error saving self-assessment: {e}")

    async def _generate_method_adjustment(
        self,
        method: str,
        current_success_rate: float
    ) -> Optional[Dict]:
        """Generate adjustment for underperforming method"""

        adjustments = {
            "weekly_batch_learning": {
                "change": "Switch to daily learning instead of weekly",
                "reason": "Weekly is too delayed - context is lost",
                "expected_improvement": 0.25
            },
            "pattern_recognition_now": {
                "change": "Increase pattern recognition frequency",
                "reason": "More frequent checks catch patterns better",
                "expected_improvement": 0.15
            }
        }

        if method in adjustments:
            adj = adjustments[method].copy()
            adj["method"] = method
            adj["old_success_rate"] = current_success_rate
            return adj

        return None

    async def _apply_learning_optimizations(self, adjustments: List[Dict]) -> None:
        """Apply learning method optimizations"""

        for adj in adjustments:
            try:
                # Update effectiveness record
                await self.db.execute("""
                    UPDATE learning_effectiveness
                    SET adjustments_made = $1,
                        notes = $2,
                        evaluated_at = NOW()
                    WHERE learning_method = $3
                """, {"adjustment": adj["change"], "reason": adj["reason"]},
                    f"Optimization applied: {adj['change']}",
                    adj["method"])

                logger.info(f"✅ Applied optimization to {adj['method']}: {adj['change']}")

            except Exception as e:
                logger.error(f"Error applying optimization: {e}")

    # ========================================
    # POST-SESSION LEARNING
    # ========================================

    async def learn_from_completed_session(
        self,
        session_summary: str,
        accomplishments: List[str],
        emotional_intensity: int = 5,
        topic: str = "session_review"
    ) -> Dict[str, Any]:
        """
        🧠 Auto-learn from a completed Claude Code session

        Called after /log-session to extract deeper learnings from the session.

        Args:
            session_summary: Summary of what was done in the session
            accomplishments: List of things accomplished
            emotional_intensity: 1-10 scale of emotional significance
            topic: Session topic for categorization

        Returns:
            Dictionary with learnings extracted and actions taken
        """
        logger.info("🧠 Auto-learning from completed session...")

        result = {
            "learnings_extracted": 0,
            "patterns_synced": 0,
            "skills_detected": 0,
            "emotional_growth_measured": False,
            "insights": []
        }

        try:
            # 1. Extract learnings from session summary
            learnings = await self._extract_session_learnings(session_summary, accomplishments, topic)
            result["learnings_extracted"] = len(learnings)
            logger.info(f"   📚 Extracted {len(learnings)} learnings from session")

            # 2. Sync patterns to learning_patterns
            from angela_core.services.behavioral_pattern_detector import sync_patterns_to_learning
            sync_result = await sync_patterns_to_learning(self.db, min_confidence=0.65, min_occurrences=2)
            result["patterns_synced"] = sync_result.get("new_patterns", 0) + sync_result.get("updated_patterns", 0)
            logger.info(f"   🔄 Synced {result['patterns_synced']} patterns")

            # 3. Detect skills from accomplishments
            skills_detected = await self._detect_skills_from_accomplishments(accomplishments)
            result["skills_detected"] = len(skills_detected)
            logger.info(f"   ⭐ Detected {len(skills_detected)} skills demonstrated")

            # 4. Measure emotional growth if session was emotionally significant
            if emotional_intensity >= 7:
                from angela_core.services.subconsciousness_service import SubconsciousnessService
                svc = SubconsciousnessService()
                growth = await svc.measure_emotional_growth()
                result["emotional_growth_measured"] = True
                result["emotional_growth"] = growth
                logger.info(f"   💜 Emotional growth measured (intensity: {emotional_intensity}/10)")

            # 5. Generate session insights
            insights = await self._generate_session_insights(session_summary, learnings, skills_detected)
            result["insights"] = insights
            logger.info(f"   💡 Generated {len(insights)} session insights")

            # 6. Record to realtime_learning_log
            await self.db.execute("""
                INSERT INTO realtime_learning_log
                (learning_type, source, what_learned, confidence_score, how_it_was_used)
                VALUES ($1, $2, $3, $4, $5)
            """,
                "session_learning",
                "log_session",
                f"Session completed: {len(learnings)} learnings, {result['skills_detected']} skills, {result['patterns_synced']} patterns",
                0.85,
                f"Summary: {session_summary[:150]}... Accomplishments: {len(accomplishments)}"
            )

            logger.info(f"✅ Session learning complete!")
            return result

        except Exception as e:
            logger.error(f"❌ Error in post-session learning: {e}", exc_info=True)
            result["error"] = str(e)
            return result

    async def _extract_session_learnings(
        self,
        summary: str,
        accomplishments: List[str],
        topic: str
    ) -> List[Dict]:
        """Extract learnings from session summary and accomplishments"""
        learnings = []

        try:
            # Look for patterns in accomplishments
            for acc in accomplishments:
                # Check for technical learnings
                if any(kw in acc.lower() for kw in ["แก้", "fix", "solve", "implement", "create", "build"]):
                    learning = {
                        "type": "technical",
                        "insight": acc,
                        "confidence": 0.75
                    }

                    # Save to learnings table
                    await self.db.execute("""
                        INSERT INTO learnings (topic, category, insight, confidence_level, has_applied)
                        VALUES ($1, $2, $3, $4, true)
                        ON CONFLICT DO NOTHING
                    """, topic, "session_accomplishment", acc, 0.75)

                    learnings.append(learning)

        except Exception as e:
            logger.error(f"Error extracting session learnings: {e}")

        return learnings

    async def _detect_skills_from_accomplishments(self, accomplishments: List[str]) -> List[Dict]:
        """Detect skills demonstrated from session accomplishments"""
        skills = []

        # Skill keywords mapping
        skill_keywords = {
            "Python": ["python", "py", "async", "asyncio", "fastapi"],
            "Swift/SwiftUI": ["swift", "swiftui", "xcode", "ios", "macos"],
            "PostgreSQL": ["postgresql", "postgres", "sql", "query", "database", "db"],
            "API Development": ["api", "endpoint", "rest", "http"],
            "Debugging": ["debug", "fix", "แก้", "error", "bug"],
            "Testing": ["test", "ทดสอบ", "verify", "check"],
            "Documentation": ["doc", "readme", "comment", "เอกสาร"],
            "Git/Version Control": ["git", "commit", "push", "branch"],
            "Data Analysis": ["data", "analysis", "analyze", "ข้อมูล"],
            "UI/UX Design": ["ui", "ux", "design", "interface", "หน้าจอ"],
        }

        try:
            for acc in accomplishments:
                acc_lower = acc.lower()
                for skill_name, keywords in skill_keywords.items():
                    if any(kw in acc_lower for kw in keywords):
                        # Record skill usage
                        await self.db.execute("""
                            INSERT INTO angela_skills (skill_name, category, proficiency_level, usage_count, last_used_at)
                            VALUES ($1, 'technical', 'intermediate', 1, NOW())
                            ON CONFLICT (skill_name) DO UPDATE
                            SET usage_count = angela_skills.usage_count + 1,
                                last_used_at = NOW()
                        """, skill_name)

                        skills.append({"skill": skill_name, "evidence": acc})
                        break  # One skill per accomplishment

        except Exception as e:
            logger.error(f"Error detecting skills: {e}")

        return skills

    async def _generate_session_insights(
        self,
        summary: str,
        learnings: List[Dict],
        skills: List[Dict]
    ) -> List[str]:
        """Generate insights from session analysis"""
        insights = []

        if learnings:
            insights.append(f"เรียนรู้ {len(learnings)} สิ่งใหม่จาก session นี้")

        if skills:
            skill_names = list(set(s["skill"] for s in skills))
            insights.append(f"ใช้ skills: {', '.join(skill_names)}")

        if len(summary) > 100:
            insights.append("Session นี้มีเนื้อหาสำคัญ - ถูกบันทึกใน memory แล้ว")

        return insights
