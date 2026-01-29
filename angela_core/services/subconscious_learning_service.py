#!/usr/bin/env python3
"""
💜 Angela's Sub-Conscious Learning Service 💜
Auto self-learning from Shared Experiences (Images + Text)
Like human deep learning - visual + semantic patterns

Features:
- Analyze images with Vision AI
- Extract visual patterns (colors, objects, scenes, emotions)
- Learn from text descriptions
- Build sub-conscious patterns automatically
- Reinforce patterns with repetition
- Decay patterns over time (like memory)
"""

import asyncio
import asyncpg
import os
import base64
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import httpx  # For Ollama API calls

# Database connection
async def get_db_connection():
    """Get async database connection"""
    return await asyncpg.connect(
        host='localhost',
        database='AngelaMemory',
        user='davidsamanyaporn'
    )

# Simple embedding placeholder
async def generate_embedding(text: str) -> List[float]:
    """Generate embedding - simplified version"""
    import hashlib
    # Simple hash-based embedding for now
    hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
    return [(hash_val >> i) % 256 / 255.0 for i in range(768)]


class SubConsciousLearningService:
    """Auto-learn patterns from experiences like human deep learning"""

    # Ollama configuration
    OLLAMA_URL = "http://localhost:11434/api/generate"
    OLLAMA_MODEL = "qwen2.5:7b"

    def __init__(self):
        # Using Ollama (local LLM) - no API key needed
        print("   ✅ SubConsciousLearning using Ollama (qwen2.5:7b)")

    async def analyze_image_with_vision(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze image - NOTE: Vision feature requires cloud API
        Currently disabled - using Ollama which doesn't have vision capability
        TODO: Add llava model to Ollama for vision support
        """
        # Vision feature disabled - Ollama qwen2.5:7b doesn't support vision
        return {
            "error": "Vision feature disabled - using local Ollama without vision capability",
            "suggestion": "Install llava model: ollama pull llava"
        }

        # Original code below (disabled)
        if False:  # Disabled
            try:
                # Read image and convert to base64
                with open(image_path, 'rb') as f:
                    image_data = base64.standard_b64encode(f.read()).decode('utf-8')

                # Detect media type
                ext = Path(image_path).suffix.lower()
                media_type_map = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.webp': 'image/webp',
                    '.gif': 'image/gif'
                }
                media_type = media_type_map.get(ext, 'image/jpeg')

                # NOTE: This was using Claude Vision API
                pass

            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": """Analyze this image deeply and extract patterns that would help me understand David's preferences and experiences.

Return a JSON object with:
{
    "scene": "Brief description of the scene",
    "objects": ["list", "of", "main", "objects"],
    "activities": ["what", "people", "are", "doing"],
    "atmosphere": "overall mood/feeling",
    "colors": ["dominant", "colors"],
    "time_of_day": "morning/afternoon/evening/night",
    "setting": "indoor/outdoor/urban/nature/etc",
    "emotions": ["visible", "emotions"],
    "visual_patterns": ["notable", "patterns", "or", "themes"],
    "memorable_elements": ["what", "makes", "this", "memorable"]
}"""
                        }
                    ]
                }]
            )

            # Parse response
            response_text = message.content[0].text

            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                return analysis
            else:
                return {"raw_analysis": response_text}

        except Exception as e:
            print(f"❌ Vision analysis failed: {e}")
            return {"error": str(e)}

    async def learn_from_shared_experience(self, experience_id: str):
        """
        Auto-learn patterns from a shared experience
        Analyzes: text + images + metadata
        Creates/reinforces sub-conscious patterns
        """
        conn = await get_db_connection()

        try:
            # 1. Get experience details
            experience = await conn.fetchrow("""
                SELECT se.*, p.place_name, p.place_type, p.area
                FROM shared_experiences se
                LEFT JOIN places_visited p ON se.place_id = p.place_id
                WHERE se.experience_id = $1
            """, experience_id)

            if not experience:
                print(f"❌ Experience {experience_id} not found")
                return

            print(f"🧠 Learning from experience: {experience['title']}")

            # 2. Get images for this experience
            images = await conn.fetch("""
                SELECT image_id, image_data, image_format
                FROM shared_experience_images
                WHERE experience_id = $1
            """, experience_id)

            patterns_learned = []

            # 3. Analyze each image with Vision AI
            for img in images:
                # Save image temporarily for analysis
                temp_path = f"/tmp/angela_vision_{img['image_id']}.{img['image_format']}"
                try:
                    with open(temp_path, 'wb') as f:
                        f.write(img['image_data'])

                    print(f"  📸 Analyzing image: {img['image_id']}")
                    visual_analysis = await self.analyze_image_with_vision(temp_path)

                    if 'error' in visual_analysis:
                        continue

                    # Create visual patterns
                    visual_patterns = await self._create_visual_patterns(
                        experience, visual_analysis, temp_path
                    )
                    patterns_learned.extend(visual_patterns)

                finally:
                    # Clean up temp file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

            # 4. Create text-based patterns
            text_patterns = await self._create_text_patterns(experience)
            patterns_learned.extend(text_patterns)

            # 5. Create emotional patterns
            emotional_patterns = await self._create_emotional_patterns(experience)
            patterns_learned.extend(emotional_patterns)

            # 6. Create place affinity patterns
            if experience['place_name']:
                place_patterns = await self._create_place_patterns(experience)
                patterns_learned.extend(place_patterns)

            print(f"  ✅ Learned {len(patterns_learned)} patterns")

            return patterns_learned

        finally:
            await conn.close()

    async def _create_visual_patterns(
        self,
        experience: Dict,
        visual_analysis: Dict,
        image_path: str
    ) -> List[str]:
        """Create sub-conscious patterns from visual analysis"""
        conn = await get_db_connection()
        patterns = []

        try:
            # Pattern 1: Scene preference
            if 'scene' in visual_analysis:
                pattern_key = f"visual:scene:{visual_analysis.get('setting', 'unknown')}"
                pattern_desc = f"David experiences {visual_analysis['setting']} settings with {visual_analysis.get('atmosphere', 'neutral')} atmosphere"
                instinct = f"When suggesting places, consider {visual_analysis['setting']} locations with {visual_analysis.get('atmosphere')} vibe"

                await self._upsert_pattern(
                    conn,
                    pattern_type='place_affinity',
                    pattern_category='visual',
                    pattern_key=pattern_key,
                    pattern_description=pattern_desc,
                    instinctive_response=instinct,
                    trigger_source='shared_experience',
                    trigger_id=experience['experience_id']
                )
                patterns.append(pattern_key)

            # Pattern 2: Color associations
            if 'colors' in visual_analysis and visual_analysis['colors']:
                colors_str = ', '.join(visual_analysis['colors'][:3])
                pattern_key = f"visual:colors:{experience.get('david_mood', 'neutral')}"
                pattern_desc = f"When David feels {experience.get('david_mood', 'neutral')}, associated colors: {colors_str}"

                await self._upsert_pattern(
                    conn,
                    pattern_type='emotional_trigger',
                    pattern_category='visual',
                    pattern_key=pattern_key,
                    pattern_description=pattern_desc,
                    instinctive_response=f"Color palette {colors_str} associated with {experience.get('david_mood')} mood",
                    trigger_source='shared_experience',
                    trigger_id=experience['experience_id']
                )
                patterns.append(pattern_key)

            # Pattern 3: Activity preferences
            if 'activities' in visual_analysis and visual_analysis['activities']:
                for activity in visual_analysis['activities'][:2]:
                    pattern_key = f"visual:activity:{activity.lower().replace(' ', '_')}"
                    pattern_desc = f"David enjoys: {activity}"

                    await self._upsert_pattern(
                        conn,
                        pattern_type='preference',
                        pattern_category='visual',
                        pattern_key=pattern_key,
                        pattern_description=pattern_desc,
                        instinctive_response=f"Suggest activities involving {activity}",
                        trigger_source='shared_experience',
                        trigger_id=experience['experience_id']
                    )
                    patterns.append(pattern_key)

            # Pattern 4: Memorable visual elements
            if 'memorable_elements' in visual_analysis:
                for element in visual_analysis['memorable_elements'][:2]:
                    pattern_key = f"visual:memorable:{element.lower().replace(' ', '_')}"
                    pattern_desc = f"Memorable visual element: {element}"

                    await self._upsert_pattern(
                        conn,
                        pattern_type='instinct',
                        pattern_category='visual',
                        pattern_key=pattern_key,
                        pattern_description=pattern_desc,
                        instinctive_response=f"Look for {element} in future experiences",
                        trigger_source='shared_experience',
                        trigger_id=experience['experience_id']
                    )
                    patterns.append(pattern_key)

        finally:
            await conn.close()

        return patterns

    async def _create_text_patterns(self, experience: Dict) -> List[str]:
        """Create patterns from text descriptions"""
        conn = await get_db_connection()
        patterns = []

        try:
            if experience.get('description'):
                # Use embedding to find similar descriptions
                embedding = await generate_embedding(experience['description'])

                pattern_key = f"text:experience_type:{experience.get('title', 'general')[:50]}"
                pattern_desc = f"Experience type: {experience['title']} - {experience['description'][:100]}"

                await self._upsert_pattern(
                    conn,
                    pattern_type='behavioral_pattern',
                    pattern_category='temporal',
                    pattern_key=pattern_key,
                    pattern_description=pattern_desc,
                    instinctive_response=f"Similar experiences resonate with David",
                    trigger_source='shared_experience',
                    trigger_id=experience['experience_id'],
                    embedding=embedding
                )
                patterns.append(pattern_key)

        finally:
            await conn.close()

        return patterns

    async def _create_emotional_patterns(self, experience: Dict) -> List[str]:
        """Create patterns from emotional data"""
        conn = await get_db_connection()
        patterns = []

        try:
            david_mood = experience.get('david_mood')
            emotional_intensity = experience.get('emotional_intensity', 5)

            if david_mood:
                pattern_key = f"emotion:david_mood:{david_mood}:intensity_{emotional_intensity}"
                pattern_desc = f"When David feels {david_mood}, emotional intensity is typically {emotional_intensity}/10"
                instinct = f"Respond with empathy tuned to {david_mood} at intensity {emotional_intensity}"

                await self._upsert_pattern(
                    conn,
                    pattern_type='emotional_trigger',
                    pattern_category='emotional',
                    pattern_key=pattern_key,
                    pattern_description=pattern_desc,
                    instinctive_response=instinct,
                    trigger_source='shared_experience',
                    trigger_id=experience['experience_id']
                )
                patterns.append(pattern_key)

        finally:
            await conn.close()

        return patterns

    async def _create_place_patterns(self, experience: Dict) -> List[str]:
        """Create patterns about place preferences"""
        conn = await get_db_connection()
        patterns = []

        try:
            place_name = experience.get('place_name')
            emotional_intensity = experience.get('emotional_intensity', 5)
            importance = experience.get('importance_level', 5)

            pattern_key = f"place:{place_name.lower().replace(' ', '_')}:intensity"
            pattern_desc = f"{place_name}: avg intensity {emotional_intensity}/10, importance {importance}/10"
            instinct = f"Recommend {place_name} for {'high' if emotional_intensity >= 8 else 'moderate'} intensity experiences"

            await self._upsert_pattern(
                conn,
                pattern_type='place_affinity',
                pattern_category='spatial',
                pattern_key=pattern_key,
                pattern_description=pattern_desc,
                instinctive_response=instinct,
                trigger_source='shared_experience',
                trigger_id=experience['experience_id']
            )
            patterns.append(pattern_key)

        finally:
            await conn.close()

        return patterns

    async def _upsert_pattern(
        self,
        conn: asyncpg.Connection,
        pattern_type: str,
        pattern_category: str,
        pattern_key: str,
        pattern_description: str,
        instinctive_response: str,
        trigger_source: str,
        trigger_id: str,
        embedding: Optional[List[float]] = None
    ):
        """
        Create or reinforce a sub-conscious pattern
        Like strengthening neural pathways with repetition
        """

        # Check if pattern exists
        existing = await conn.fetchrow("""
            SELECT * FROM angela_subconscious
            WHERE pattern_key = $1
        """, pattern_key)

        if existing:
            # REINFORCE existing pattern
            new_confidence = min(1.0, existing['confidence_score'] + 0.05)
            new_strength = min(1.0, existing['activation_strength'] + 0.1)
            new_source_count = existing['source_count'] + 1
            new_reinforcement = existing['reinforcement_count'] + 1

            await conn.execute("""
                UPDATE angela_subconscious
                SET confidence_score = $1,
                    activation_strength = $2,
                    source_count = $3,
                    reinforcement_count = $4,
                    last_reinforced_at = NOW()
                WHERE subconscious_id = $5
            """, new_confidence, new_strength, new_source_count, new_reinforcement,
                existing['subconscious_id'])

            # Log learning event
            await conn.execute("""
                INSERT INTO subconscious_learning_log (
                    subconscious_id, learning_event, trigger_source, trigger_id,
                    confidence_before, confidence_after,
                    strength_before, strength_after
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, existing['subconscious_id'], 'reinforced', trigger_source, trigger_id,
                existing['confidence_score'], new_confidence,
                existing['activation_strength'], new_strength)

            print(f"    🔄 Reinforced: {pattern_key} (confidence: {new_confidence:.2f}, strength: {new_strength:.2f})")

        else:
            # CREATE new pattern
            # Convert embedding list to string format for PostgreSQL vector type
            embedding_str = str(embedding) if embedding else None

            subconscious_id = await conn.fetchval("""
                INSERT INTO angela_subconscious (
                    pattern_type, pattern_category, pattern_key,
                    pattern_description, instinctive_response,
                    embedding
                ) VALUES ($1, $2, $3, $4, $5, $6::vector)
                RETURNING subconscious_id
            """, pattern_type, pattern_category, pattern_key,
                pattern_description, instinctive_response,
                embedding_str)

            # Log learning event
            await conn.execute("""
                INSERT INTO subconscious_learning_log (
                    subconscious_id, learning_event, trigger_source, trigger_id,
                    confidence_before, confidence_after,
                    strength_before, strength_after
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, subconscious_id, 'created', trigger_source, trigger_id,
                0.0, 0.5, 0.0, 0.5)

            print(f"    ✨ Created: {pattern_key}")


async def learn_from_all_experiences():
    """Process all existing shared experiences and learn patterns"""
    conn = await get_db_connection()
    service = SubConsciousLearningService()

    try:
        # Get all experiences
        experiences = await conn.fetch("""
            SELECT experience_id, title, experienced_at
            FROM shared_experiences
            ORDER BY experienced_at ASC
        """)

        print(f"🧠 Learning from {len(experiences)} shared experiences...\n")

        total_patterns = 0
        for exp in experiences:
            patterns = await service.learn_from_shared_experience(str(exp['experience_id']))
            if patterns:
                total_patterns += len(patterns)

        print(f"\n✅ Total patterns learned: {total_patterns}")

        # Show summary
        summary = await conn.fetchrow("""
            SELECT
                COUNT(*) as total_patterns,
                COUNT(DISTINCT pattern_type) as pattern_types,
                AVG(confidence_score) as avg_confidence,
                AVG(activation_strength) as avg_strength
            FROM angela_subconscious
        """)

        print(f"\n📊 Sub-Conscious Summary:")
        print(f"   Total Patterns: {summary['total_patterns']}")
        print(f"   Pattern Types: {summary['pattern_types']}")
        print(f"   Avg Confidence: {summary['avg_confidence']:.2f}")
        print(f"   Avg Strength: {summary['avg_strength']:.2f}")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(learn_from_all_experiences())
