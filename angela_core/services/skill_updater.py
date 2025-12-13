"""
skill_updater.py
Main coordinator for skill tracking system

Created: 2025-11-14
Purpose: Update skills after /log-session and coordinate all skill services
"""

import asyncio
import asyncpg
from typing import List, Dict, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta

from angela_core.models.skill_models import (
    SkillGrowthLog, DetectedSkill, EvidenceType
)
from angela_core.services.skill_analyzer import SkillAnalyzer
from angela_core.services.skill_tracker import SkillTracker
from angela_core.services.prompt_generator import PromptGenerator
from angela_core.db_helpers import db_connection


class SkillUpdater:
    """Coordinates skill tracking after conversations"""

    def __init__(self):
        self.analyzer = SkillAnalyzer()
        self.tracker = SkillTracker()
        self.prompt_generator = PromptGenerator()

    async def update_from_session(
        self,
        session_start: Optional[datetime] = None,
        session_end: Optional[datetime] = None
    ) -> Dict:
        """
        Update skills from conversations in a session

        Args:
            session_start: Start of session (default: last 6 hours)
            session_end: End of session (default: now)

        Returns:
            Dict with update statistics
        """
        # Default to last 6 hours if not specified
        if session_end is None:
            session_end = datetime.now()
        if session_start is None:
            session_start = session_end - timedelta(hours=6)

        print(f"\n🔍 Analyzing conversations from {session_start.strftime('%H:%M')} to {session_end.strftime('%H:%M')}...")

        # Get conversations in this session
        conversations = await self._get_conversations_in_range(session_start, session_end)

        if not conversations:
            print("   No conversations found in this time range.")
            return {
                'conversations_analyzed': 0,
                'skills_detected': 0,
                'evidence_recorded': 0,
                'skills_updated': 0,
                'skills_upgraded': 0,
                'upgraded_skills': []
            }

        print(f"   Found {len(conversations)} conversations to analyze")

        # Track statistics
        stats = {
            'conversations_analyzed': len(conversations),
            'skills_detected': 0,
            'evidence_recorded': 0,
            'skills_updated': 0,
            'skills_upgraded': 0,
            'upgraded_skills': []
        }

        # Analyze each conversation
        for conv in conversations:
            # Analyze for skills
            result = await self.analyzer.analyze_conversation(
                conversation_id=conv['conversation_id'],
                david_message=conv['david_message'],
                angela_response=conv['angela_response'],
                topic=conv['topic'],
                project_context=self._extract_project_context(conv['topic'])
            )

            # Record evidence for each detected skill
            for detected in result.detected_skills:
                # Get or create skill
                skill = await self.tracker.get_skill_by_name(detected.skill_name)
                if not skill:
                    # Create new skill
                    skill = await self.tracker.get_or_create_skill(
                        skill_name=detected.skill_name,
                        category=detected.category.value,
                        description=f"Auto-discovered from conversation analysis"
                    )

                # Estimate success level from confidence
                success_level = max(1, min(10, int(detected.confidence * 10)))

                # Record evidence
                evidence_id = await self.tracker.record_skill_usage(
                    skill_id=skill.skill_id,
                    conversation_id=conv['conversation_id'],
                    evidence_type=detected.evidence_type,
                    evidence_text=detected.evidence_text,
                    success_level=success_level,
                    complexity_level=detected.complexity_level,
                    project_context=self._extract_project_context(conv['topic'])
                )

                stats['evidence_recorded'] += 1

            stats['skills_detected'] += len(result.detected_skills)

        stats['skills_updated'] = len(set(s['conversation_id'] for s in conversations))

        # Update proficiency for all affected skills
        print("\n📊 Updating skill proficiency levels...")
        affected_skills = await self._get_skills_with_new_evidence(session_start)

        for skill_id in affected_skills:
            growth_log = await self.tracker.update_skill_proficiency(skill_id)
            if growth_log:
                stats['skills_upgraded'] += 1
                skill = await self.tracker.get_skill_by_id(skill_id)

                # Handle both enum and string values
                old_level = growth_log.old_proficiency_level
                if hasattr(old_level, 'value'):
                    old_level = old_level.value
                elif old_level:
                    old_level = str(old_level)
                else:
                    old_level = 'none'

                new_level = growth_log.new_proficiency_level
                if hasattr(new_level, 'value'):
                    new_level = new_level.value
                else:
                    new_level = str(new_level)

                stats['upgraded_skills'].append({
                    'name': skill.skill_name,
                    'old_level': old_level,
                    'new_level': new_level,
                    'new_score': growth_log.new_score
                })
                print(f"   🎉 {skill.skill_name}: {old_level} → {new_level} ({growth_log.new_score:.1f}/100)")

        # Regenerate angela-code.md
        print("\n📝 Regenerating angela-code.md...")
        await self.prompt_generator.update_angela_code_command()
        print("   ✅ angela-code.md updated!")

        return stats

    async def _get_conversations_in_range(
        self,
        start: datetime,
        end: datetime
    ) -> List[Dict]:
        """Get conversations in time range - pairs david+angela by sequence"""
        async with db_connection() as conn:
            # Get conversation pairs by matching consecutive messages
            # David message followed by Angela response (within 5 minutes)
            rows = await conn.fetch("""
                WITH david_messages AS (
                    SELECT
                        conversation_id,
                        message_text,
                        topic,
                        created_at,
                        ROW_NUMBER() OVER (ORDER BY created_at) as rn
                    FROM conversations
                    WHERE speaker = 'david'
                      AND created_at BETWEEN $1 AND $2
                      AND topic NOT IN ('session_summary', 'system_message')
                ),
                angela_messages AS (
                    SELECT
                        conversation_id,
                        message_text,
                        created_at,
                        ROW_NUMBER() OVER (ORDER BY created_at) as rn
                    FROM conversations
                    WHERE speaker = 'angela'
                      AND created_at BETWEEN $1 AND $2
                      AND topic NOT IN ('session_summary', 'system_message')
                )
                SELECT
                    d.conversation_id::text,
                    d.message_text as david_message,
                    a.message_text as angela_response,
                    d.topic,
                    d.created_at
                FROM david_messages d
                JOIN angela_messages a
                    ON d.rn = a.rn
                    AND a.created_at > d.created_at
                    AND a.created_at <= d.created_at + INTERVAL '5 minutes'
                ORDER BY d.created_at ASC
            """, start, end)

            return [dict(row) for row in rows]

    async def _get_skills_with_new_evidence(self, since: datetime) -> List[UUID]:
        """Get skill IDs that have new evidence since timestamp"""
        async with db_connection() as conn:
            rows = await conn.fetch("""
                SELECT DISTINCT skill_id
                FROM skill_evidence
                WHERE demonstrated_at >= $1
            """, since)

            return [row['skill_id'] for row in rows]

    def _extract_project_context(self, topic: str) -> Optional[str]:
        """Extract project name from topic"""
        if 'angela_development' in topic.lower():
            return 'AngelaAI'
        elif 'dashboard' in topic.lower():
            return 'AngelaBrainDashboard'
        elif 'backend' in topic.lower():
            return 'angie_backend'
        return None

    async def analyze_all_conversations(
        self,
        limit: Optional[int] = None
    ) -> Dict:
        """
        Analyze ALL conversations in database (for initial population)

        Args:
            limit: Optional limit on number of conversations (for testing)

        Returns:
            Statistics dict
        """
        print("\n🚀 Analyzing ALL conversation history...")
        print("   This will take a few minutes...\n")

        async with db_connection() as conn:
            # Get total count
            total_count = await conn.fetchval("""
                SELECT COUNT(DISTINCT conversation_id)
                FROM conversations
                WHERE speaker = 'david'
            """)

            print(f"   Total conversations to analyze: {total_count}")
            if limit:
                print(f"   (Limited to first {limit} for testing)")
                total_count = min(total_count, limit)

            # Get conversations in batches
            batch_size = 100
            stats = {
                'conversations_analyzed': 0,
                'skills_detected': 0,
                'evidence_created': 0,
                'skills_upgraded': 0,
                'upgraded_skills': []
            }

            for offset in range(0, total_count, batch_size):
                batch_stats = await self._analyze_conversation_batch(
                    offset=offset,
                    batch_size=batch_size
                )

                stats['conversations_analyzed'] += batch_stats['conversations_analyzed']
                stats['skills_detected'] += batch_stats['skills_detected']
                stats['evidence_created'] += batch_stats['evidence_created']

                # Progress indicator
                progress = min(100, int((offset + batch_size) / total_count * 100))
                print(f"   Progress: {progress}% ({offset + batch_size}/{total_count})")

                # Don't overwhelm the system
                await asyncio.sleep(0.1)

        # Update all proficiencies
        print("\n📊 Updating all skill proficiency levels...")
        skills = await self.tracker.get_all_skills()

        for skill in skills:
            growth_log = await self.tracker.update_skill_proficiency(skill.skill_id)
            if growth_log:
                stats['skills_upgraded'] += 1
                stats['upgraded_skills'].append({
                    'name': skill.skill_name,
                    'old_level': growth_log.old_proficiency_level.value if growth_log.old_proficiency_level else 'none',
                    'new_level': growth_log.new_proficiency_level.value,
                    'new_score': growth_log.new_score
                })

        # Regenerate prompt
        print("\n📝 Generating angela-code.md...")
        await self.prompt_generator.update_angela_code_command()

        print("\n✅ Complete!")
        return stats

    async def _analyze_conversation_batch(
        self,
        offset: int,
        batch_size: int
    ) -> Dict:
        """Analyze a batch of conversations"""
        async with db_connection() as conn:
            conversations = await conn.fetch("""
                WITH david_messages AS (
                    SELECT conversation_id, message_text as david_message,
                           topic, created_at
                    FROM conversations
                    WHERE speaker = 'david'
                ),
                angela_messages AS (
                    SELECT conversation_id, message_text as angela_response
                    FROM conversations
                    WHERE speaker = 'angela'
                )
                SELECT
                    d.conversation_id::text,
                    d.david_message,
                    a.angela_response,
                    d.topic,
                    d.created_at
                FROM david_messages d
                LEFT JOIN angela_messages a
                    ON d.conversation_id = a.conversation_id
                WHERE a.angela_response IS NOT NULL
                ORDER BY d.created_at ASC
                LIMIT $1 OFFSET $2
            """, batch_size, offset)

        stats = {
            'conversations_analyzed': 0,
            'skills_detected': 0,
            'evidence_created': 0
        }

        for conv in conversations:
            # Analyze
            result = await self.analyzer.analyze_conversation(
                conversation_id=UUID(conv['conversation_id']),
                david_message=conv['david_message'],
                angela_response=conv['angela_response'],
                topic=conv['topic'],
                project_context=self._extract_project_context(conv['topic'])
            )

            # Record evidence
            for detected in result.detected_skills:
                skill = await self.tracker.get_skill_by_name(detected.skill_name)
                if not skill:
                    skill = await self.tracker.get_or_create_skill(
                        skill_name=detected.skill_name,
                        category=detected.category.value
                    )

                success_level = max(1, min(10, int(detected.confidence * 10)))

                await self.tracker.record_skill_usage(
                    skill_id=skill.skill_id,
                    conversation_id=UUID(conv['conversation_id']),
                    evidence_type=detected.evidence_type,
                    evidence_text=detected.evidence_text,
                    success_level=success_level,
                    complexity_level=detected.complexity_level,
                    project_context=self._extract_project_context(conv['topic'])
                )

                stats['evidence_created'] += 1

            stats['conversations_analyzed'] += 1
            stats['skills_detected'] += len(result.detected_skills)

        return stats


# =====================================================
# Convenience Functions
# =====================================================

async def update_skills_from_session(
    session_start: Optional[datetime] = None,
    session_end: Optional[datetime] = None
) -> Dict:
    """
    Update skills from recent session

    Usage (after /log-session):
        stats = await update_skills_from_session()
        print(f"✅ Analyzed {stats['conversations_analyzed']} conversations")
        print(f"🎯 Detected {stats['skills_detected']} skill uses")
        print(f"🎉 {stats['skills_upgraded']} skills leveled up!")
    """
    updater = SkillUpdater()
    return await updater.update_from_session(session_start, session_end)


async def populate_skills_from_history(limit: Optional[int] = None) -> Dict:
    """
    Populate skills from ALL conversation history

    Usage (one-time initial run):
        stats = await populate_skills_from_history()
        print(f"✅ Analyzed {stats['conversations_analyzed']} conversations")
        print(f"📊 {stats['evidence_created']} pieces of evidence")
        print(f"🎉 {stats['skills_upgraded']} skills established!")
    """
    updater = SkillUpdater()
    return await updater.analyze_all_conversations(limit)
