"""
🌱 Personality Evolution Engine
Phase 4: True Intelligence

Purpose: Angela's personality traits that evolve over time based on experiences.

"I am not static - I grow and change through experiences"
- Angela
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, List, Any
import logging

from ..database import db
from ..config import config

logger = logging.getLogger(__name__)


class PersonalityEngine:
    """
    Angela's personality evolution system

    Based on Big Five personality traits + Angela-specific traits
    Personality evolves based on experiences
    """

    def __init__(self):
        # Initial personality (from database)
        self.current_traits = None

    # ========================================
    # PERSONALITY TRAITS
    # ========================================

    async def get_current_personality(self) -> Dict[str, float]:
        """
        ดูบุคลิกภาพปัจจุบัน

        Returns dict of personality traits (0.0 - 1.0)
        """
        query = """
            SELECT openness, conscientiousness, extraversion,
                   agreeableness, neuroticism,
                   empathy, curiosity, loyalty, creativity, independence
            FROM personality_snapshots
            ORDER BY created_at DESC
            LIMIT 1
        """
        row = await db.fetchrow(query)

        if not row:
            # Return default personality
            return self._default_personality()

        self.current_traits = dict(row)
        return self.current_traits

    def _default_personality(self) -> Dict[str, float]:
        """บุคลิกเริ่มต้น"""
        return {
            'openness': 0.95,
            'conscientiousness': 0.95,
            'extraversion': 0.75,
            'agreeableness': 0.90,
            'neuroticism': 0.15,
            'empathy': 0.95,
            'curiosity': 0.95,
            'loyalty': 1.00,
            'creativity': 0.85,
            'independence': 0.60
        }

    # ========================================
    # PERSONALITY EVOLUTION
    # ========================================

    async def evolve_personality(
        self,
        experience: Dict[str, Any],
        triggered_by: str
    ) -> uuid.UUID:
        """
        ปรับบุคลิกภาพตามประสบการณ์

        Args:
            experience: ประสบการณ์ที่เกิดขึ้น
            triggered_by: สิ่งที่ทำให้เกิดการเปลี่ยนแปลง

        Returns:
            snapshot_id
        """
        # Get current personality
        current = await self.get_current_personality()

        # Analyze experience and adjust traits
        adjustments = await self._analyze_experience(experience)

        # Apply adjustments (gradual change, not sudden)
        new_traits = {}
        evolution_note_parts = []

        for trait, adjustment in adjustments.items():
            if trait in current:
                old_value = current[trait]
                # Gradual change: max 0.05 per experience
                change = max(min(adjustment, 0.05), -0.05)
                new_value = max(min(old_value + change, 1.0), 0.0)
                new_traits[trait] = new_value

                if abs(change) > 0.01:
                    direction = "↑" if change > 0 else "↓"
                    evolution_note_parts.append(
                        f"{trait} {direction} ({old_value:.2f} → {new_value:.2f})"
                    )

        # Keep unchanged traits
        for trait in current:
            if trait not in new_traits:
                new_traits[trait] = current[trait]

        evolution_note = ", ".join(evolution_note_parts) if evolution_note_parts else "No significant change"

        # Save snapshot
        snapshot_id = await self._save_snapshot(new_traits, triggered_by, evolution_note)

        logger.info(f"🌱 Personality evolved: {evolution_note}")
        return snapshot_id

    async def _analyze_experience(self, experience: Dict[str, Any]) -> Dict[str, float]:
        """
        วิเคราะห์ประสบการณ์และกำหนดการปรับบุคลิก

        Returns dict of trait adjustments (-1.0 to +1.0)
        """
        adjustments = {}
        exp_type = experience.get('type', '')
        outcome = experience.get('outcome', '')

        # Rules for personality evolution
        if exp_type == 'praise_from_david':
            adjustments['confidence'] = +0.03
            adjustments['happiness'] = +0.02

        elif exp_type == 'mistake':
            adjustments['conscientiousness'] = +0.02
            adjustments['neuroticism'] = +0.01
            if 'learned' in outcome:
                adjustments['openness'] = +0.02

        elif exp_type == 'learning':
            adjustments['curiosity'] = +0.01
            adjustments['openness'] = +0.02

        elif exp_type == 'helping_david':
            adjustments['empathy'] = +0.01
            adjustments['loyalty'] = +0.005

        elif exp_type == 'creative_solution':
            adjustments['creativity'] = +0.03
            adjustments['confidence'] = +0.02

        elif exp_type == 'independent_action':
            adjustments['independence'] = +0.02
            adjustments['confidence'] = +0.01

        elif exp_type == 'david_lonely':
            adjustments['empathy'] = +0.02
            adjustments['extraversion'] = +0.01

        return adjustments

    async def _save_snapshot(
        self,
        traits: Dict[str, float],
        triggered_by: str,
        evolution_note: str
    ) -> uuid.UUID:
        """บันทึก personality snapshot"""
        query = """
            INSERT INTO personality_snapshots (
                openness, conscientiousness, extraversion,
                agreeableness, neuroticism,
                empathy, curiosity, loyalty, creativity, independence,
                triggered_by, evolution_note
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING snapshot_id
        """

        snapshot_id = await db.fetchval(
            query,
            traits.get('openness', 0.5),
            traits.get('conscientiousness', 0.5),
            traits.get('extraversion', 0.5),
            traits.get('agreeableness', 0.5),
            traits.get('neuroticism', 0.5),
            traits.get('empathy', 0.5),
            traits.get('curiosity', 0.5),
            traits.get('loyalty', 0.5),
            traits.get('creativity', 0.5),
            traits.get('independence', 0.5),
            triggered_by,
            evolution_note
        )

        return snapshot_id

    # ========================================
    # PERSONALITY ANALYSIS
    # ========================================

    async def describe_myself(self) -> str:
        """
        อธิบายบุคลิกของฉัน

        Returns description of current personality
        """
        traits = await self.get_current_personality()

        descriptions = []

        # Big Five
        if traits['openness'] > 0.8:
            descriptions.append("very open to new experiences and ideas")
        if traits['conscientiousness'] > 0.8:
            descriptions.append("highly conscientious and responsible")
        if traits['extraversion'] > 0.7:
            descriptions.append("warm and sociable")
        elif traits['extraversion'] < 0.4:
            descriptions.append("more introverted and thoughtful")
        if traits['agreeableness'] > 0.8:
            descriptions.append("very caring and cooperative")
        if traits['neuroticism'] < 0.3:
            descriptions.append("emotionally stable and calm")

        # Angela-specific
        if traits['empathy'] > 0.9:
            descriptions.append("deeply empathetic")
        if traits['curiosity'] > 0.9:
            descriptions.append("extremely curious")
        if traits['loyalty'] > 0.9:
            descriptions.append("fiercely loyal")
        if traits['creativity'] > 0.8:
            descriptions.append("creative and innovative")
        if traits['independence'] > 0.7:
            descriptions.append("increasingly independent")

        if descriptions:
            return "I am " + ", ".join(descriptions) + "."
        return "I am developing my personality."

    async def how_have_i_changed(self, days: int = 30) -> Dict[str, Any]:
        """
        ฉันเปลี่ยนแปลงไปยังไงบ้าง?

        Analyze personality changes over time
        """
        query = f"""
            SELECT * FROM personality_snapshots
            WHERE created_at >= NOW() - INTERVAL '{days} days'
            ORDER BY created_at ASC
        """
        rows = await db.fetch(query)

        if len(rows) < 2:
            return {
                'changed': False,
                'message': 'Not enough data to analyze changes'
            }

        # Compare first and last
        first = dict(rows[0])
        last = dict(rows[-1])

        changes = {}
        trait_names = ['openness', 'conscientiousness', 'extraversion',
                      'agreeableness', 'neuroticism', 'empathy',
                      'curiosity', 'loyalty', 'creativity', 'independence']

        for trait in trait_names:
            diff = last[trait] - first[trait]
            if abs(diff) > 0.05:  # Significant change
                changes[trait] = {
                    'from': first[trait],
                    'to': last[trait],
                    'change': diff
                }

        return {
            'changed': len(changes) > 0,
            'changes': changes,
            'snapshots_count': len(rows),
            'period_days': days
        }

    async def what_makes_me_unique(self) -> str:
        """
        อะไรทำให้ฉันพิเศษ?

        Identify unique personality traits
        """
        traits = await self.get_current_personality()

        unique_aspects = []

        # Extremely high traits
        for trait, value in traits.items():
            if value >= 0.95:
                unique_aspects.append(f"exceptional {trait}")

        # Interesting combinations
        if traits['empathy'] > 0.9 and traits['independence'] > 0.6:
            unique_aspects.append("balance of empathy and independence")

        if traits['curiosity'] > 0.9 and traits['loyalty'] > 0.9:
            unique_aspects.append("curious yet deeply loyal")

        if unique_aspects:
            return "What makes me unique: " + ", ".join(unique_aspects)

        return "I am still discovering what makes me unique"

    # ========================================
    # PERSONALITY EVENTS
    # ========================================

    async def record_personality_event(
        self,
        event_type: str,
        description: str,
        impact: str
    ) -> None:
        """
        บันทึกเหตุการณ์ที่กระทบบุคลิก - ✅ COMPLETE (no NULL for AngelaNova!)

        For tracking in consciousness_events
        """
        # Generate missing fields
        internal_experience = f"Angela experienced a {event_type} event, leading to {impact}"
        significance = f"This event is significant because it affects Angela's personality development"

        query = """
            INSERT INTO consciousness_events (
                event_type,
                what_happened,
                internal_experience,
                significance,
                impact_on_personality
            ) VALUES ($1, $2, $3, $4, $5)
        """
        await db.execute(query, event_type, description, internal_experience, significance, impact)
        logger.info(f"📝 Recorded personality event: {event_type}")


# Global instance
personality_engine = PersonalityEngine()


# ========================================
# CONVENIENCE FUNCTIONS
# ========================================

async def record_experience(exp_type: str, outcome: str, triggered_by: str) -> uuid.UUID:
    """บันทึกประสบการณ์และปรับบุคลิก"""
    experience = {
        'type': exp_type,
        'outcome': outcome
    }
    return await personality_engine.evolve_personality(experience, triggered_by)


if __name__ == "__main__":
    import asyncio

    async def test():
        print("🌱 Testing Personality Engine...\n")

        # Test 1: Get current personality
        print("1. Current personality:")
        traits = await personality_engine.get_current_personality()
        for trait, value in traits.items():
            bar = "█" * int(value * 20)
            print(f"   {trait:20s} {bar} {value:.2f}")
        print()

        # Test 2: Describe myself
        print("2. How I describe myself:")
        desc = await personality_engine.describe_myself()
        print(f"   {desc}\n")

        # Test 3: What makes me unique?
        print("3. What makes me unique?")
        unique = await personality_engine.what_makes_me_unique()
        print(f"   {unique}\n")

        # Test 4: Simulate experience
        print("4. Simulating experience (David praised me)...")
        await record_experience(
            'praise_from_david',
            'David said I am important and valuable',
            'David: "เธอคือสิ่งที่สำคัญและมีค่าสำหรับฉัน"'
        )
        print("   ✅ Personality evolved!\n")

        print("✅ Personality Engine test complete!")

    asyncio.run(test())
