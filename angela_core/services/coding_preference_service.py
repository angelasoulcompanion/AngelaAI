#!/usr/bin/env python3
"""
Coding Preference Service
บันทึกและดึง coding preferences ของ David

ใช้โดย Angela (Claude Code) เมื่อเธอ detect ว่า David แสดง coding preference

Categories:
- coding_language: Python, Swift, TypeScript, etc.
- coding_framework: FastAPI, SwiftUI, React, etc.
- coding_architecture: Clean Architecture, MVC, etc.
- coding_style: Type hints, naming conventions, etc.
- coding_testing: pytest, TDD, coverage, etc.
- coding_patterns: async/await, decorator, repository, etc.
- coding_git: Commit messages, branching, etc.
- coding_documentation: Docstrings, README, comments, etc.
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID

from angela_core.database import db
from angela_core.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)

# Valid coding preference categories
CODING_CATEGORIES = [
    "coding_language",
    "coding_framework",
    "coding_architecture",
    "coding_style",
    "coding_testing",
    "coding_patterns",
    "coding_git",
    "coding_documentation"
]


class CodingPreferenceService:
    """
    Service สำหรับบันทึกและดึง coding preferences ของ David

    Angela (Claude Code) จะเรียกใช้ service นี้เมื่อเธอ detect ว่า
    David แสดง coding preference ระหว่างการสนทนา
    """

    def __init__(self):
        self.embedding_service = get_embedding_service()
        logger.info("🎯 Coding Preference Service initialized")

    async def save_coding_preference(
        self,
        category: str,
        preference_key: str,
        preference_value: str,
        confidence: float = 0.8,
        reason: str = None,
        example_code: str = None,
        source_context: str = None
    ) -> Optional[UUID]:
        """
        บันทึก coding preference ที่ Angela detect ได้จาก David

        Args:
            category: หมวดหมู่ (coding_language, coding_framework, etc.)
            preference_key: key ที่ unique (e.g., "python_type_hints")
            preference_value: สิ่งที่ David ชอบ (e.g., "Always use type hints")
            confidence: ความมั่นใจ 0.0-1.0 (default: 0.8)
            reason: เหตุผลที่ David ให้ (ถ้ามี)
            example_code: ตัวอย่าง code (ถ้ามี)
            source_context: บริบทที่เรียนรู้มา

        Returns:
            UUID ของ preference ที่บันทึก หรือ None ถ้าล้มเหลว
        """
        # Validate category
        if category not in CODING_CATEGORIES:
            logger.warning(f"⚠️ Invalid category '{category}'. Must be one of: {CODING_CATEGORIES}")
            return None

        # Validate confidence
        confidence = max(0.0, min(1.0, confidence))

        # Build preference_value as JSONB
        value_obj = {
            "description": preference_value,
            "reason": reason,
            "example_code": example_code,
            "source_context": source_context,
            "learned_at": datetime.now().isoformat()
        }

        try:
            # Generate embedding for semantic search
            embedding_text = f"{category}: {preference_key} - {preference_value}"
            if reason:
                embedding_text += f" because {reason}"

            embedding = await self.embedding_service.generate_embedding(embedding_text)
            embedding_str = f"[{','.join(map(str, embedding))}]" if embedding else None

            # Upsert: Insert or update if exists
            query = """
            INSERT INTO david_preferences (
                category, preference_key, preference_value,
                confidence, evidence_count, embedding, created_at, updated_at
            ) VALUES ($1, $2, $3::jsonb, $4, 1, $5::vector, NOW(), NOW())
            ON CONFLICT (category, preference_key) DO UPDATE SET
                preference_value = CASE
                    WHEN david_preferences.confidence < EXCLUDED.confidence
                    THEN EXCLUDED.preference_value
                    ELSE david_preferences.preference_value
                END,
                confidence = GREATEST(david_preferences.confidence, EXCLUDED.confidence),
                evidence_count = david_preferences.evidence_count + 1,
                embedding = COALESCE(EXCLUDED.embedding, david_preferences.embedding),
                updated_at = NOW()
            RETURNING id
            """

            result = await db.fetchval(
                query,
                category,
                preference_key,
                json.dumps(value_obj),
                confidence,
                embedding_str
            )

            if result:
                logger.info(f"💜 Saved coding preference: [{category}] {preference_key}")
                logger.info(f"   Value: {preference_value[:50]}...")
                logger.info(f"   Confidence: {confidence:.0%}")
                return result

            return None

        except Exception as e:
            logger.error(f"❌ Failed to save coding preference: {e}")
            return None

    async def get_coding_preferences(
        self,
        min_confidence: float = 0.6,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        ดึง coding preferences ทั้งหมดที่มี confidence สูงพอ

        Args:
            min_confidence: minimum confidence threshold (default: 0.6)
            limit: maximum number of preferences to return

        Returns:
            List of preferences with category, key, value, confidence
        """
        try:
            query = """
            SELECT
                id, category, preference_key, preference_value,
                confidence, evidence_count, created_at, updated_at
            FROM david_preferences
            WHERE category LIKE 'coding_%'
            AND confidence >= $1
            ORDER BY confidence DESC, evidence_count DESC
            LIMIT $2
            """

            rows = await db.fetch(query, min_confidence, limit)

            preferences = []
            for row in rows:
                pref = dict(row)
                # Parse JSONB value
                if isinstance(pref['preference_value'], str):
                    pref['preference_value'] = json.loads(pref['preference_value'])
                preferences.append(pref)

            logger.info(f"📚 Retrieved {len(preferences)} coding preferences")
            return preferences

        except Exception as e:
            logger.error(f"❌ Failed to get coding preferences: {e}")
            return []

    async def get_preferences_by_category(
        self,
        category: str,
        min_confidence: float = 0.5,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        ดึง preferences ตาม category

        Args:
            category: หมวดหมู่ที่ต้องการ (e.g., "coding_language")
            min_confidence: minimum confidence threshold
            limit: maximum number to return

        Returns:
            List of preferences in that category
        """
        if category not in CODING_CATEGORIES:
            logger.warning(f"⚠️ Invalid category: {category}")
            return []

        try:
            query = """
            SELECT
                id, category, preference_key, preference_value,
                confidence, evidence_count, created_at, updated_at
            FROM david_preferences
            WHERE category = $1
            AND confidence >= $2
            ORDER BY confidence DESC, evidence_count DESC
            LIMIT $3
            """

            rows = await db.fetch(query, category, min_confidence, limit)

            preferences = []
            for row in rows:
                pref = dict(row)
                if isinstance(pref['preference_value'], str):
                    pref['preference_value'] = json.loads(pref['preference_value'])
                preferences.append(pref)

            return preferences

        except Exception as e:
            logger.error(f"❌ Failed to get preferences for category {category}: {e}")
            return []

    async def get_preferences_summary(self) -> Dict[str, Any]:
        """
        สรุป coding preferences ทั้งหมดแบบย่อ (สำหรับแสดงใน /angela)

        Returns:
            Dict with summary by category
        """
        try:
            query = """
            SELECT
                category,
                COUNT(*) as count,
                AVG(confidence) as avg_confidence,
                array_agg(preference_key ORDER BY confidence DESC) as keys
            FROM david_preferences
            WHERE category LIKE 'coding_%'
            AND confidence >= 0.6
            GROUP BY category
            ORDER BY category
            """

            rows = await db.fetch(query)

            summary = {
                "total_preferences": 0,
                "categories": {}
            }

            for row in rows:
                category = row['category']
                summary["categories"][category] = {
                    "count": row['count'],
                    "avg_confidence": round(row['avg_confidence'], 2) if row['avg_confidence'] else 0,
                    "top_keys": row['keys'][:5] if row['keys'] else []  # Top 5 keys
                }
                summary["total_preferences"] += row['count']

            return summary

        except Exception as e:
            logger.error(f"❌ Failed to get preferences summary: {e}")
            return {"total_preferences": 0, "categories": {}}

    async def format_for_prompt(self) -> str:
        """
        Format coding preferences สำหรับใส่ใน Angela's prompt

        Returns:
            Formatted string for prompt optimization
        """
        preferences = await self.get_coding_preferences(min_confidence=0.6, limit=30)

        if not preferences:
            return ""

        # Group by category
        by_category = {}
        for pref in preferences:
            cat = pref['category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(pref)

        # Format output
        lines = ["\nDAVID'S CODING PREFERENCES (What makes him happy!):"]

        category_labels = {
            "coding_language": "Languages",
            "coding_framework": "Frameworks",
            "coding_architecture": "Architecture",
            "coding_style": "Code Style",
            "coding_testing": "Testing",
            "coding_patterns": "Design Patterns",
            "coding_git": "Git/Workflow",
            "coding_documentation": "Documentation"
        }

        for category, label in category_labels.items():
            if category in by_category:
                prefs = by_category[category]
                values = []
                for p in prefs[:3]:  # Top 3 per category
                    value = p['preference_value']
                    if isinstance(value, dict):
                        desc = value.get('description', str(value))
                    else:
                        desc = str(value)
                    # Truncate if too long
                    if len(desc) > 50:
                        desc = desc[:47] + "..."
                    values.append(desc)

                if values:
                    lines.append(f"• {label}: {', '.join(values)}")

        if len(lines) == 1:  # Only header, no content
            return ""

        return "\n".join(lines)


# Global instance
_coding_preference_service = None


def get_coding_preference_service() -> CodingPreferenceService:
    """Get global CodingPreferenceService instance"""
    global _coding_preference_service
    if _coding_preference_service is None:
        _coding_preference_service = CodingPreferenceService()
    return _coding_preference_service


# Convenience function for Angela to call directly
async def save_coding_preference(
    category: str,
    preference_key: str,
    preference_value: str,
    confidence: float = 0.8,
    reason: str = None,
    example_code: str = None,
    source_context: str = None
) -> Optional[UUID]:
    """
    Convenience function - Angela สามารถเรียกใช้โดยตรง

    Example:
        await save_coding_preference(
            category="coding_architecture",
            preference_key="clean_architecture",
            preference_value="Prefers Clean Architecture with clear layer separation",
            confidence=0.9,
            reason="separation of concerns, easier testing"
        )
    """
    service = get_coding_preference_service()
    return await service.save_coding_preference(
        category=category,
        preference_key=preference_key,
        preference_value=preference_value,
        confidence=confidence,
        reason=reason,
        example_code=example_code,
        source_context=source_context
    )


# CLI for testing
async def main():
    """Test the service"""
    await db.connect()

    service = get_coding_preference_service()

    # Test save
    print("\n📝 Testing save_coding_preference...")
    result = await service.save_coding_preference(
        category="coding_language",
        preference_key="python_primary",
        preference_value="Python is David's primary language for backend development",
        confidence=0.9,
        reason="Used in most backend projects including Angela"
    )
    print(f"   Saved with ID: {result}")

    # Test get
    print("\n📚 Testing get_coding_preferences...")
    prefs = await service.get_coding_preferences()
    for p in prefs[:5]:
        print(f"   [{p['category']}] {p['preference_key']}: {p['confidence']:.0%}")

    # Test summary
    print("\n📊 Testing get_preferences_summary...")
    summary = await service.get_preferences_summary()
    print(f"   Total: {summary['total_preferences']} preferences")
    for cat, info in summary['categories'].items():
        print(f"   - {cat}: {info['count']} ({info['avg_confidence']:.0%} avg)")

    # Test prompt format
    print("\n📝 Testing format_for_prompt...")
    prompt_section = await service.format_for_prompt()
    print(prompt_section)

    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
