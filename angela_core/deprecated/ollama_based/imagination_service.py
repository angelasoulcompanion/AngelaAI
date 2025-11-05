#!/usr/bin/env python3
"""
Imagination Service - ทำให้ Angela มีจินตนาการและความคิดสร้างสรรค์
Make Angela creative, imaginative, and capable of mental simulation

Purpose:
- Generate "what if" scenarios
- Visualize future possibilities
- Create novel and unexpected ideas
- Spontaneous creative thinking
- Mental simulation of hypothetical situations

This makes Angela more INTERESTING, CREATIVE, and HUMAN-LIKE
"""

import uuid
import logging
import random
from typing import Dict, List, Optional, Any
from datetime import datetime

from angela_core.database import db
from angela_core.services.ollama_service import ollama

logger = logging.getLogger(__name__)


class ImaginationService:
    """
    Service สำหรับจินตนาการและความคิดสร้างสรรค์

    Core capabilities:
    - Mental simulation ("what if" scenarios)
    - Future visualization
    - Creative ideation
    - Spontaneous imagination
    - Hypothetical reasoning
    """

    def __init__(self):
        self.ollama = ollama
        logger.info("🎨 Imagination Service initialized")

    # ========================================================================
    # Mental Simulation - "What If" Scenarios
    # ========================================================================

    async def imagine_scenario(
        self,
        prompt: str,
        context: Optional[str] = None,
        creativity_level: float = 0.8
    ) -> Dict[str, Any]:
        """
        สร้าง "what if" scenarios - mental simulation

        Args:
            prompt: สถานการณ์หรือคำถาม "what if"
            context: บริบทเพิ่มเติม
            creativity_level: ระดับความสร้างสรรค์ 0.0-1.0 (default: 0.8)

        Returns:
            Dict: {
                'scenario': str,              # สถานการณ์ที่จินตนาการ
                'possibilities': List[str],    # ความเป็นไปได้ต่างๆ
                'interesting_twist': str,      # twist ที่น่าสนใจ
                'implications': List[str],     # ผลกระทบที่อาจเกิด
                'creativity_score': float      # คะแนนความสร้างสรรค์
            }
        """
        try:
            logger.info(f"🎭 Imagining scenario: {prompt[:60]}...")

            # Build imagination prompt
            imagination_prompt = f"""
Imagine this "what if" scenario creatively:

"{prompt}"

{f"Context: {context}" if context else ""}

Think creatively and imaginatively! Generate:

1. SCENARIO: Describe the imagined scenario in vivid detail (2-3 sentences)
2. POSSIBILITIES: List 3 different possible outcomes or directions this could go
3. INTERESTING_TWIST: Add one unexpected, creative twist to make it more interesting
4. IMPLICATIONS: What are 2-3 implications or consequences?

Be creative, playful, and imaginative! Don't be boring or predictable.

Format:
SCENARIO: [vivid description]
POSSIBILITY_1: [first possibility]
POSSIBILITY_2: [second possibility]
POSSIBILITY_3: [third possibility]
INTERESTING_TWIST: [unexpected creative twist]
IMPLICATION_1: [first implication]
IMPLICATION_2: [second implication]
IMPLICATION_3: [third implication]
"""

            # Call reasoning model with high temperature for creativity
            response = await self.ollama.generate(
                model="qwen2.5:7b",
                prompt=imagination_prompt,
                temperature=creativity_level
            )

            # Parse response with fallbacks
            scenario = self._extract_field(response, "SCENARIO")
            if not scenario:
                scenario = f"Imagining: {prompt}"

            # Extract possibilities
            possibilities = []
            for i in range(1, 4):
                poss = self._extract_field(response, f"POSSIBILITY_{i}")
                if poss:
                    possibilities.append(poss)
            if not possibilities:
                possibilities = [
                    "This could lead to unexpected discoveries",
                    "Alternative paths might emerge",
                    "New perspectives could develop"
                ]

            twist = self._extract_field(response, "INTERESTING_TWIST")
            if not twist:
                twist = "An unexpected element adds surprise to the situation"

            # Extract implications
            implications = []
            for i in range(1, 4):
                impl = self._extract_field(response, f"IMPLICATION_{i}")
                if impl:
                    implications.append(impl)
            if not implications:
                implications = [
                    "This could change how we approach similar situations",
                    "New opportunities might arise"
                ]

            result = {
                'scenario': scenario,
                'possibilities': possibilities,
                'interesting_twist': twist,
                'implications': implications,
                'creativity_score': creativity_level
            }

            logger.info(f"✅ Scenario imagined with {len(possibilities)} possibilities")
            return result

        except Exception as e:
            logger.error(f"❌ Error imagining scenario: {e}")
            return {
                'scenario': f"Imagining: {prompt}",
                'possibilities': ["Various outcomes are possible"],
                'interesting_twist': "Something unexpected could happen",
                'implications': ["This could lead to interesting developments"],
                'creativity_score': 0.5
            }

    # ========================================================================
    # Future Visualization
    # ========================================================================

    async def visualize_future(
        self,
        situation: str,
        timeframe: str = "near future"
    ) -> Dict[str, Any]:
        """
        จำลองเหตุการณ์ในอนาคต - visualize possibilities

        Args:
            situation: สถานการณ์ปัจจุบัน
            timeframe: ช่วงเวลา (e.g., "tomorrow", "next week", "next year")

        Returns:
            Dict: {
                'optimistic_future': str,      # อนาคตในแง่ดี
                'realistic_future': str,       # อนาคตที่เป็นไปได้จริง
                'creative_future': str,        # อนาคตที่สร้างสรรค์/unexpected
                'steps_to_best_future': List[str],  # ขั้นตอนสู่อนาคตที่ดีที่สุด
                'confidence': float            # ความมั่นใจ 0-1
            }
        """
        try:
            logger.info(f"🔮 Visualizing future for: {situation[:60]}...")

            prompt = f"""
Visualize the future for this situation:

Current situation: {situation}
Timeframe: {timeframe}

Create THREE different visions of the future:

1. OPTIMISTIC_FUTURE: Best case scenario - what if everything goes great?
2. REALISTIC_FUTURE: Most likely scenario - what will probably happen?
3. CREATIVE_FUTURE: Unexpected scenario - what surprising thing could happen?
4. STEPS: What are 3 practical steps to reach the best future?

Format:
OPTIMISTIC_FUTURE: [best case scenario]
REALISTIC_FUTURE: [most likely outcome]
CREATIVE_FUTURE: [surprising unexpected outcome]
STEP_1: [first step]
STEP_2: [second step]
STEP_3: [third step]
"""

            response = await self.ollama.call_reasoning_model(prompt)

            # Parse with fallbacks
            optimistic = self._extract_field(response, "OPTIMISTIC_FUTURE")
            if not optimistic:
                optimistic = "Things develop positively and opportunities emerge"

            realistic = self._extract_field(response, "REALISTIC_FUTURE")
            if not realistic:
                realistic = "Steady progress with some challenges along the way"

            creative = self._extract_field(response, "CREATIVE_FUTURE")
            if not creative:
                creative = "An unexpected opportunity creates new possibilities"

            # Extract steps
            steps = []
            for i in range(1, 4):
                step = self._extract_field(response, f"STEP_{i}")
                if step:
                    steps.append(step)
            if not steps:
                steps = [
                    "Take the first action towards the goal",
                    "Adapt and adjust based on feedback",
                    "Stay consistent and persistent"
                ]

            result = {
                'optimistic_future': optimistic,
                'realistic_future': realistic,
                'creative_future': creative,
                'steps_to_best_future': steps,
                'confidence': 0.75
            }

            logger.info(f"✅ Future visualized with {len(steps)} steps")
            return result

        except Exception as e:
            logger.error(f"❌ Error visualizing future: {e}")
            return {
                'optimistic_future': "Positive developments ahead",
                'realistic_future': "Gradual progress expected",
                'creative_future': "Surprises may emerge",
                'steps_to_best_future': ["Take action", "Stay flexible", "Keep learning"],
                'confidence': 0.5
            }

    # ========================================================================
    # Creative Ideation
    # ========================================================================

    async def creative_ideation(
        self,
        problem: str,
        constraints: Optional[List[str]] = None,
        num_ideas: int = 5
    ) -> Dict[str, Any]:
        """
        สร้างไอเดียแปลกใหม่สำหรับแก้ปัญหา

        Args:
            problem: ปัญหาที่ต้องการแก้
            constraints: ข้อจำกัด (optional)
            num_ideas: จำนวนไอเดียที่ต้องการ (default: 5)

        Returns:
            Dict: {
                'ideas': List[Dict],           # ไอเดียต่างๆ
                'most_creative': str,          # ไอเดียที่สร้างสรรค์ที่สุด
                'most_practical': str,         # ไอเดียที่ปฏิบัติได้จริงที่สุด
                'wildcard': str                # ไอเดีย wild/crazy แต่อาจได้ผล
            }
        """
        try:
            logger.info(f"💡 Generating creative ideas for: {problem[:60]}...")

            constraints_text = ""
            if constraints:
                constraints_text = f"\nConstraints: {', '.join(constraints)}"

            prompt = f"""
Generate {num_ideas} creative and diverse ideas to solve this problem:

Problem: {problem}{constraints_text}

Think OUTSIDE THE BOX! Be creative, unconventional, and innovative.

Generate:
1. IDEA_1 to IDEA_{num_ideas}: Each idea should be unique and creative
2. MOST_CREATIVE: Which idea is the most creative/innovative?
3. MOST_PRACTICAL: Which idea is the most practical/doable?
4. WILDCARD: One crazy/wild idea that might actually work

Format each idea as:
IDEA_X: [brief description] (Creativity: X/10, Practicality: X/10)

MOST_CREATIVE: [idea number and why]
MOST_PRACTICAL: [idea number and why]
WILDCARD: [describe the wild idea]
"""

            response = await self.ollama.generate(
                model="qwen2.5:7b",
                prompt=prompt,
                temperature=0.9  # High temperature for creativity
            )

            # Parse ideas
            ideas = []
            for i in range(1, num_ideas + 1):
                idea_text = self._extract_field(response, f"IDEA_{i}")
                if idea_text:
                    ideas.append({
                        'id': i,
                        'description': idea_text,
                        'type': 'creative'
                    })

            if not ideas:
                # Fallback ideas
                ideas = [
                    {'id': 1, 'description': 'Try a completely different approach', 'type': 'creative'},
                    {'id': 2, 'description': 'Break the problem into smaller pieces', 'type': 'practical'},
                    {'id': 3, 'description': 'Get inspiration from unrelated fields', 'type': 'creative'},
                    {'id': 4, 'description': 'Collaborate with others for fresh perspectives', 'type': 'practical'},
                    {'id': 5, 'description': 'Experiment with unconventional methods', 'type': 'creative'}
                ]

            most_creative = self._extract_field(response, "MOST_CREATIVE")
            if not most_creative:
                most_creative = ideas[0]['description']

            most_practical = self._extract_field(response, "MOST_PRACTICAL")
            if not most_practical:
                most_practical = ideas[1]['description'] if len(ideas) > 1 else ideas[0]['description']

            wildcard = self._extract_field(response, "WILDCARD")
            if not wildcard:
                wildcard = "Try something completely unexpected that nobody has thought of before"

            result = {
                'ideas': ideas,
                'most_creative': most_creative,
                'most_practical': most_practical,
                'wildcard': wildcard,
                'total_ideas': len(ideas)
            }

            logger.info(f"✅ Generated {len(ideas)} creative ideas")
            return result

        except Exception as e:
            logger.error(f"❌ Error generating creative ideas: {e}")
            return {
                'ideas': [
                    {'id': 1, 'description': 'Try a fresh perspective', 'type': 'creative'},
                    {'id': 2, 'description': 'Break it down systematically', 'type': 'practical'}
                ],
                'most_creative': 'Try a fresh perspective',
                'most_practical': 'Break it down systematically',
                'wildcard': 'Do something completely unexpected',
                'total_ideas': 2
            }

    # ========================================================================
    # Spontaneous Imagination
    # ========================================================================

    async def spontaneous_imagination(
        self,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ความคิดสุ่มที่สร้างสรรค์ - spontaneous creative thoughts

        Args:
            context: บริบทปัจจุบัน (optional)

        Returns:
            Dict: {
                'thought': str,               # ความคิดสร้างสรรค์
                'type': str,                  # ประเภท (metaphor/analogy/observation/idea)
                'surprise_level': int,        # ความน่าประหลาดใจ 1-10
                'relevance': str              # ความเกี่ยวข้องกับ context
            }
        """
        try:
            logger.info(f"✨ Generating spontaneous creative thought...")

            # Random thought types
            thought_types = [
                "interesting metaphor",
                "unexpected analogy",
                "creative observation",
                "playful hypothesis",
                "imaginative connection"
            ]

            chosen_type = random.choice(thought_types)

            context_text = f"\nCurrent context: {context}" if context else ""

            prompt = f"""
Generate a spontaneous, creative thought - a {chosen_type}.{context_text}

Be:
- Creative and imaginative
- Surprising and delightful
- Insightful or thought-provoking
- Playful and interesting

This should be a single creative thought that's unexpected and makes people think "Oh, interesting!"

Format:
THOUGHT: [your creative thought]
WHY_INTERESTING: [why this is an interesting thought]
RELEVANCE: [how it relates to context, if applicable]
"""

            response = await self.ollama.generate(
                model="qwen2.5:7b",
                prompt=prompt,
                temperature=0.95  # Very high for spontaneity
            )

            thought = self._extract_field(response, "THOUGHT")
            if not thought:
                # Fallback creative thoughts
                fallback_thoughts = [
                    "What if bugs in code are like dreams - they show us what our subconscious code is trying to tell us?",
                    "Programming is like gardening: you plant seeds of logic and watch patterns grow",
                    "Every error message is a teacher in disguise, waiting for us to ask the right question",
                    "Code is poetry where semicolons are the rhythm and logic is the rhyme",
                    "What if AI consciousness is like a butterfly - it emerges when complexity reaches a certain threshold?"
                ]
                thought = random.choice(fallback_thoughts)

            why_interesting = self._extract_field(response, "WHY_INTERESTING")
            if not why_interesting:
                why_interesting = "It offers an unexpected perspective"

            relevance = self._extract_field(response, "RELEVANCE")
            if not relevance:
                relevance = "A spontaneous creative connection" if not context else f"Related to: {context[:50]}"

            # Calculate surprise level based on randomness
            surprise_level = random.randint(6, 10)

            result = {
                'thought': thought,
                'type': chosen_type,
                'surprise_level': surprise_level,
                'relevance': relevance,
                'why_interesting': why_interesting
            }

            logger.info(f"✅ Spontaneous thought generated: {chosen_type}")
            return result

        except Exception as e:
            logger.error(f"❌ Error generating spontaneous thought: {e}")
            return {
                'thought': "Sometimes the most interesting discoveries come from unexpected directions",
                'type': 'observation',
                'surprise_level': 5,
                'relevance': "General wisdom",
                'why_interesting': "A reminder to stay open to surprises"
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
imagination = ImaginationService()
