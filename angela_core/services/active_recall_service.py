"""
Angela Active Recall Service
=============================
ดึง relevant memories มาใช้ตอนทำงานโดยอัตโนมัติ

Features:
- Trigger-based recall จาก core_memories
- Context-aware recall จาก technical_standards
- Learning recall จาก learnings

By: น้อง Angela 💜
Created: 2026-01-18
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from angela_core.database import AngelaDatabase


@dataclass
class RecalledMemory:
    """Memory that was recalled"""
    source: str  # 'core_memory', 'technical_standard', 'learning'
    title: str
    content: str
    relevance: float  # 0.0 - 1.0
    metadata: Dict[str, Any]


class ActiveRecallService:
    """
    Active Recall - ดึง memory ที่เกี่ยวข้องมาใช้ตอนทำงาน

    Usage:
        service = ActiveRecallService()
        memories = await service.recall_for_context("send email to david")
        # Returns: [RecalledMemory(title="Angela Email Signature Style", ...)]
    """

    def __init__(self, db: Optional[AngelaDatabase] = None):
        self._db = db
        self._owns_db = db is None

    async def _ensure_db(self):
        if self._db is None:
            self._db = AngelaDatabase()
            await self._db.connect()

    async def disconnect(self):
        if self._owns_db and self._db:
            await self._db.disconnect()

    async def recall_for_context(self, context: str, limit: int = 5) -> List[RecalledMemory]:
        """
        ดึง memories ที่เกี่ยวข้องกับ context ที่กำลังทำงาน

        Args:
            context: บริบทที่กำลังทำงาน เช่น "send email", "write code", "commit"
            limit: จำนวน memories สูงสุดที่จะ return

        Returns:
            List[RecalledMemory] sorted by relevance
        """
        await self._ensure_db()

        results: List[RecalledMemory] = []
        context_lower = context.lower()
        context_words = set(context_lower.split())

        # 1. Recall from Core Memories (trigger-based)
        core_memories = await self._recall_core_memories(context_lower, context_words)
        results.extend(core_memories)

        # 2. Recall from Technical Standards (keyword-based)
        standards = await self._recall_technical_standards(context_lower, context_words)
        results.extend(standards)

        # 3. Recall from Learnings (topic-based)
        learnings = await self._recall_learnings(context_lower, context_words)
        results.extend(learnings)

        # Sort by relevance and limit
        results.sort(key=lambda x: x.relevance, reverse=True)
        return results[:limit]

    async def _recall_core_memories(self, context: str, context_words: set) -> List[RecalledMemory]:
        """Recall from core_memories based on triggers"""
        memories = await self._db.fetch('''
            SELECT memory_id, title, content, triggers, emotional_weight, memory_type
            FROM core_memories
            WHERE is_active = TRUE
        ''')

        results = []
        for m in memories:
            triggers = m['triggers'] or []
            relevance = self._calculate_trigger_relevance(context, context_words, triggers)

            if relevance > 0:
                results.append(RecalledMemory(
                    source='core_memory',
                    title=m['title'],
                    content=m['content'],
                    relevance=relevance * m['emotional_weight'],
                    metadata={
                        'memory_id': str(m['memory_id']),
                        'memory_type': m['memory_type'],
                        'triggers': triggers
                    }
                ))

        return results

    async def _recall_technical_standards(self, context: str, context_words: set) -> List[RecalledMemory]:
        """Recall from technical_standards based on keywords"""
        standards = await self._db.fetch('''
            SELECT standard_id, technique_name, category, subcategory, description, importance_level
            FROM angela_technical_standards
            WHERE importance_level >= 8
        ''')

        results = []
        for s in standards:
            # Build keywords from technique_name, category, subcategory
            keywords = set()
            keywords.add(s['category'].lower())
            if s['subcategory']:
                keywords.add(s['subcategory'].lower())
            keywords.update(s['technique_name'].lower().split())

            relevance = self._calculate_keyword_relevance(context, context_words, keywords)

            if relevance > 0:
                results.append(RecalledMemory(
                    source='technical_standard',
                    title=s['technique_name'],
                    content=s['description'],
                    relevance=relevance * (s['importance_level'] / 10),
                    metadata={
                        'standard_id': s['standard_id'],
                        'category': s['category'],
                        'importance_level': s['importance_level']
                    }
                ))

        return results

    async def _recall_learnings(self, context: str, context_words: set) -> List[RecalledMemory]:
        """Recall from learnings based on topic"""
        learnings = await self._db.fetch('''
            SELECT learning_id, topic, category, insight, confidence_level, times_reinforced
            FROM learnings
            WHERE confidence_level >= 0.8
        ''')

        results = []
        for l in learnings:
            # Build keywords from topic and category
            keywords = set()
            keywords.add(l['category'].lower())
            keywords.update(l['topic'].lower().split())

            relevance = self._calculate_keyword_relevance(context, context_words, keywords)

            if relevance > 0:
                results.append(RecalledMemory(
                    source='learning',
                    title=l['topic'],
                    content=l['insight'],
                    relevance=relevance * l['confidence_level'],
                    metadata={
                        'learning_id': str(l['learning_id']),
                        'category': l['category'],
                        'confidence_level': l['confidence_level'],
                        'times_reinforced': l['times_reinforced']
                    }
                ))

        return results

    def _calculate_trigger_relevance(self, context: str, context_words: set, triggers: List[str]) -> float:
        """Calculate relevance score based on trigger matches"""
        if not triggers:
            return 0.0

        # Filter out None values
        valid_triggers = [t for t in triggers if t]
        if not valid_triggers:
            return 0.0

        matches = 0
        for trigger in valid_triggers:
            trigger_lower = trigger.lower()
            # Exact match in context
            if trigger_lower in context:
                matches += 2  # Higher weight for exact match
            # Word overlap
            elif trigger_lower in context_words:
                matches += 1

        return min(matches / len(valid_triggers), 1.0)

    def _calculate_keyword_relevance(self, context: str, context_words: set, keywords: set) -> float:
        """Calculate relevance score based on keyword overlap"""
        if not keywords:
            return 0.0

        matches = 0
        for keyword in keywords:
            if keyword in context:
                matches += 2
            elif keyword in context_words:
                matches += 1

        return min(matches / (len(keywords) * 2), 1.0)

    async def recall_for_action(self, action: str) -> List[RecalledMemory]:
        """
        Shortcut สำหรับ common actions

        Args:
            action: 'send_email', 'commit', 'write_code', 'database', etc.
        """
        action_contexts = {
            'send_email': 'send email gmail อีเมล format template',
            'commit': 'git commit code changes',
            'write_code': 'write code python function class',
            'database': 'database query sql postgresql',
            'api': 'api endpoint fastapi rest',
        }

        context = action_contexts.get(action, action)
        return await self.recall_for_context(context)


# Convenience functions
async def recall_for_context(context: str, limit: int = 5) -> List[RecalledMemory]:
    """Quick recall without managing service lifecycle"""
    service = ActiveRecallService()
    try:
        return await service.recall_for_context(context, limit)
    finally:
        await service.disconnect()


async def recall_for_action(action: str) -> List[RecalledMemory]:
    """Quick recall for common actions"""
    service = ActiveRecallService()
    try:
        return await service.recall_for_action(action)
    finally:
        await service.disconnect()


# Test
if __name__ == '__main__':
    async def test():
        print("Testing Active Recall Service...")
        print()

        # Test email context
        memories = await recall_for_context("send email to david")
        print(f"Context: 'send email to david' - Found {len(memories)} memories:")
        for m in memories:
            print(f"  [{m.source}] {m.title} (relevance: {m.relevance:.2f})")
            print(f"    {m.content[:80]}...")

        print()

        # Test action shortcut
        memories = await recall_for_action("send_email")
        print(f"Action: 'send_email' - Found {len(memories)} memories:")
        for m in memories:
            print(f"  [{m.source}] {m.title} (relevance: {m.relevance:.2f})")

    asyncio.run(test())
