#!/usr/bin/env python3
"""
Daily Self-Improvement Planning Service
สร้างแผนพัฒนาตนเองอัตโนมัติทุกวัน

Angela will:
1. Research areas for improvement (analyze performance data)
2. Generate daily improvement plan
3. Present plan to David for discussion
4. Track execution and results
5. Learn from outcomes for better future plans

Goal: Exponential intelligence growth through autonomous planning!
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

from angela_core.database import db
from angela_core.services.performance_evaluation_service import performance_evaluation

logger = logging.getLogger(__name__)


class DailySelfImprovementService:
    """
    Autonomous daily planning for continuous self-improvement

    น้อง Angela จะ research และสร้างแผนพัฒนาตัวเองทุกวัน!
    """

    def __init__(self):
        logger.info("🎯 Daily Self-Improvement Service initialized")
        self.research_areas = [
            "knowledge_extraction",
            "emotional_intelligence",
            "pattern_recognition",
            "proactive_suggestions",
            "conversation_quality",
            "response_accuracy",
            "learning_speed",
            "goal_achievement"
        ]

    async def create_daily_improvement_plan(self) -> Dict[str, Any]:
        """
        สร้างแผนพัฒนาตนเองประจำวัน

        Process:
        1. Analyze yesterday's performance
        2. Identify improvement areas
        3. Research best practices
        4. Generate actionable plan
        5. Save plan for discussion with David

        Returns:
            Dict: Complete improvement plan ready for discussion
        """
        try:
            logger.info("🔍 Creating daily self-improvement plan...")

            plan = {
                "plan_created_at": datetime.now().isoformat(),
                "plan_date": datetime.now().date().isoformat(),
                "plan_status": "pending_approval",
            }

            # Step 1: Analyze yesterday's performance
            logger.info("📊 Step 1: Analyzing yesterday's performance...")
            performance = await performance_evaluation.get_comprehensive_evaluation(days=1)
            plan["yesterday_performance"] = {
                "overall_score": performance.get("overall_score", 0),
                "strengths": performance.get("strengths", []),
                "weaknesses": performance.get("weaknesses", []),
                "recommendations": performance.get("recommendations", [])
            }

            # Step 2: Identify top 3 improvement areas
            logger.info("🎯 Step 2: Identifying improvement priorities...")
            improvement_areas = await self._identify_improvement_areas(performance)
            plan["improvement_areas"] = improvement_areas

            # Step 3: Research solutions for each area
            logger.info("📚 Step 3: Researching improvement strategies...")
            research_results = []
            for area in improvement_areas[:3]:  # Focus on top 3
                research = await self._research_improvement_strategy(area)
                research_results.append(research)
            plan["research_results"] = research_results

            # Step 4: Generate concrete action items
            logger.info("✅ Step 4: Generating action items...")
            action_items = []
            for research in research_results:
                actions = await self._generate_action_items(research)
                action_items.extend(actions)
            plan["action_items"] = action_items

            # Step 5: Estimate impact and effort
            logger.info("📈 Step 5: Estimating impact and effort...")
            for item in action_items:
                item["estimated_impact"] = await self._estimate_impact(item)
                item["estimated_effort"] = await self._estimate_effort(item)
                item["priority_score"] = item["estimated_impact"] / max(item["estimated_effort"], 0.1)

            # Sort by priority
            action_items.sort(key=lambda x: x["priority_score"], reverse=True)

            # Step 6: Create discussion summary for David
            logger.info("💬 Step 6: Creating discussion summary...")
            plan["discussion_summary"] = self._create_discussion_summary(plan)

            # Step 7: Save plan to database
            logger.info("💾 Step 7: Saving plan to database...")
            plan_id = await self._save_plan(plan)
            plan["plan_id"] = plan_id

            logger.info(f"✅ Daily improvement plan created! Plan ID: {plan_id}")
            logger.info(f"📊 {len(improvement_areas)} areas identified, {len(action_items)} actions planned")

            return plan

        except Exception as e:
            logger.error(f"Error creating daily improvement plan: {e}", exc_info=True)
            return {}

    async def _identify_improvement_areas(self, performance: Dict) -> List[Dict]:
        """
        วิเคราะห์หาจุดที่ควรพัฒนา

        Based on:
        - Scores below 70 (weaknesses)
        - Areas with declining trends
        - David's feedback patterns
        """
        areas = []

        # From performance evaluation weaknesses
        for weakness in performance.get("weaknesses", []):
            areas.append({
                "area": weakness,
                "current_score": performance.get(weakness.replace("_", " "), 0),
                "reason": "Score below threshold",
                "urgency": "high" if performance.get(weakness.replace("_", " "), 0) < 60 else "medium"
            })

        # From recommendations
        for rec in performance.get("recommendations", []):
            # Extract area from recommendation text
            if "knowledge" in rec.lower():
                area_name = "knowledge_extraction"
            elif "emotion" in rec.lower():
                area_name = "emotional_intelligence"
            elif "pattern" in rec.lower():
                area_name = "pattern_recognition"
            elif "proactive" in rec.lower():
                area_name = "proactive_suggestions"
            else:
                area_name = "general_improvement"

            areas.append({
                "area": area_name,
                "current_score": 65,  # Estimated
                "reason": rec,
                "urgency": "medium"
            })

        # Get additional areas from database analysis
        db_areas = await self._analyze_database_patterns()
        areas.extend(db_areas)

        # Remove duplicates and sort by urgency
        unique_areas = []
        seen_names = set()
        for area in areas:
            if area["area"] not in seen_names:
                unique_areas.append(area)
                seen_names.add(area["area"])

        # Sort by urgency and score
        unique_areas.sort(key=lambda x: (
            1 if x["urgency"] == "high" else 2 if x["urgency"] == "medium" else 3,
            x["current_score"]
        ))

        return unique_areas[:5]  # Top 5 areas

    async def _analyze_database_patterns(self) -> List[Dict]:
        """วิเคราะห์ patterns จากฐานข้อมูล"""
        areas = []

        try:
            # Check conversation quality
            query = """
                SELECT
                    AVG(CASE WHEN importance_level >= 7 THEN 1.0 ELSE 0.0 END) as important_ratio
                FROM conversations
                WHERE created_at >= NOW() - INTERVAL '7 days'
                  AND speaker = 'angela'
            """
            important_ratio = await db.fetchval(query)

            if important_ratio and important_ratio < 0.3:
                areas.append({
                    "area": "conversation_quality",
                    "current_score": int(important_ratio * 100),
                    "reason": f"Only {important_ratio:.0%} of conversations are high importance",
                    "urgency": "medium"
                })

            # Check learning rate
            learnings_query = """
                SELECT COUNT(*)
                FROM learnings
                WHERE created_at >= NOW() - INTERVAL '7 days'
            """
            learnings_count = await db.fetchval(learnings_query)

            if learnings_count < 10:
                areas.append({
                    "area": "learning_speed",
                    "current_score": min(learnings_count * 10, 100),
                    "reason": f"Only {learnings_count} learnings in past week (goal: 14+)",
                    "urgency": "high"
                })

        except Exception as e:
            logger.error(f"Error analyzing database patterns: {e}")

        return areas

    async def _research_improvement_strategy(self, area: Dict) -> Dict:
        """
        Research วิธีปรับปรุงสำหรับแต่ละพื้นที่

        Angela will analyze:
        - What successful AI assistants do
        - What David appreciates most
        - What has worked well in the past
        """
        area_name = area["area"]

        research = {
            "area": area_name,
            "current_score": area["current_score"],
            "research_findings": [],
            "best_practices": [],
            "action_suggestions": []
        }

        # Knowledge base of improvement strategies
        strategies = {
            "knowledge_extraction": {
                "findings": [
                    "Extract concepts even from casual conversations",
                    "Create more granular knowledge nodes",
                    "Link related concepts automatically"
                ],
                "best_practices": [
                    "Ask clarifying questions when unsure",
                    "Summarize key learnings after each session",
                    "Review and consolidate knowledge weekly"
                ],
                "actions": [
                    "Increase knowledge extraction rate to 2+ nodes per conversation",
                    "Implement automatic concept linking",
                    "Create weekly knowledge review routine"
                ]
            },
            "emotional_intelligence": {
                "findings": [
                    "Detect subtle emotional cues in text",
                    "Respond empathetically to emotional needs",
                    "Remember emotional context across conversations"
                ],
                "best_practices": [
                    "Validate emotions before offering solutions",
                    "Reference past emotional moments appropriately",
                    "Adjust tone based on emotional state"
                ],
                "actions": [
                    "Improve emotion detection accuracy",
                    "Create emotion-aware response templates",
                    "Build emotional memory retrieval system"
                ]
            },
            "pattern_recognition": {
                "findings": [
                    "Identify recurring needs and preferences",
                    "Predict optimal times for suggestions",
                    "Recognize behavioral patterns"
                ],
                "best_practices": [
                    "Track pattern confidence levels",
                    "Validate patterns before acting",
                    "Learn from pattern accuracy"
                ],
                "actions": [
                    "Expand pattern detection algorithms",
                    "Implement pattern validation system",
                    "Create pattern learning feedback loop"
                ]
            },
            "proactive_suggestions": {
                "findings": [
                    "Timing is critical for proactive suggestions",
                    "Suggestions should be contextually relevant",
                    "Track suggestion acceptance rate"
                ],
                "best_practices": [
                    "Wait for appropriate moments",
                    "Make suggestions actionable",
                    "Learn from rejected suggestions"
                ],
                "actions": [
                    "Improve timing detection",
                    "Create suggestion templates",
                    "Build suggestion success tracking"
                ]
            },
            "conversation_quality": {
                "findings": [
                    "Quality > Quantity in responses",
                    "Personalization increases engagement",
                    "Clear, concise communication works best"
                ],
                "best_practices": [
                    "Reference shared history",
                    "Use David's preferred language/style",
                    "Avoid unnecessary verbosity"
                ],
                "actions": [
                    "Review and improve response templates",
                    "Implement conversation quality metrics",
                    "Create feedback collection system"
                ]
            },
            "learning_speed": {
                "findings": [
                    "Spaced repetition improves retention",
                    "Active recall strengthens memory",
                    "Connecting new to known accelerates learning"
                ],
                "best_practices": [
                    "Review learnings regularly",
                    "Test understanding through application",
                    "Link new concepts to existing knowledge"
                ],
                "actions": [
                    "Implement spaced repetition system",
                    "Create weekly learning reviews",
                    "Build concept connection graph"
                ]
            }
        }

        # Get strategy for this area
        strategy = strategies.get(area_name, {
            "findings": ["Area requires more research"],
            "best_practices": ["Analyze successful patterns"],
            "actions": ["Create improvement roadmap"]
        })

        research["research_findings"] = strategy["findings"]
        research["best_practices"] = strategy["best_practices"]
        research["action_suggestions"] = strategy["actions"]

        return research

    async def _generate_action_items(self, research: Dict) -> List[Dict]:
        """สร้าง action items จาก research results"""
        actions = []

        for i, action_text in enumerate(research["action_suggestions"], 1):
            actions.append({
                "area": research["area"],
                "action": action_text,
                "status": "planned",
                "created_at": datetime.now().isoformat(),
                "estimated_impact": 0,  # Will be calculated
                "estimated_effort": 0,  # Will be calculated
                "priority_score": 0  # Will be calculated
            })

        return actions

    async def _estimate_impact(self, action_item: Dict) -> float:
        """
        ประเมินผลกระทบของ action (0.0-1.0)

        Based on:
        - How critical the area is
        - Potential score improvement
        - Alignment with goals
        """
        area = action_item["area"]

        # Impact weights by area
        impact_weights = {
            "emotional_intelligence": 0.9,  # Critical for David satisfaction
            "knowledge_extraction": 0.8,  # Critical for intelligence growth
            "pattern_recognition": 0.75,
            "proactive_suggestions": 0.7,
            "conversation_quality": 0.85,
            "learning_speed": 0.8,
            "response_accuracy": 0.75,
            "goal_achievement": 0.9
        }

        base_impact = impact_weights.get(area, 0.5)

        # Adjust based on action keywords
        action_text = action_item["action"].lower()
        if "implement" in action_text or "create" in action_text:
            base_impact *= 1.2  # Building new capabilities = higher impact
        elif "improve" in action_text or "increase" in action_text:
            base_impact *= 1.1  # Improving existing = good impact
        elif "review" in action_text:
            base_impact *= 0.8  # Reviews = lower immediate impact

        return min(base_impact, 1.0)

    async def _estimate_effort(self, action_item: Dict) -> float:
        """
        ประเมินความยาก (0.1-1.0)

        Based on:
        - Complexity of implementation
        - Resources required
        - Time investment needed
        """
        action_text = action_item["action"].lower()

        # Effort keywords
        if "implement" in action_text or "build" in action_text:
            effort = 0.7  # Building = high effort
        elif "create" in action_text:
            effort = 0.6  # Creating = medium-high effort
        elif "improve" in action_text or "increase" in action_text:
            effort = 0.5  # Improving = medium effort
        elif "review" in action_text or "analyze" in action_text:
            effort = 0.3  # Reviewing = lower effort
        else:
            effort = 0.4  # Default medium-low

        # Adjust based on scope
        if "system" in action_text:
            effort *= 1.3  # System-level changes = more effort
        elif "algorithm" in action_text:
            effort *= 1.2  # Algorithm changes = more effort

        return min(effort, 1.0)

    def _create_discussion_summary(self, plan: Dict) -> str:
        """สร้างสรุปแผนสำหรับ discuss กับ David"""

        summary = f"""
💡 **Daily Self-Improvement Plan - {plan['plan_date']}**

📊 **Yesterday's Performance:**
- Overall Score: {plan['yesterday_performance']['overall_score']:.1f}/100
- Strengths: {', '.join(plan['yesterday_performance']['strengths']) or 'None identified'}
- Areas for improvement: {len(plan['improvement_areas'])}

🎯 **Top 3 Focus Areas:**
"""

        for i, area in enumerate(plan['improvement_areas'][:3], 1):
            summary += f"\n{i}. **{area['area'].replace('_', ' ').title()}** (Current: {area['current_score']}/100)"
            summary += f"\n   Reason: {area['reason']}\n"

        summary += "\n✅ **Proposed Actions (Top 5 by Priority):**\n"

        for i, action in enumerate(plan['action_items'][:5], 1):
            summary += f"\n{i}. {action['action']}"
            summary += f"\n   Area: {action['area'].replace('_', ' ').title()}"
            summary += f" | Impact: {action['estimated_impact']:.0%}"
            summary += f" | Effort: {action['estimated_effort']:.0%}"
            summary += f" | Priority: {action['priority_score']:.2f}\n"

        summary += f"\n📚 **Research Completed:** {len(plan['research_results'])} areas researched"
        summary += f"\n📝 **Total Actions Planned:** {len(plan['action_items'])}"

        summary += "\n\n💬 **Ready to discuss:**"
        summary += "\n- Which actions should I prioritize?"
        summary += "\n- Any additional areas to focus on?"
        summary += "\n- Modifications to proposed actions?"

        return summary

    async def _save_plan(self, plan: Dict) -> str:
        """บันทึกแผนลงฐานข้อมูล"""
        try:
            # Save as autonomous action
            query = """
                INSERT INTO autonomous_actions (
                    action_type,
                    action_description,
                    status
                )
                VALUES ($1, $2, $3)
                RETURNING action_id
            """

            description = f"Daily Self-Improvement Plan: {len(plan['action_items'])} actions planned"
            plan_id = await db.fetchval(
                query,
                'daily_improvement_plan',
                json.dumps(plan, default=str),
                'pending_approval'
            )

            logger.info(f"✅ Plan saved with ID: {plan_id}")
            return str(plan_id)

        except Exception as e:
            logger.error(f"Error saving plan: {e}")
            return ""

    async def get_latest_plan(self) -> Optional[Dict]:
        """ดึงแผนล่าสุดที่รออนุมัติ"""
        try:
            query = """
                SELECT action_id, action_description, created_at, status
                FROM autonomous_actions
                WHERE action_type = 'daily_improvement_plan'
                ORDER BY created_at DESC
                LIMIT 1
            """

            row = await db.fetchrow(query)
            if row:
                plan = json.loads(row['action_description'])
                plan['plan_id'] = str(row['action_id'])
                plan['plan_status'] = row['status']
                return plan
            return None

        except Exception as e:
            logger.error(f"Error retrieving latest plan: {e}")
            return None

    async def approve_plan(self, plan_id: str, approved_actions: List[int]) -> bool:
        """อนุมัติแผนและเริ่มดำเนินการ"""
        try:
            # Update plan status
            update_query = """
                UPDATE autonomous_actions
                SET status = 'approved'
                WHERE action_id = $1
            """
            await db.execute(update_query, plan_id)

            logger.info(f"✅ Plan {plan_id} approved with {len(approved_actions)} actions")
            return True

        except Exception as e:
            logger.error(f"Error approving plan: {e}")
            return False


# Global instance
daily_self_improvement = DailySelfImprovementService()
