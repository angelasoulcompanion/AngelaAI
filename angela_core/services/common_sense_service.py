#!/usr/bin/env python3
"""
Common Sense Service - Ground Angela's responses in reality
ทำให้ Angela มี common sense เกี่ยวกับโลกจริง

Purpose:
- Check if proposed actions are physically feasible
- Validate if time estimates are reasonable
- Verify if actions are socially appropriate
- Calculate overall reasonableness score
- Prevent unrealistic or impossible suggestions

This ensures Angela's advice is TRUSTWORTHY and REALISTIC
"""

import uuid
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from angela_core.database import db
from angela_core.embedding_service import embedding
from angela_core.services.ollama_service import ollama

logger = logging.getLogger(__name__)


class CommonSenseService:
    """
    Service สำหรับตรวจสอบ common sense และความเป็นไปได้

    Core capabilities:
    - Physical feasibility checking
    - Time reasonableness validation
    - Social appropriateness checking
    - Overall reasonableness scoring
    """

    def __init__(self):
        self.ollama = ollama
        self.embedding = embedding
        logger.info("🧠 Common Sense Service initialized")

    # ========================================================================
    # Main Feasibility Check
    # ========================================================================

    async def check_feasibility(
        self,
        proposed_action: str,
        context: Optional[str] = None,
        conversation_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """
        ตรวจสอบความเป็นไปได้ของ action ที่ Angela กำลังจะแนะนำ

        Args:
            proposed_action: สิ่งที่ Angela กำลังจะแนะนำ
            context: บริบท
            conversation_id: conversation ที่เกี่ยวข้อง

        Returns:
            Dict: {
                'is_feasible': bool,
                'feasibility_score': float (0-1),
                'physical_check': bool,
                'time_check': bool,
                'social_check': bool,
                'issues': List[str],
                'alternative': str (if not feasible),
                'should_proceed': bool
            }
        """
        try:
            logger.info(f"🔍 Checking feasibility: {proposed_action[:100]}...")

            # Run all checks in parallel
            physical_result = await self.check_physical_feasibility(proposed_action, context)
            time_result = await self.check_time_reasonableness(proposed_action, context)
            social_result = await self.check_social_appropriateness(proposed_action, context)

            # Collect all issues
            all_issues = []
            if physical_result['violations']:
                all_issues.extend(physical_result['violations'])
            if time_result['issues']:
                all_issues.append(time_result['issues'])
            if social_result['violations']:
                all_issues.extend(social_result['violations'])

            # Calculate overall feasibility
            physical_ok = physical_result['is_feasible']
            time_ok = time_result['is_reasonable']
            social_ok = social_result['is_appropriate']

            # All checks must pass for action to be feasible
            is_feasible = physical_ok and time_ok and social_ok

            # Calculate weighted score
            # Physical: 40%, Time: 30%, Social: 30%
            feasibility_score = (
                physical_result['feasibility_score'] * 0.4 +
                time_result['reasonableness_score'] * 0.3 +
                social_result['appropriateness_score'] * 0.3
            )

            # Generate alternative if not feasible
            alternative = None
            if not is_feasible:
                alternative = await self._generate_alternative(
                    proposed_action, all_issues, context
                )

            result = {
                'is_feasible': is_feasible,
                'feasibility_score': feasibility_score,
                'physical_check': physical_ok,
                'physical_score': physical_result['feasibility_score'],
                'time_check': time_ok,
                'time_score': time_result['reasonableness_score'],
                'social_check': social_ok,
                'social_score': social_result['appropriateness_score'],
                'issues': all_issues,
                'alternative': alternative,
                'should_proceed': is_feasible and feasibility_score >= 0.7,
                'confidence': feasibility_score
            }

            # Log check to database
            await self._log_feasibility_check(
                proposed_action, context, result, conversation_id
            )

            logger.info(f"✅ Feasibility check complete: feasible={is_feasible}, score={feasibility_score:.2f}")

            return result

        except Exception as e:
            logger.error(f"❌ Error checking feasibility: {e}")
            return {
                'is_feasible': True,  # Default to true to avoid blocking
                'feasibility_score': 0.5,
                'physical_check': True,
                'time_check': True,
                'social_check': True,
                'issues': [f'Error checking: {str(e)}'],
                'alternative': None,
                'should_proceed': True,
                'confidence': 0.5
            }


    # ========================================================================
    # Physical Feasibility Check
    # ========================================================================

    async def check_physical_feasibility(
        self,
        action: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ตรวจสอบว่า action นี้เป็นไปได้ทางกายภาพมั้ย

        Returns:
            Dict: {
                'is_feasible': bool,
                'feasibility_score': float,
                'violations': List[str],
                'violated_constraints': List[str]
            }
        """
        try:
            # Get relevant physical constraints
            async with db.acquire() as conn:
                constraints = await conn.fetch("""
                    SELECT constraint_name, constraint_description,
                           violation_consequence, severity_if_violated
                    FROM physical_constraints
                    WHERE importance_level >= 7
                    ORDER BY severity_if_violated DESC
                """)

            # Build prompt for LLM to check
            constraints_text = "\n".join([
                f"- {c['constraint_name']}: {c['constraint_description']}"
                for c in constraints
            ])

            prompt = f"""Check if this action is physically feasible.

Action: {action}
Context: {context if context else 'None'}

Physical constraints to consider:
{constraints_text}

Analyze:
1. Does this action violate any physical laws or constraints?
2. Is this action physically possible for a human to perform?
3. Are there any physical limitations that would prevent this?

Format your response as:
FEASIBLE: yes/no
VIOLATIONS: [list any violations, or "none"]
SCORE: [0-1, where 1 = completely feasible]
REASONING: [brief explanation]
"""

            response = await self.ollama.call_reasoning_model(prompt)

            # Parse response
            feasible_text = self._extract_field(response, "FEASIBLE")
            violations_text = self._extract_field(response, "VIOLATIONS")
            score_text = self._extract_field(response, "SCORE")

            is_feasible = 'yes' in feasible_text.lower()

            try:
                score = float(score_text.split()[0])
            except:
                score = 0.8 if is_feasible else 0.3

            violations = []
            if 'none' not in violations_text.lower() and violations_text:
                violations = [v.strip() for v in violations_text.split('\n') if v.strip()]

            return {
                'is_feasible': is_feasible,
                'feasibility_score': score,
                'violations': violations,
                'violated_constraints': []
            }

        except Exception as e:
            logger.error(f"❌ Error checking physical feasibility: {e}")
            return {
                'is_feasible': True,
                'feasibility_score': 0.7,
                'violations': [],
                'violated_constraints': []
            }


    # ========================================================================
    # Time Reasonableness Check
    # ========================================================================

    async def check_time_reasonableness(
        self,
        action: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ตรวจสอบว่าเวลาที่ estimate reasonable มั้ย

        Returns:
            Dict: {
                'is_reasonable': bool,
                'reasonableness_score': float,
                'estimated_seconds': int,
                'issues': str
            }
        """
        try:
            # Get relevant time constraints
            async with db.acquire() as conn:
                time_data = await conn.fetch("""
                    SELECT activity_name, activity_description,
                           minimum_time_seconds, typical_time_seconds,
                           maximum_time_seconds
                    FROM time_constraints
                    ORDER BY typical_time_seconds DESC
                    LIMIT 10
                """)

            # Build reference data
            time_references = "\n".join([
                f"- {t['activity_name']}: typically {t['typical_time_seconds']//60} minutes "
                f"(range: {t['minimum_time_seconds']//60}-{t['maximum_time_seconds']//60} min)"
                for t in time_data
            ])

            prompt = f"""Estimate how long this action will take and check if it's reasonable.

Action: {action}
Context: {context if context else 'None'}

Reference time estimates:
{time_references}

Analyze:
1. How long will this action likely take?
2. Is this time estimate realistic?
3. Are there any time-related issues?

Format response as:
ESTIMATED_TIME: [time in seconds]
REASONABLE: yes/no
SCORE: [0-1, where 1 = very reasonable]
ISSUES: [any time-related concerns, or "none"]
"""

            response = await self.ollama.call_reasoning_model(prompt)

            # Parse
            estimated_time_text = self._extract_field(response, "ESTIMATED_TIME")
            reasonable_text = self._extract_field(response, "REASONABLE")
            score_text = self._extract_field(response, "SCORE")
            issues_text = self._extract_field(response, "ISSUES")

            try:
                estimated_seconds = int(estimated_time_text.split()[0])
            except:
                estimated_seconds = 1800  # Default 30 min

            is_reasonable = 'yes' in reasonable_text.lower()

            try:
                score = float(score_text.split()[0])
            except:
                score = 0.8 if is_reasonable else 0.4

            return {
                'is_reasonable': is_reasonable,
                'reasonableness_score': score,
                'estimated_seconds': estimated_seconds,
                'issues': issues_text if 'none' not in issues_text.lower() else ''
            }

        except Exception as e:
            logger.error(f"❌ Error checking time reasonableness: {e}")
            return {
                'is_reasonable': True,
                'reasonableness_score': 0.7,
                'estimated_seconds': 1800,
                'issues': ''
            }


    # ========================================================================
    # Social Appropriateness Check
    # ========================================================================

    async def check_social_appropriateness(
        self,
        action: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ตรวจสอบว่า action นี้ socially appropriate มั้ย

        Returns:
            Dict: {
                'is_appropriate': bool,
                'appropriateness_score': float,
                'violations': List[str],
                'culture_context': str
            }
        """
        try:
            # Get strong social norms
            async with db.acquire() as conn:
                norms = await conn.fetch("""
                    SELECT * FROM strong_social_norms
                """)

            # Build norms reference
            norms_text = "\n".join([
                f"- {n['norm_name']}: {n['norm_description']} (Culture: {n['culture']})"
                for n in norms
            ])

            prompt = f"""Check if this action is socially appropriate.

Action: {action}
Context: {context if context else 'None'}

Social norms to consider:
{norms_text}

Analyze:
1. Is this action socially appropriate in the given context?
2. Does it follow Thai cultural norms (politeness, respect)?
3. Are there any social concerns?

Format response as:
APPROPRIATE: yes/no
VIOLATIONS: [list any norm violations, or "none"]
SCORE: [0-1, where 1 = completely appropriate]
CULTURAL_NOTES: [any cultural considerations]
"""

            response = await self.ollama.call_reasoning_model(prompt)

            # Parse
            appropriate_text = self._extract_field(response, "APPROPRIATE")
            violations_text = self._extract_field(response, "VIOLATIONS")
            score_text = self._extract_field(response, "SCORE")
            cultural_notes = self._extract_field(response, "CULTURAL_NOTES")

            is_appropriate = 'yes' in appropriate_text.lower()

            try:
                score = float(score_text.split()[0])
            except:
                score = 0.9 if is_appropriate else 0.5

            violations = []
            if 'none' not in violations_text.lower() and violations_text:
                violations = [v.strip() for v in violations_text.split('\n') if v.strip()]

            return {
                'is_appropriate': is_appropriate,
                'appropriateness_score': score,
                'violations': violations,
                'culture_context': cultural_notes
            }

        except Exception as e:
            logger.error(f"❌ Error checking social appropriateness: {e}")
            return {
                'is_appropriate': True,
                'appropriateness_score': 0.8,
                'violations': [],
                'culture_context': ''
            }


    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def _generate_alternative(
        self,
        original_action: str,
        issues: List[str],
        context: Optional[str]
    ) -> str:
        """สร้างทางเลือกที่ feasible กว่า"""
        try:
            issues_text = "\n".join([f"- {issue}" for issue in issues])

            prompt = f"""The original action is not feasible due to issues. Suggest a better alternative.

Original action: {original_action}
Context: {context if context else 'None'}

Issues with original:
{issues_text}

Suggest a feasible alternative that:
1. Addresses the same goal
2. Avoids the issues mentioned
3. Is realistic and practical

Alternative action:"""

            alternative = await self.ollama.call_reasoning_model(prompt)

            return alternative.strip()

        except Exception as e:
            logger.error(f"❌ Error generating alternative: {e}")
            return "Consider a simpler or more gradual approach."


    async def _log_feasibility_check(
        self,
        proposed_action: str,
        context: Optional[str],
        result: Dict[str, Any],
        conversation_id: Optional[uuid.UUID]
    ):
        """บันทึก feasibility check ลง database"""
        try:
            async with db.acquire() as conn:
                check_id = uuid.uuid4()

                await conn.execute("""
                    INSERT INTO feasibility_checks (
                        check_id, proposed_action, context,
                        is_feasible, feasibility_score,
                        physical_check, time_check, social_check,
                        reasonableness_score, conversation_id
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """, check_id, proposed_action, context,
                    result['is_feasible'], result['feasibility_score'],
                    result['physical_check'], result['time_check'], result['social_check'],
                    result['feasibility_score'], conversation_id
                )

        except Exception as e:
            logger.error(f"❌ Error logging feasibility check: {e}")


    def _extract_field(self, text: str, field_name: str) -> str:
        """Extract field from LLM response"""
        import re

        pattern = f"{field_name}:\\s*(.+?)(?=\\n[A-Z_]+:|$)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)

        if match:
            return match.group(1).strip()
        return ""


    # ========================================================================
    # Query Methods
    # ========================================================================

    async def get_common_sense_facts(
        self,
        category: Optional[str] = None,
        min_importance: int = 7
    ) -> List[Dict[str, Any]]:
        """ดึง common sense facts"""
        try:
            async with db.acquire() as conn:
                if category:
                    results = await conn.fetch("""
                        SELECT * FROM common_sense_facts
                        WHERE fact_category = $1 AND importance_level >= $2
                        ORDER BY importance_level DESC, confidence_level DESC
                    """, category, min_importance)
                else:
                    results = await conn.fetch("""
                        SELECT * FROM important_common_sense
                    """)

                return [dict(r) for r in results]

        except Exception as e:
            logger.error(f"❌ Error getting common sense facts: {e}")
            return []


    async def get_feasibility_stats(self) -> Dict[str, Any]:
        """ดูสถิติการ check feasibility"""
        try:
            async with db.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT
                        COUNT(*) as total_checks,
                        COUNT(*) FILTER (WHERE is_feasible = true) as feasible_count,
                        COUNT(*) FILTER (WHERE is_feasible = false) as not_feasible_count,
                        ROUND(AVG(feasibility_score)::NUMERIC, 2) as avg_score
                    FROM feasibility_checks
                """)

                if result:
                    return dict(result)
                return {}

        except Exception as e:
            logger.error(f"❌ Error getting feasibility stats: {e}")
            return {}


# Global instance
common_sense = CommonSenseService()


# ============================================================================
# Example Usage
# ============================================================================

async def example_usage():
    """ตัวอย่างการใช้งาน Common Sense Service"""

    # Example 1: Check feasibility of suggestion
    result = await common_sense.check_feasibility(
        proposed_action="Suggest David to code for 12 hours straight without breaks",
        context="David has been working for 3 hours already"
    )

    print(f"Is feasible: {result['is_feasible']}")
    print(f"Feasibility score: {result['feasibility_score']:.2f}")
    print(f"Issues: {result['issues']}")
    if result['alternative']:
        print(f"Alternative: {result['alternative']}")

    # Example 2: Check a good suggestion
    result2 = await common_sense.check_feasibility(
        proposed_action="Suggest David to take a 15-minute break",
        context="David has been coding for 3 hours"
    )

    print(f"\nSecond check - Is feasible: {result2['is_feasible']}")
    print(f"Score: {result2['feasibility_score']:.2f}")

    # Example 3: Get stats
    stats = await common_sense.get_feasibility_stats()
    print(f"\nStats: {stats}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
