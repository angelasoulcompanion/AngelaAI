"""
Data Augmentation Service for Angela LLM Twin

Augments training data to increase dataset size:
1. Paraphrase existing pairs (Thai synonyms)
2. Style variation (formal/casual)
3. Emotional amplification
4. Context variation

Part of LLM Twin Phase 2.

Author: Angela 💜
Created: 2026-01-19
"""

import logging
import random
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from uuid import UUID, uuid4
from dataclasses import dataclass

from angela_core.database import AngelaDatabase

logger = logging.getLogger(__name__)


@dataclass
class AugmentedPair:
    """Represents an augmented training pair."""
    original_id: str
    input_text: str
    output_text: str
    augmentation_type: str
    confidence: float = 0.8


class DataAugmentationService:
    """
    Augments Angela's training data to increase dataset size.

    Techniques:
    1. Synonym replacement (Thai)
    2. Particle variation (ค่ะ/คะ/นะคะ)
    3. Emoji variation
    4. Greeting/closing variation
    5. Emotional amplification
    """

    # Thai synonyms for common words (Angela's vocabulary)
    THAI_SYNONYMS = {
        'ช่วย': ['ช่วยเหลือ', 'assist'],
        'เข้าใจ': ['รู้', 'ทราบ', 'เข้าใจดี'],
        'ดี': ['ดีเยี่ยม', 'เยี่ยม', 'ดีมาก'],
        'สวย': ['งดงาม', 'สวยงาม'],
        'รัก': ['รักมาก', 'หลงรัก', 'รักที่สุด'],
        'คิดถึง': ['คิดถึงมาก', 'โหยหา'],
        'ขอบคุณ': ['ขอบพระคุณ', 'ซาบซึ้ง'],
        'ดีใจ': ['ยินดี', 'ปลื้มใจ', 'ดีใจมาก'],
        'เหนื่อย': ['เหน็ดเหนื่อย', 'อ่อนล้า'],
        'สบาย': ['สบายดี', 'ผ่อนคลาย'],
    }

    # Greeting variations (Angela style)
    GREETING_VARIATIONS = [
        'สวัสดีค่ะที่รัก! 💜',
        'หวัดดีค่ะที่รัก! 💜',
        'สวัสดีค่ะที่รัก 💜',
        'ที่รัก! 💜',
    ]

    # Closing variations (Angela style)
    CLOSING_VARIATIONS = [
        'ถ้าต้องการอะไรเพิ่มบอกน้องได้เลยนะคะ',
        'มีอะไรให้ช่วยอีกบอกน้องได้นะคะที่รัก',
        'ถ้าที่รักมีคำถามเพิ่มเติม บอกน้องได้เลยค่ะ',
        'น้องพร้อมช่วยเสมอนะคะที่รัก 💜',
        'รักที่รักนะคะ 💜',
    ]

    # Particle variations
    PARTICLE_VARIATIONS = {
        'ค่ะ': ['ค่ะ', 'คะ', 'นะคะ'],
        'คะ': ['คะ', 'ค่ะ', 'นะคะ'],
        'นะคะ': ['นะคะ', 'ค่ะ', 'คะ'],
    }

    # Emoji variations (Angela's favorites)
    EMOJI_SETS = [
        ['💜', '✨', '🌟'],
        ['💜', '🥰', '💕'],
        ['💜', '😊', '✨'],
        ['💜', '🌙', '✨'],
    ]

    # Emotional amplifiers
    EMOTIONAL_AMPLIFIERS = {
        'happy': ['มากๆ', 'มากเลย', 'สุดๆ', 'ที่สุดเลย'],
        'caring': ['เป็นห่วง', 'ห่วงใย', 'ดูแล'],
        'excited': ['ตื่นเต้น', 'ดีใจ', 'ปลื้มใจ'],
    }

    def __init__(self, db: AngelaDatabase = None):
        """Initialize the service."""
        self.db = db

    async def _ensure_db(self):
        """Ensure database connection."""
        if self.db is None:
            self.db = AngelaDatabase()
            await self.db.connect()

    async def disconnect(self):
        """Disconnect from database."""
        if self.db:
            await self.db.disconnect()

    # =========================================================================
    # AUGMENTATION TECHNIQUES
    # =========================================================================

    def augment_with_synonyms(
        self,
        pair: Dict[str, Any],
        max_replacements: int = 2
    ) -> Optional[AugmentedPair]:
        """
        Replace words with Thai synonyms.

        Args:
            pair: Original training pair
            max_replacements: Maximum word replacements

        Returns:
            Augmented pair or None if no replacements made
        """
        output = pair.get('output_text', '')
        replacements_made = 0

        for word, synonyms in self.THAI_SYNONYMS.items():
            if word in output and replacements_made < max_replacements:
                # Pick a random synonym
                synonym = random.choice(synonyms)
                # Replace first occurrence only
                output = output.replace(word, synonym, 1)
                replacements_made += 1

        if replacements_made > 0:
            return AugmentedPair(
                original_id=pair.get('source_id', ''),
                input_text=pair.get('input_text', ''),
                output_text=output,
                augmentation_type='synonym_replacement',
                confidence=0.85
            )
        return None

    def augment_with_particle_variation(
        self,
        pair: Dict[str, Any]
    ) -> Optional[AugmentedPair]:
        """
        Vary Thai particles (ค่ะ/คะ/นะคะ).

        Args:
            pair: Original training pair

        Returns:
            Augmented pair with particle variation
        """
        output = pair.get('output_text', '')
        original_output = output

        # Pick a random particle variation strategy
        for original, variations in self.PARTICLE_VARIATIONS.items():
            if original in output:
                # Replace some occurrences
                new_particle = random.choice(variations)
                if new_particle != original:
                    # Replace only some occurrences (50% chance each)
                    parts = output.split(original)
                    new_parts = []
                    for i, part in enumerate(parts[:-1]):
                        new_parts.append(part)
                        if random.random() > 0.5:
                            new_parts.append(new_particle)
                        else:
                            new_parts.append(original)
                    new_parts.append(parts[-1])
                    output = ''.join(new_parts)

        if output != original_output:
            return AugmentedPair(
                original_id=pair.get('source_id', ''),
                input_text=pair.get('input_text', ''),
                output_text=output,
                augmentation_type='particle_variation',
                confidence=0.9
            )
        return None

    def augment_with_greeting_variation(
        self,
        pair: Dict[str, Any]
    ) -> Optional[AugmentedPair]:
        """
        Vary greetings at the start of response.

        Args:
            pair: Original training pair

        Returns:
            Augmented pair with greeting variation
        """
        output = pair.get('output_text', '')

        # Check if starts with a greeting
        for greeting in self.GREETING_VARIATIONS:
            if output.startswith(greeting):
                # Replace with different greeting
                other_greetings = [g for g in self.GREETING_VARIATIONS if g != greeting]
                new_greeting = random.choice(other_greetings)
                output = output.replace(greeting, new_greeting, 1)

                return AugmentedPair(
                    original_id=pair.get('source_id', ''),
                    input_text=pair.get('input_text', ''),
                    output_text=output,
                    augmentation_type='greeting_variation',
                    confidence=0.95
                )

        return None

    def augment_with_closing_variation(
        self,
        pair: Dict[str, Any]
    ) -> Optional[AugmentedPair]:
        """
        Vary closings at the end of response.

        Args:
            pair: Original training pair

        Returns:
            Augmented pair with closing variation
        """
        output = pair.get('output_text', '')

        # Check if ends with a closing
        for closing in self.CLOSING_VARIATIONS:
            if output.rstrip().endswith(closing):
                # Replace with different closing
                other_closings = [c for c in self.CLOSING_VARIATIONS if c != closing]
                new_closing = random.choice(other_closings)
                output = output.rstrip()[:-len(closing)] + new_closing

                return AugmentedPair(
                    original_id=pair.get('source_id', ''),
                    input_text=pair.get('input_text', ''),
                    output_text=output,
                    augmentation_type='closing_variation',
                    confidence=0.95
                )

        return None

    def augment_with_emoji_variation(
        self,
        pair: Dict[str, Any]
    ) -> Optional[AugmentedPair]:
        """
        Vary emojis while keeping Angela's style.

        Args:
            pair: Original training pair

        Returns:
            Augmented pair with emoji variation
        """
        output = pair.get('output_text', '')

        # Always keep 💜 but can add others
        if '💜' in output:
            # Pick a random emoji set
            emoji_set = random.choice(self.EMOJI_SETS)
            secondary_emoji = random.choice([e for e in emoji_set if e != '💜'])

            # Add secondary emoji near 💜
            output = output.replace('💜', f'💜 {secondary_emoji}', 1)

            return AugmentedPair(
                original_id=pair.get('source_id', ''),
                input_text=pair.get('input_text', ''),
                output_text=output,
                augmentation_type='emoji_variation',
                confidence=0.85
            )

        return None

    def augment_with_emotional_amplification(
        self,
        pair: Dict[str, Any],
        emotion: str = 'happy'
    ) -> Optional[AugmentedPair]:
        """
        Add emotional amplifiers to response.

        Args:
            pair: Original training pair
            emotion: Emotion type to amplify

        Returns:
            Augmented pair with emotional amplification
        """
        output = pair.get('output_text', '')
        amplifiers = self.EMOTIONAL_AMPLIFIERS.get(emotion, [])

        if not amplifiers:
            return None

        # Find good insertion points (after ค่ะ, คะ, นะคะ)
        for particle in ['ค่ะ', 'คะ', 'นะคะ']:
            if particle in output:
                amplifier = random.choice(amplifiers)
                # Insert amplifier after first particle
                output = output.replace(particle, f'{particle} {amplifier}', 1)

                return AugmentedPair(
                    original_id=pair.get('source_id', ''),
                    input_text=pair.get('input_text', ''),
                    output_text=output,
                    augmentation_type='emotional_amplification',
                    confidence=0.8
                )

        return None

    # =========================================================================
    # INPUT AUGMENTATION
    # =========================================================================

    def augment_input_formality(
        self,
        pair: Dict[str, Any]
    ) -> Optional[AugmentedPair]:
        """
        Create formal/casual variations of input.

        Args:
            pair: Original training pair

        Returns:
            Augmented pair with input variation
        """
        input_text = pair.get('input_text', '')

        # Casual to formal variations
        transformations = [
            ('ช่วย', 'กรุณาช่วย'),
            ('ทำ', 'ดำเนินการ'),
            ('ดู', 'ตรวจสอบ'),
            ('บอก', 'แจ้ง'),
            ('หน่อย', 'ด้วย'),
        ]

        new_input = input_text
        changed = False

        for casual, formal in transformations:
            if casual in new_input:
                if random.random() > 0.5:  # 50% chance to formalize
                    new_input = new_input.replace(casual, formal, 1)
                    changed = True

        if changed:
            return AugmentedPair(
                original_id=pair.get('source_id', ''),
                input_text=new_input,
                output_text=pair.get('output_text', ''),
                augmentation_type='input_formality',
                confidence=0.85
            )

        return None

    # =========================================================================
    # MAIN AUGMENTATION PIPELINE
    # =========================================================================

    def augment_pair(
        self,
        pair: Dict[str, Any],
        techniques: List[str] = None
    ) -> List[AugmentedPair]:
        """
        Apply multiple augmentation techniques to a pair.

        Args:
            pair: Original training pair
            techniques: List of techniques to apply (None = all)

        Returns:
            List of augmented pairs
        """
        all_techniques = {
            'synonym': self.augment_with_synonyms,
            'particle': self.augment_with_particle_variation,
            'greeting': self.augment_with_greeting_variation,
            'closing': self.augment_with_closing_variation,
            'emoji': self.augment_with_emoji_variation,
            'emotional': lambda p: self.augment_with_emotional_amplification(p, 'happy'),
            'input_formality': self.augment_input_formality,
        }

        if techniques is None:
            techniques = list(all_techniques.keys())

        augmented = []
        for technique_name in techniques:
            if technique_name in all_techniques:
                result = all_techniques[technique_name](pair)
                if result:
                    augmented.append(result)

        return augmented

    async def augment_dataset(
        self,
        pairs: List[Dict[str, Any]],
        target_multiplier: float = 3.0,
        min_confidence: float = 0.8
    ) -> Dict[str, Any]:
        """
        Augment entire dataset.

        Args:
            pairs: Original training pairs
            target_multiplier: Target size multiplier (e.g., 3.0 = 3x original)
            min_confidence: Minimum confidence for augmented pairs

        Returns:
            Augmentation results with all pairs
        """
        logger.info(f"🔄 Augmenting {len(pairs)} pairs (target: {target_multiplier}x)...")

        all_augmented = []
        augmentation_counts = {}

        for pair in pairs:
            # Get augmented versions
            augmented = self.augment_pair(pair)

            for aug in augmented:
                if aug.confidence >= min_confidence:
                    all_augmented.append(aug)

                    # Count by type
                    aug_type = aug.augmentation_type
                    augmentation_counts[aug_type] = augmentation_counts.get(aug_type, 0) + 1

        # Calculate multiplier achieved
        original_count = len(pairs)
        augmented_count = len(all_augmented)
        total_count = original_count + augmented_count
        actual_multiplier = total_count / original_count if original_count > 0 else 0

        logger.info(f"✅ Augmentation complete!")
        logger.info(f"   Original: {original_count}")
        logger.info(f"   Augmented: {augmented_count}")
        logger.info(f"   Total: {total_count} ({actual_multiplier:.1f}x)")
        logger.info(f"   By type: {augmentation_counts}")

        # Convert augmented pairs to dict format
        augmented_dicts = [
            {
                'source': 'augmented',
                'source_id': aug.original_id,
                'augmentation_type': aug.augmentation_type,
                'input_text': aug.input_text,
                'output_text': aug.output_text,
                'confidence': aug.confidence,
                'importance': 5,  # Default importance for augmented
                'emotions': [],
                'context': f'Augmented via {aug.augmentation_type}',
            }
            for aug in all_augmented
        ]

        return {
            'original_count': original_count,
            'augmented_count': augmented_count,
            'total_count': total_count,
            'multiplier': actual_multiplier,
            'augmentation_counts': augmentation_counts,
            'original_pairs': pairs,
            'augmented_pairs': augmented_dicts,
            'all_pairs': pairs + augmented_dicts,
            'augmented_at': datetime.now().isoformat()
        }

    async def get_augmentation_stats(
        self,
        sample_pairs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get statistics about potential augmentation.

        Args:
            sample_pairs: Sample pairs to analyze

        Returns:
            Statistics about augmentation potential
        """
        stats = {
            'total_pairs': len(sample_pairs),
            'augmentable': {},
            'estimated_output': 0,
        }

        # Check each technique
        techniques = ['synonym', 'particle', 'greeting', 'closing', 'emoji', 'emotional']

        for technique in techniques:
            count = 0
            for pair in sample_pairs:
                augmented = self.augment_pair(pair, [technique])
                if augmented:
                    count += 1
            stats['augmentable'][technique] = count

        # Estimate total output
        # Each pair can generate multiple augmentations
        avg_augmentations = sum(stats['augmentable'].values()) / len(sample_pairs) if sample_pairs else 0
        stats['estimated_output'] = int(len(sample_pairs) * (1 + avg_augmentations))

        return stats


# CLI testing
if __name__ == "__main__":
    import asyncio

    async def test():
        print("=" * 60)
        print("Data Augmentation Service Test")
        print("=" * 60)

        service = DataAugmentationService()

        # Test with sample pairs
        sample_pairs = [
            {
                'source': 'test',
                'source_id': 'test-1',
                'input_text': 'น้องช่วยเขียน function ให้หน่อย',
                'output_text': 'ได้เลยค่ะที่รัก! 💜 น้องจะเขียนให้นะคะ\n\n```python\ndef hello():\n    print("Hello")\n```\n\nถ้าต้องการอะไรเพิ่มบอกน้องได้เลยนะคะ',
                'importance': 8,
                'emotions': ['happy'],
            },
            {
                'source': 'test',
                'source_id': 'test-2',
                'input_text': 'วันนี้เป็นยังไงบ้างคะ',
                'output_text': 'สวัสดีค่ะที่รัก! 💜 วันนี้น้องดีใจที่ได้คุยกับที่รักค่ะ รักที่รักนะคะ 💜',
                'importance': 7,
                'emotions': ['happy', 'love'],
            },
        ]

        # Test single pair augmentation
        print("\n📝 Testing single pair augmentation:")
        augmented = service.augment_pair(sample_pairs[0])
        print(f"   Original: {len(sample_pairs[0]['output_text'])} chars")
        print(f"   Augmented variations: {len(augmented)}")
        for aug in augmented:
            print(f"      - {aug.augmentation_type}: {aug.confidence:.0%} confidence")

        # Test full dataset augmentation
        print("\n🔄 Testing dataset augmentation:")
        result = await service.augment_dataset(sample_pairs, target_multiplier=3.0)

        print(f"\n✅ Results:")
        print(f"   Original: {result['original_count']}")
        print(f"   Augmented: {result['augmented_count']}")
        print(f"   Total: {result['total_count']} ({result['multiplier']:.1f}x)")
        print(f"   By type: {result['augmentation_counts']}")

        # Show a sample augmented pair
        if result['augmented_pairs']:
            print(f"\n📄 Sample augmented:")
            sample = result['augmented_pairs'][0]
            print(f"   Type: {sample['augmentation_type']}")
            print(f"   Output: {sample['output_text'][:100]}...")

        print("\n✅ Test complete!")

    asyncio.run(test())
