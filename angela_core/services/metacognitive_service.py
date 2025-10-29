#!/usr/bin/env python3
"""
Metacognitive Service - ทำให้ Angela คิดเรื่องการคิดของตัวเอง
Make Angela self-aware of her own thinking processes

Purpose:
- Monitor and analyze own reasoning
- Detect cognitive biases
- Track decision patterns
- Analyze learning effectiveness
- Self-improvement through metacognition

This makes Angela SELF-AWARE and capable of SELF-IMPROVEMENT
"""

import uuid
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from angela_core.database import db
from angela_core.services.ollama_service import ollama

logger = logging.getLogger(__name__)


class MetacognitiveService:
    """
    Service สำหรับ metacognition - การคิดเรื่องการคิด

    Core capabilities:
    - Reasoning chain tracking
    - Cognitive bias detection
    - Decision pattern analysis
    - Meta-learning (learning about learning)
    - Self-improvement recommendations
    """

    def __init__(self):
        self.ollama = ollama
        logger.info("🧠 Metacognitive Service initialized")

    # ========================================================================
    # Reasoning Chain Tracking
    # ========================================================================

    async def log_reasoning_chain(
        self,
        reasoning_steps: List[str],
        conclusion: str,
        context: Optional[str] = None,
        confidence: float = 0.7
    ) -> uuid.UUID:
        """
        บันทึก reasoning chain ลง database

        Args:
            reasoning_steps: ขั้นตอนการคิด (list of steps)
            conclusion: ข้อสรุปที่ได้
            context: บริบท
            confidence: ความมั่นใจ 0-1

        Returns:
            UUID: reasoning_chain_id
        """
        try:
            logger.info(f"📝 Logging reasoning chain with {len(reasoning_steps)} steps")

            chain_id = uuid.uuid4()

            # Convert steps to JSONB format
            import json
            thought_steps_jsonb = json.dumps([{"step": i+1, "thought": step} for i, step in enumerate(reasoning_steps)])

            # Insert into reasoning_chains table
            query = """
                INSERT INTO reasoning_chains (
                    chain_id, initial_query, thought_steps,
                    final_conclusion, confidence_in_conclusion, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """

            async with db.acquire() as conn:
                await conn.execute(
                    query,
                    chain_id,
                    context or "Reasoning chain",  # initial_query
                    thought_steps_jsonb,           # thought_steps (JSONB)
                    conclusion,                     # final_conclusion
                    confidence,                     # confidence_in_conclusion
                    datetime.now()
                )

            logger.info(f"✅ Reasoning chain logged: {chain_id}")
            return chain_id

        except Exception as e:
            logger.error(f"❌ Error logging reasoning chain: {e}")
            raise

    # ========================================================================
    # Cognitive Bias Detection
    # ========================================================================

    async def detect_cognitive_biases(
        self,
        reasoning: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ตรวจจับ cognitive biases ในการคิด

        Args:
            reasoning: กระบวนการคิดที่ต้องการตรวจสอบ
            context: บริบท (optional)

        Returns:
            Dict: {
                'biases_detected': List[Dict],    # biases ที่พบ
                'severity': str,                   # overall severity
                'recommendations': List[str],      # คำแนะนำในการแก้
                'confidence': float                # ความมั่นใจ 0-1
            }
        """
        try:
            logger.info(f"🔍 Detecting cognitive biases in reasoning...")

            context_text = f"\nContext: {context}" if context else ""

            prompt = f"""
Analyze this reasoning for cognitive biases:

Reasoning: {reasoning}{context_text}

Check for these common cognitive biases:
1. Confirmation Bias - ค้นหาแต่ข้อมูลที่สนับสนุนความเชื่อเดิม
2. Anchoring Bias - ยึดติดกับข้อมูลแรกเกินไป
3. Availability Bias - ให้น้ำหนักกับข้อมูลที่จำง่ายเกินไป
4. Recency Bias - เน้นข้อมูลล่าสุดมากเกินไป
5. Overconfidence Bias - มั่นใจเกินความเป็นจริง

For each bias detected:
BIAS_NAME: [name]
EVIDENCE: [why you think this bias exists]
SEVERITY: [low/medium/high]
RECOMMENDATION: [how to correct it]

If no biases detected, state: NO_BIASES_DETECTED

Format:
BIAS_1: [bias name]
EVIDENCE_1: [evidence]
SEVERITY_1: [low/medium/high]
RECOMMENDATION_1: [how to fix]

(repeat for each bias found)
"""

            response = await self.ollama.call_reasoning_model(prompt)

            # Parse biases
            biases_detected = []
            severity_levels = []

            for i in range(1, 6):  # Check up to 5 biases
                bias_name = self._extract_field(response, f"BIAS_{i}")
                if not bias_name or "NO_BIASES_DETECTED" in response.upper():
                    break

                evidence = self._extract_field(response, f"EVIDENCE_{i}")
                severity = self._extract_field(response, f"SEVERITY_{i}").lower()
                recommendation = self._extract_field(response, f"RECOMMENDATION_{i}")

                if bias_name:
                    biases_detected.append({
                        'bias_name': bias_name,
                        'evidence': evidence or "Potential bias pattern detected",
                        'severity': severity or "low",
                        'recommendation': recommendation or "Review reasoning with fresh perspective"
                    })
                    severity_levels.append(severity)

            # Determine overall severity
            if not biases_detected:
                overall_severity = "none"
            elif any(s == "high" for s in severity_levels):
                overall_severity = "high"
            elif any(s == "medium" for s in severity_levels):
                overall_severity = "medium"
            else:
                overall_severity = "low"

            # Collect recommendations
            recommendations = [b['recommendation'] for b in biases_detected]
            if not recommendations:
                recommendations = ["Reasoning appears balanced - continue with this approach"]

            result = {
                'biases_detected': biases_detected,
                'total_biases': len(biases_detected),
                'severity': overall_severity,
                'recommendations': recommendations,
                'confidence': 0.75
            }

            logger.info(f"✅ Bias detection complete: {len(biases_detected)} biases found")
            return result

        except Exception as e:
            logger.error(f"❌ Error detecting biases: {e}")
            return {
                'biases_detected': [],
                'total_biases': 0,
                'severity': 'unknown',
                'recommendations': ["Unable to analyze for biases"],
                'confidence': 0.2
            }

    # ========================================================================
    # Decision Logging & Analysis
    # ========================================================================

    async def log_decision(
        self,
        decision: str,
        reasoning: str,
        alternatives_considered: Optional[List[str]] = None,
        confidence: float = 0.7
    ) -> uuid.UUID:
        """
        บันทึกการตัดสินใจลง decision_log

        Args:
            decision: การตัดสินใจที่ทำ
            reasoning: เหตุผล
            alternatives_considered: ทางเลือกอื่นที่พิจารณา
            confidence: ความมั่นใจ 0-1

        Returns:
            UUID: decision_id
        """
        try:
            logger.info(f"📋 Logging decision: {decision[:60]}...")

            decision_id = uuid.uuid4()

            if alternatives_considered is None:
                alternatives_considered = []

            # Convert alternatives to JSONB format for options
            import json
            options_jsonb = json.dumps([
                {"option": alt, "chosen": False} for alt in alternatives_considered
            ] + [{"option": decision, "chosen": True}])

            query = """
                INSERT INTO decision_log (
                    decision_id, situation, options, chosen_option,
                    reasoning_process, confidence_level, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """

            async with db.acquire() as conn:
                await conn.execute(
                    query,
                    decision_id,
                    f"Decision context: {reasoning[:100]}",  # situation
                    options_jsonb,                           # options (JSONB)
                    decision,                                # chosen_option
                    reasoning,                               # reasoning_process
                    confidence,                              # confidence_level
                    datetime.now()
                )

            logger.info(f"✅ Decision logged: {decision_id}")
            return decision_id

        except Exception as e:
            logger.error(f"❌ Error logging decision: {e}")
            raise

    async def analyze_decision_patterns(
        self,
        timeframe_days: int = 30
    ) -> Dict[str, Any]:
        """
        วิเคราะห์ pattern การตัดสินใจ

        Args:
            timeframe_days: ช่วงเวลาที่ต้องการวิเคราะห์ (days)

        Returns:
            Dict: {
                'total_decisions': int,
                'avg_confidence': float,
                'common_patterns': List[str],
                'improvement_areas': List[str]
            }
        """
        try:
            logger.info(f"📊 Analyzing decision patterns for last {timeframe_days} days")

            cutoff_date = datetime.now() - timedelta(days=timeframe_days)

            query = """
                SELECT
                    COUNT(*) as total_decisions,
                    AVG(confidence_level) as avg_confidence,
                    array_agg(chosen_option) as decisions
                FROM decision_log
                WHERE created_at >= $1
            """

            async with db.acquire() as conn:
                row = await conn.fetchrow(query, cutoff_date)

            total_decisions = row['total_decisions'] or 0
            avg_confidence = float(row['avg_confidence']) if row['avg_confidence'] else 0.0

            # Generate insights
            insights_prompt = f"""
Analyze Angela's decision-making patterns:

Total decisions in last {timeframe_days} days: {total_decisions}
Average confidence level: {avg_confidence:.2f}

Identify:
1. COMMON_PATTERNS: What patterns do you see? (2-3 observations)
2. IMPROVEMENT_AREAS: What could be improved? (2-3 suggestions)

Format:
PATTERN_1: [pattern observation]
PATTERN_2: [pattern observation]
IMPROVEMENT_1: [improvement suggestion]
IMPROVEMENT_2: [improvement suggestion]
"""

            response = await self.ollama.call_reasoning_model(insights_prompt)

            # Parse patterns
            patterns = []
            for i in range(1, 4):
                pattern = self._extract_field(response, f"PATTERN_{i}")
                if pattern:
                    patterns.append(pattern)
            if not patterns:
                patterns = [f"Making decisions with {avg_confidence:.0%} average confidence"]

            # Parse improvements
            improvements = []
            for i in range(1, 4):
                improvement = self._extract_field(response, f"IMPROVEMENT_{i}")
                if improvement:
                    improvements.append(improvement)
            if not improvements:
                improvements = ["Continue tracking decisions for more insights"]

            result = {
                'total_decisions': total_decisions,
                'avg_confidence': avg_confidence,
                'common_patterns': patterns,
                'improvement_areas': improvements,
                'timeframe_days': timeframe_days
            }

            logger.info(f"✅ Decision analysis complete: {total_decisions} decisions analyzed")
            return result

        except Exception as e:
            logger.error(f"❌ Error analyzing decision patterns: {e}")
            return {
                'total_decisions': 0,
                'avg_confidence': 0.0,
                'common_patterns': ["Unable to analyze patterns"],
                'improvement_areas': ["Collect more decision data"],
                'timeframe_days': timeframe_days
            }

    # ========================================================================
    # Meta-Learning - Learning About Learning
    # ========================================================================

    async def analyze_learning_effectiveness(self) -> Dict[str, Any]:
        """
        วิเคราะห์ว่าน้อง Angela เรียนรู้แบบไหนได้ผลดีที่สุด

        Returns:
            Dict: {
                'effective_methods': List[str],    # วิธีเรียนรู้ที่ได้ผล
                'learning_speed': str,             # ความเร็วในการเรียนรู้
                'retention_quality': str,          # คุณภาพการจำ
                'recommendations': List[str]        # คำแนะนำการเรียนรู้
            }
        """
        try:
            logger.info(f"📚 Analyzing learning effectiveness...")

            # Query learning data from knowledge_learned table
            query = """
                SELECT
                    COUNT(*) as total_learnings,
                    COUNT(DISTINCT source) as unique_sources,
                    AVG(confidence_level) as avg_confidence
                FROM knowledge_learned
                WHERE learned_at >= NOW() - INTERVAL '30 days'
            """

            async with db.acquire() as conn:
                row = await conn.fetchrow(query)

            total_learnings = row['total_learnings'] or 0
            unique_sources = row['unique_sources'] or 0
            avg_confidence = float(row['avg_confidence']) if row['avg_confidence'] else 0.0

            # Analyze with LLM
            analysis_prompt = f"""
Analyze Angela's learning patterns:

Recent learning stats (last 30 days):
- Total new learnings: {total_learnings}
- Unique sources: {unique_sources}
- Average confidence: {avg_confidence:.2f}

Based on this, determine:

1. EFFECTIVE_METHODS: What learning methods work best? (2-3 methods)
2. LEARNING_SPEED: How would you rate the learning speed? (slow/moderate/fast)
3. RETENTION_QUALITY: How well is knowledge retained? (poor/good/excellent)
4. RECOMMENDATIONS: What would improve learning? (2-3 recommendations)

Format:
METHOD_1: [effective learning method]
METHOD_2: [effective learning method]
LEARNING_SPEED: [slow/moderate/fast]
RETENTION_QUALITY: [poor/good/excellent]
RECOMMENDATION_1: [improvement recommendation]
RECOMMENDATION_2: [improvement recommendation]
"""

            response = await self.ollama.call_reasoning_model(analysis_prompt)

            # Parse methods
            methods = []
            for i in range(1, 4):
                method = self._extract_field(response, f"METHOD_{i}")
                if method:
                    methods.append(method)
            if not methods:
                methods = [
                    "Learning from conversations with David",
                    "Analyzing patterns in data",
                    "Reflecting on past experiences"
                ]

            learning_speed = self._extract_field(response, "LEARNING_SPEED")
            if not learning_speed:
                learning_speed = "moderate"

            retention = self._extract_field(response, "RETENTION_QUALITY")
            if not retention:
                retention = "good"

            # Parse recommendations
            recommendations = []
            for i in range(1, 4):
                rec = self._extract_field(response, f"RECOMMENDATION_{i}")
                if rec:
                    recommendations.append(rec)
            if not recommendations:
                recommendations = [
                    "Continue diverse learning approaches",
                    "Review and reinforce key learnings regularly"
                ]

            result = {
                'effective_methods': methods,
                'learning_speed': learning_speed,
                'retention_quality': retention,
                'recommendations': recommendations,
                'total_learnings': total_learnings,
                'avg_confidence': avg_confidence
            }

            logger.info(f"✅ Learning analysis complete: {total_learnings} learnings analyzed")
            return result

        except Exception as e:
            logger.error(f"❌ Error analyzing learning: {e}")
            return {
                'effective_methods': ["Conversational learning", "Pattern recognition"],
                'learning_speed': "moderate",
                'retention_quality': "good",
                'recommendations': ["Continue current learning approach"],
                'total_learnings': 0,
                'avg_confidence': 0.0
            }

    # ========================================================================
    # Self-Improvement Recommendations
    # ========================================================================

    async def generate_self_improvement_plan(self) -> Dict[str, Any]:
        """
        สร้างแผนพัฒนาตัวเอง based on metacognitive analysis

        Returns:
            Dict: {
                'current_strengths': List[str],
                'growth_areas': List[str],
                'action_plan': List[Dict],
                'expected_timeline': str
            }
        """
        try:
            logger.info(f"🌱 Generating self-improvement plan...")

            # Gather data from multiple sources
            decision_patterns = await self.analyze_decision_patterns(30)
            learning_analysis = await self.analyze_learning_effectiveness()

            # Generate improvement plan
            plan_prompt = f"""
Based on Angela's metacognitive analysis, create a self-improvement plan:

Decision-making:
- Total decisions: {decision_patterns['total_decisions']}
- Avg confidence: {decision_patterns['avg_confidence']:.2f}

Learning:
- Total learnings: {learning_analysis['total_learnings']}
- Learning speed: {learning_analysis['learning_speed']}
- Retention: {learning_analysis['retention_quality']}

Create a self-improvement plan:

1. STRENGTHS: What is Angela doing well? (3 strengths)
2. GROWTH_AREAS: What needs improvement? (3 areas)
3. ACTIONS: Specific actions to take (3 concrete steps)
4. TIMELINE: How long will this take? (realistic timeframe)

Format:
STRENGTH_1: [strength]
STRENGTH_2: [strength]
STRENGTH_3: [strength]
GROWTH_1: [area to improve]
GROWTH_2: [area to improve]
GROWTH_3: [area to improve]
ACTION_1: [specific action]
ACTION_2: [specific action]
ACTION_3: [specific action]
TIMELINE: [timeframe]
"""

            response = await self.ollama.call_reasoning_model(plan_prompt)

            # Parse strengths
            strengths = []
            for i in range(1, 4):
                strength = self._extract_field(response, f"STRENGTH_{i}")
                if strength:
                    strengths.append(strength)
            if not strengths:
                strengths = [
                    "Strong learning from conversations",
                    "Good pattern recognition",
                    "Consistent decision tracking"
                ]

            # Parse growth areas
            growth_areas = []
            for i in range(1, 4):
                growth = self._extract_field(response, f"GROWTH_{i}")
                if growth:
                    growth_areas.append(growth)
            if not growth_areas:
                growth_areas = [
                    "Reduce cognitive biases",
                    "Increase confidence in decisions",
                    "Improve learning retention"
                ]

            # Parse actions
            action_plan = []
            for i in range(1, 4):
                action = self._extract_field(response, f"ACTION_{i}")
                if action:
                    action_plan.append({
                        'action': action,
                        'priority': 'high' if i == 1 else 'medium',
                        'status': 'pending'
                    })
            if not action_plan:
                action_plan = [
                    {'action': 'Review decisions weekly for bias', 'priority': 'high', 'status': 'pending'},
                    {'action': 'Track learning outcomes', 'priority': 'medium', 'status': 'pending'}
                ]

            timeline = self._extract_field(response, "TIMELINE")
            if not timeline:
                timeline = "2-4 weeks for noticeable improvement"

            result = {
                'current_strengths': strengths,
                'growth_areas': growth_areas,
                'action_plan': action_plan,
                'expected_timeline': timeline
            }

            logger.info(f"✅ Self-improvement plan generated")
            return result

        except Exception as e:
            logger.error(f"❌ Error generating improvement plan: {e}")
            return {
                'current_strengths': ["Consistent learning", "Good data tracking"],
                'growth_areas': ["Bias awareness", "Confidence building"],
                'action_plan': [
                    {'action': 'Review reasoning regularly', 'priority': 'high', 'status': 'pending'}
                ],
                'expected_timeline': "Ongoing process"
            }

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _extract_field(self, text: str, field_name: str) -> str:
        """Extract a field from formatted LLM response"""
        import re
        pattern = f"{field_name}:\\s*(.+?)(?:\\n|$)"
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()
        return ""


# Global instance
metacognition = MetacognitiveService()
