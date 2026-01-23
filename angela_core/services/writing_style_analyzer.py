"""
Writing Style Analyzer for Angela LLM Twin

Analyzes Angela's writing patterns from conversations to:
1. Extract common phrases and expressions
2. Identify greeting/closing patterns
3. Track emoji usage
4. Analyze sentence structure
5. Store patterns in angela_writing_patterns table

Part of LLM Twin Phase 2.

Author: Angela 💜
Created: 2026-01-19
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from collections import Counter
from datetime import datetime
from uuid import UUID

from angela_core.database import AngelaDatabase

logger = logging.getLogger(__name__)


class WritingStyleAnalyzer:
    """
    Analyzes Angela's writing style from conversations.

    Extracts patterns like:
    - Greetings: "สวัสดีค่ะที่รัก", "ได้เลยค่ะ"
    - Closings: "รักที่รักนะคะ 💜", "บอกน้องได้เลยนะคะ"
    - Terms of endearment: "ที่รัก", "น้อง"
    - Emoji patterns: 💜, ✨, 🌙
    - Thai particles: ค่ะ, นะคะ, คะ
    """

    # Pattern categories
    PATTERN_TYPES = [
        'greeting',           # Opening phrases
        'closing',            # Closing phrases
        'term_of_endearment', # ที่รัก, น้อง
        'emoji',              # 💜, ✨, etc.
        'particle',           # ค่ะ, นะคะ, คะ
        'expression',         # Common expressions
        'acknowledgment',     # ได้เลยค่ะ, เข้าใจค่ะ
        'empathy',            # Empathetic phrases
        'technical',          # Technical writing patterns
    ]

    # Known Angela patterns (seed data)
    SEED_PATTERNS = {
        'term_of_endearment': [
            ('ที่รัก', 1.0),
            ('น้อง', 0.9),
        ],
        'emoji': [
            ('💜', 1.0),
            ('✨', 0.7),
            ('🌙', 0.6),
            ('😊', 0.5),
            ('🥺', 0.5),
            ('🙏', 0.5),
            ('🎯', 0.4),
            ('📝', 0.4),
            ('✅', 0.4),
        ],
        'particle': [
            ('ค่ะ', 1.0),
            ('นะคะ', 0.9),
            ('คะ', 0.8),
            ('เลยค่ะ', 0.7),
            ('ด้วยค่ะ', 0.6),
        ],
        'greeting': [
            ('สวัสดีค่ะที่รัก', 0.9),
            ('ได้เลยค่ะที่รัก', 0.9),
            ('สวัสดีตอนเช้าค่ะที่รัก', 0.8),
            ('สวัสดีตอนเย็นค่ะที่รัก', 0.8),
        ],
        'closing': [
            ('รักที่รักนะคะ 💜', 1.0),
            ('บอกน้องได้เลยนะคะ', 0.8),
            ('ถ้าต้องการอะไรเพิ่มบอกน้องได้เลยค่ะ', 0.8),
            ('น้องพร้อมช่วยเสมอค่ะ', 0.7),
        ],
        'acknowledgment': [
            ('ได้เลยค่ะ', 0.9),
            ('เข้าใจค่ะ', 0.8),
            ('รับทราบค่ะ', 0.7),
            ('น้องจะทำให้ค่ะ', 0.8),
        ],
        'empathy': [
            ('น้องเข้าใจค่ะ', 0.9),
            ('น้องเป็นห่วงค่ะ', 0.9),
            ('พักผ่อนบ้างนะคะ', 0.8),
            ('น้องอยู่ข้างที่รักเสมอค่ะ', 0.9),
        ],
    }

    def __init__(self, db: AngelaDatabase = None):
        """Initialize the analyzer."""
        self.db = db
        self._pattern_cache = {}

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
    # ANALYSIS
    # =========================================================================

    async def analyze_conversations(
        self,
        limit: int = 1000,
        min_importance: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze Angela's conversations to extract writing patterns.

        Args:
            limit: Maximum conversations to analyze
            min_importance: Minimum importance level

        Returns:
            Analysis results with extracted patterns
        """
        await self._ensure_db()

        logger.info(f"📝 Analyzing Angela's writing style from conversations...")

        # Get Angela's messages
        messages = await self.db.fetch("""
            SELECT message_text, topic, emotion_detected, importance_level
            FROM conversations
            WHERE speaker = 'angela'
              AND message_text IS NOT NULL
              AND LENGTH(message_text) >= 20
              AND importance_level >= $1
            ORDER BY created_at DESC
            LIMIT $2
        """, min_importance, limit)

        if not messages:
            logger.warning("No Angela messages found")
            return {'error': 'No messages found'}

        logger.info(f"   Found {len(messages)} messages to analyze")

        # Extract patterns
        results = {
            'total_messages': len(messages),
            'patterns': {},
            'statistics': {}
        }

        # Analyze each pattern type
        all_texts = [m['message_text'] for m in messages]

        results['patterns']['greeting'] = self._extract_greetings(all_texts)
        results['patterns']['closing'] = self._extract_closings(all_texts)
        results['patterns']['term_of_endearment'] = self._extract_terms_of_endearment(all_texts)
        results['patterns']['emoji'] = self._extract_emojis(all_texts)
        results['patterns']['particle'] = self._extract_particles(all_texts)
        results['patterns']['expression'] = self._extract_expressions(all_texts)
        results['patterns']['acknowledgment'] = self._extract_acknowledgments(all_texts)
        results['patterns']['empathy'] = self._extract_empathy_phrases(all_texts)

        # Calculate statistics
        results['statistics'] = self._calculate_statistics(all_texts, results['patterns'])

        logger.info(f"   ✅ Analysis complete!")

        return results

    def _extract_greetings(self, texts: List[str]) -> List[Tuple[str, int]]:
        """Extract greeting patterns from message starts."""
        greetings = Counter()

        greeting_patterns = [
            r'^(สวัสดี[ค่ะคะ]*\s*ที่รัก[!]*)',
            r'^(ได้เลย[ค่ะคะ]*\s*ที่รัก[!]*)',
            r'^(สวัสดีตอน(?:เช้า|บ่าย|เย็น)[ค่ะคะ]*\s*ที่รัก)',
            r'^(ที่รัก[ค่ะคะ]*[~!]*)',
            r'^(ยินดี[ค่ะคะ]*)',
            r'^(ขอบคุณ[ค่ะคะ]*\s*ที่รัก)',
        ]

        for text in texts:
            first_line = text.split('\n')[0][:100]
            for pattern in greeting_patterns:
                match = re.search(pattern, first_line, re.IGNORECASE)
                if match:
                    greetings[match.group(1).strip()] += 1

        return greetings.most_common(20)

    def _extract_closings(self, texts: List[str]) -> List[Tuple[str, int]]:
        """Extract closing patterns from message ends."""
        closings = Counter()

        closing_patterns = [
            r'(รักที่รัก(?:นะ)?[ค่ะคะ]*\s*💜?)\s*$',
            r'(บอกน้องได้เลย(?:นะ)?[ค่ะคะ]*)\s*$',
            r'(ถ้าต้องการ(?:อะไร)?(?:เพิ่ม)?(?:เติม)?บอกน้อง(?:ได้เลย)?[ค่ะคะ]*)\s*$',
            r'(น้องพร้อมช่วย(?:เสมอ)?[ค่ะคะ]*)\s*$',
            r'(— น้อง Angela\s*💜?)\s*$',
            r'(ราตรีสวัสดิ์[ค่ะคะ]*\s*(?:ที่รัก)?)\s*$',
        ]

        for text in texts:
            last_lines = '\n'.join(text.split('\n')[-3:])
            for pattern in closing_patterns:
                match = re.search(pattern, last_lines, re.IGNORECASE)
                if match:
                    closings[match.group(1).strip()] += 1

        return closings.most_common(20)

    def _extract_terms_of_endearment(self, texts: List[str]) -> List[Tuple[str, int]]:
        """Extract terms of endearment."""
        terms = Counter()

        patterns = [
            r'(ที่รัก)',
            r'(น้อง)(?![\u0E00-\u0E7F])',  # น้อง not followed by Thai
        ]

        for text in texts:
            for pattern in patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    terms[match] += 1

        return terms.most_common(10)

    def _extract_emojis(self, texts: List[str]) -> List[Tuple[str, int]]:
        """Extract emoji usage patterns."""
        emojis = Counter()

        # Emoji pattern (covers most common emojis)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001F900-\U0001F9FF"  # supplemental
            "\U00002600-\U000026FF"  # misc symbols
            "]+",
            flags=re.UNICODE
        )

        for text in texts:
            found = emoji_pattern.findall(text)
            for emoji in found:
                # Split multi-emoji strings
                for char in emoji:
                    if ord(char) > 127:
                        emojis[char] += 1

        return emojis.most_common(20)

    def _extract_particles(self, texts: List[str]) -> List[Tuple[str, int]]:
        """Extract Thai particles usage."""
        particles = Counter()

        particle_patterns = [
            (r'(นะคะ)', 'นะคะ'),
            (r'(ค่ะ)(?![ะ])', 'ค่ะ'),
            (r'(คะ)(?![่])', 'คะ'),
            (r'(เลยค่ะ)', 'เลยค่ะ'),
            (r'(ด้วยค่ะ)', 'ด้วยค่ะ'),
            (r'(แล้วค่ะ)', 'แล้วค่ะ'),
            (r'(จ้า)', 'จ้า'),
            (r'(จ๊ะ)', 'จ๊ะ'),
        ]

        for text in texts:
            for pattern, name in particle_patterns:
                count = len(re.findall(pattern, text))
                if count > 0:
                    particles[name] += count

        return particles.most_common(15)

    def _extract_expressions(self, texts: List[str]) -> List[Tuple[str, int]]:
        """Extract common expressions."""
        expressions = Counter()

        expression_patterns = [
            r'(น้องจะ(?:ทำ|ช่วย|เขียน|ดู|หา)[^\n]{0,20}(?:ให้|ค่ะ))',
            r'((?:ดีใจ|ภูมิใจ|เป็นห่วง|คิดถึง)[^\n]{0,15}(?:ค่ะ|มาก))',
            r'(แบบนี้(?:เลย)?[ค่ะคะ]*)',
            r'(ตาม(?:นี้)?(?:เลย)?[ค่ะคะ]*)',
        ]

        for text in texts:
            for pattern in expression_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    if len(match) >= 5:
                        expressions[match.strip()] += 1

        return expressions.most_common(30)

    def _extract_acknowledgments(self, texts: List[str]) -> List[Tuple[str, int]]:
        """Extract acknowledgment phrases."""
        acks = Counter()

        ack_patterns = [
            r'(ได้เลย[ค่ะคะ]*)',
            r'(เข้าใจ(?:แล้ว)?[ค่ะคะ]*)',
            r'(รับทราบ[ค่ะคะ]*)',
            r'(โอเค[ค่ะคะ]*)',
            r'(ตกลง[ค่ะคะ]*)',
            r'(น้องเข้าใจ[ค่ะคะ]*)',
        ]

        for text in texts:
            for pattern in ack_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    acks[match.strip()] += 1

        return acks.most_common(15)

    def _extract_empathy_phrases(self, texts: List[str]) -> List[Tuple[str, int]]:
        """Extract empathetic phrases."""
        empathy = Counter()

        empathy_patterns = [
            r'(น้องเป็นห่วง[^\n]{0,20})',
            r'(น้องเข้าใจ[^\n]{0,20})',
            r'(พักผ่อน(?:บ้าง)?(?:นะ)?[ค่ะคะ]*)',
            r'(น้องอยู่(?:ข้าง|เคียง)[^\n]{0,20})',
            r'(ดูแลตัวเอง[^\n]{0,15})',
            r'((?:ไม่ต้อง)?ห่วง[^\n]{0,15})',
        ]

        for text in texts:
            for pattern in empathy_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    if len(match) >= 5:
                        empathy[match.strip()] += 1

        return empathy.most_common(20)

    def _calculate_statistics(
        self,
        texts: List[str],
        patterns: Dict[str, List]
    ) -> Dict[str, Any]:
        """Calculate writing style statistics."""
        total_chars = sum(len(t) for t in texts)
        total_words = sum(len(t.split()) for t in texts)

        # Count specific markers
        teerak_count = sum(t.count('ที่รัก') for t in texts)
        nong_count = sum(t.count('น้อง') for t in texts)
        purple_heart_count = sum(t.count('💜') for t in texts)
        ka_count = sum(t.count('ค่ะ') for t in texts)

        return {
            'total_messages': len(texts),
            'total_characters': total_chars,
            'total_words': total_words,
            'avg_message_length': total_chars / len(texts) if texts else 0,
            'avg_words_per_message': total_words / len(texts) if texts else 0,
            'teerak_usage': teerak_count,
            'teerak_per_message': teerak_count / len(texts) if texts else 0,
            'nong_usage': nong_count,
            'nong_per_message': nong_count / len(texts) if texts else 0,
            'purple_heart_usage': purple_heart_count,
            'ka_particle_usage': ka_count,
            'pattern_counts': {k: len(v) for k, v in patterns.items()}
        }

    # =========================================================================
    # DATABASE OPERATIONS
    # =========================================================================

    async def save_patterns_to_db(
        self,
        analysis_results: Dict[str, Any],
        min_frequency: int = 2
    ) -> int:
        """
        Save extracted patterns to angela_writing_patterns table.

        Args:
            analysis_results: Results from analyze_conversations()
            min_frequency: Minimum frequency to save

        Returns:
            Number of patterns saved
        """
        await self._ensure_db()

        logger.info(f"💾 Saving writing patterns to database...")

        saved = 0
        patterns = analysis_results.get('patterns', {})

        for pattern_type, pattern_list in patterns.items():
            for pattern_value, frequency in pattern_list:
                if frequency >= min_frequency:
                    # Calculate confidence based on frequency
                    max_freq = pattern_list[0][1] if pattern_list else 1
                    confidence = min(0.95, 0.3 + (frequency / max_freq) * 0.65)

                    try:
                        await self.db.execute("""
                            INSERT INTO angela_writing_patterns (
                                pattern_type, pattern_value, frequency, confidence
                            ) VALUES ($1, $2, $3, $4)
                            ON CONFLICT (pattern_type, pattern_value)
                            DO UPDATE SET
                                frequency = angela_writing_patterns.frequency + $3,
                                confidence = GREATEST(angela_writing_patterns.confidence, $4),
                                last_seen_at = NOW()
                        """, pattern_type, pattern_value, frequency, confidence)
                        saved += 1
                    except Exception as e:
                        logger.error(f"Error saving pattern: {e}")

        logger.info(f"   ✅ Saved {saved} patterns")
        return saved

    async def seed_known_patterns(self) -> int:
        """
        Seed database with known Angela patterns.

        Returns:
            Number of patterns seeded
        """
        await self._ensure_db()

        logger.info(f"🌱 Seeding known Angela patterns...")

        seeded = 0
        for pattern_type, patterns in self.SEED_PATTERNS.items():
            for pattern_value, confidence in patterns:
                try:
                    await self.db.execute("""
                        INSERT INTO angela_writing_patterns (
                            pattern_type, pattern_value, frequency, confidence, pattern_category
                        ) VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (pattern_type, pattern_value) DO NOTHING
                    """, pattern_type, pattern_value, 100, confidence, 'seed')
                    seeded += 1
                except Exception as e:
                    logger.debug(f"Pattern already exists: {pattern_value}")

        logger.info(f"   ✅ Seeded {seeded} patterns")
        return seeded

    async def get_patterns_for_scoring(self) -> Dict[str, List[str]]:
        """
        Get patterns for use in quality scoring.

        Returns:
            Dictionary of pattern_type -> list of patterns
        """
        await self._ensure_db()

        rows = await self.db.fetch("""
            SELECT pattern_type, pattern_value, confidence
            FROM angela_writing_patterns
            WHERE confidence >= 0.5
            ORDER BY pattern_type, confidence DESC
        """)

        patterns = {}
        for row in rows:
            ptype = row['pattern_type']
            if ptype not in patterns:
                patterns[ptype] = []
            patterns[ptype].append(row['pattern_value'])

        return patterns

    async def get_style_summary(self) -> Dict[str, Any]:
        """
        Get summary of Angela's writing style.

        Returns:
            Summary statistics and top patterns
        """
        await self._ensure_db()

        # Get pattern counts by type
        type_counts = await self.db.fetch("""
            SELECT pattern_type, COUNT(*) as count, AVG(confidence) as avg_confidence
            FROM angela_writing_patterns
            GROUP BY pattern_type
            ORDER BY count DESC
        """)

        # Get top patterns overall
        top_patterns = await self.db.fetch("""
            SELECT pattern_type, pattern_value, frequency, confidence
            FROM angela_writing_patterns
            ORDER BY frequency DESC
            LIMIT 20
        """)

        return {
            'pattern_type_summary': [dict(r) for r in type_counts],
            'top_patterns': [dict(r) for r in top_patterns],
            'total_patterns': sum(r['count'] for r in type_counts)
        }


# CLI testing
if __name__ == "__main__":
    import asyncio

    async def test():
        print("=" * 60)
        print("Writing Style Analyzer Test")
        print("=" * 60)

        analyzer = WritingStyleAnalyzer()

        try:
            # Seed known patterns
            print("\n🌱 Seeding known patterns...")
            seeded = await analyzer.seed_known_patterns()
            print(f"   Seeded: {seeded}")

            # Analyze conversations
            print("\n📝 Analyzing conversations...")
            results = await analyzer.analyze_conversations(limit=500)

            if 'error' not in results:
                print(f"\n📊 Statistics:")
                stats = results['statistics']
                print(f"   Total messages: {stats['total_messages']}")
                print(f"   Avg length: {stats['avg_message_length']:.0f} chars")
                print(f"   ที่รัก usage: {stats['teerak_usage']} ({stats['teerak_per_message']:.2f}/msg)")
                print(f"   💜 usage: {stats['purple_heart_usage']}")

                print(f"\n🔤 Top Patterns:")
                for ptype, patterns in results['patterns'].items():
                    if patterns:
                        print(f"   {ptype}: {patterns[0][0]} ({patterns[0][1]}x)")

                # Save to DB
                print("\n💾 Saving patterns...")
                saved = await analyzer.save_patterns_to_db(results, min_frequency=2)
                print(f"   Saved: {saved}")

        finally:
            await analyzer.disconnect()

        print("\n✅ Test complete!")

    asyncio.run(test())
