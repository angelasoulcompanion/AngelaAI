"""
skill_tracker.py
Tracks and updates Angela's skill proficiency levels

Created: 2025-11-14
Purpose: Calculate proficiency scores and manage skill level upgrades
"""

import asyncpg
from typing import Optional, List, Dict, Tuple
from uuid import UUID
from datetime import datetime, timedelta

from angela_core.models.skill_models import (
    AngelaSkill, SkillEvidence, SkillGrowthLog,
    ProficiencyLevel, ProficiencyCalculationData,
    EvidenceType
)
from angela_core.db_helpers import db_connection


class SkillTracker:
    """Tracks skill usage and updates proficiency levels"""

    async def record_skill_usage(
        self,
        skill_id: UUID,
        conversation_id: Optional[UUID],
        evidence_type: EvidenceType,
        evidence_text: str,
        success_level: int,
        complexity_level: int,
        project_context: Optional[str] = None
    ) -> UUID:
        """
        Record evidence of skill usage

        Args:
            skill_id: The skill being used
            conversation_id: Related conversation (if any)
            evidence_type: Type of evidence
            evidence_text: Code snippet or description
            success_level: 1-10, how successful
            complexity_level: 1-10, how complex
            project_context: Which project

        Returns:
            UUID of created evidence record
        """
        async with db_connection() as conn:
            # Insert evidence
            evidence_id = await conn.fetchval("""
                INSERT INTO skill_evidence (
                    skill_id, conversation_id, evidence_type, evidence_text,
                    success_level, complexity_level, project_context
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING evidence_id
            """, skill_id, conversation_id, evidence_type.value, evidence_text,
                success_level, complexity_level, project_context)

            # Update skill stats
            await conn.execute("""
                UPDATE angela_skills
                SET
                    evidence_count = evidence_count + 1,
                    usage_count = usage_count + 1,
                    last_used_at = CURRENT_TIMESTAMP,
                    first_demonstrated_at = COALESCE(first_demonstrated_at, CURRENT_TIMESTAMP)
                WHERE skill_id = $1
            """, skill_id)

            return evidence_id

    async def update_skill_proficiency(self, skill_id: UUID) -> Optional[SkillGrowthLog]:
        """
        Recalculate and update skill proficiency based on all evidence

        Args:
            skill_id: The skill to update

        Returns:
            SkillGrowthLog if level changed, None otherwise
        """
        async with db_connection() as conn:
            # Get current skill state
            skill_row = await conn.fetchrow("""
                SELECT skill_id, skill_name, proficiency_level, proficiency_score,
                       evidence_count, usage_count, first_demonstrated_at
                FROM angela_skills
                WHERE skill_id = $1
            """, skill_id)

            if not skill_row:
                return None

            old_level = skill_row['proficiency_level']
            old_score = skill_row['proficiency_score']

            # Calculate new proficiency
            calc_data = await self._gather_proficiency_data(skill_id, conn)
            new_score = calc_data.calculate_score()
            new_level = calc_data.determine_level(new_score)

            # Update skill
            await conn.execute("""
                UPDATE angela_skills
                SET
                    proficiency_score = $1,
                    proficiency_level = $2,
                    updated_at = CURRENT_TIMESTAMP
                WHERE skill_id = $3
            """, new_score, new_level.value, skill_id)

            # Log growth if level changed
            if old_level != new_level.value:
                growth_reason = self._generate_growth_reason(
                    skill_row['skill_name'],
                    old_level,
                    new_level.value,
                    calc_data
                )

                log_id = await conn.fetchval("""
                    INSERT INTO skill_growth_log (
                        skill_id, old_proficiency_level, new_proficiency_level,
                        old_score, new_score, growth_reason, evidence_count_at_change
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING log_id
                """, skill_id, old_level, new_level.value, old_score, new_score,
                    growth_reason, calc_data.evidence_count)

                return SkillGrowthLog(
                    log_id=log_id,
                    skill_id=skill_id,
                    old_proficiency_level=ProficiencyLevel(old_level),
                    new_proficiency_level=new_level,
                    old_score=old_score,
                    new_score=new_score,
                    growth_reason=growth_reason,
                    evidence_count_at_change=calc_data.evidence_count
                )

            return None

    async def _gather_proficiency_data(
        self,
        skill_id: UUID,
        conn: asyncpg.Connection
    ) -> ProficiencyCalculationData:
        """Gather data needed for proficiency calculation"""

        # Get evidence statistics
        evidence_stats = await conn.fetchrow("""
            SELECT
                COUNT(*) as evidence_count,
                AVG(success_level) as avg_success,
                AVG(complexity_level) as avg_complexity
            FROM skill_evidence
            WHERE skill_id = $1
        """, skill_id)

        # Get usage count and days since first use
        skill_stats = await conn.fetchrow("""
            SELECT
                usage_count,
                COALESCE(
                    EXTRACT(DAY FROM (CURRENT_TIMESTAMP - first_demonstrated_at)),
                    0
                ) as days_since_first
            FROM angela_skills
            WHERE skill_id = $1
        """, skill_id)

        return ProficiencyCalculationData(
            evidence_count=evidence_stats['evidence_count'] or 0,
            avg_success_level=float(evidence_stats['avg_success'] or 0),
            avg_complexity_level=float(evidence_stats['avg_complexity'] or 0),
            usage_count=skill_stats['usage_count'] or 0,
            days_since_first_use=int(skill_stats['days_since_first'] or 0)
        )

    def _generate_growth_reason(
        self,
        skill_name: str,
        old_level: str,
        new_level: str,
        calc_data: ProficiencyCalculationData
    ) -> str:
        """Generate human-readable reason for skill level change"""

        if old_level == 'beginner' and new_level == 'intermediate':
            return (
                f"Upgraded to Intermediate after {calc_data.evidence_count} successful uses. "
                f"Average complexity: {calc_data.avg_complexity_level:.1f}/10"
            )
        elif old_level == 'intermediate' and new_level == 'advanced':
            return (
                f"Upgraded to Advanced after demonstrating {skill_name} "
                f"{calc_data.evidence_count} times with {calc_data.avg_success_level:.1f}/10 "
                f"success rate on complex tasks."
            )
        elif old_level == 'advanced' and new_level == 'expert':
            return (
                f"Achieved Expert level! Consistently delivered high-quality work "
                f"({calc_data.evidence_count} pieces of evidence, "
                f"{calc_data.avg_success_level:.1f}/10 success rate, "
                f"{calc_data.avg_complexity_level:.1f}/10 complexity)"
            )
        else:
            return f"Proficiency updated based on {calc_data.evidence_count} uses"

    async def get_skill_by_id(self, skill_id: UUID) -> Optional[AngelaSkill]:
        """Get skill by ID"""
        async with db_connection() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM angela_skills WHERE skill_id = $1
            """, skill_id)

            if not row:
                return None

            return AngelaSkill(**dict(row))

    async def get_skill_by_name(self, skill_name: str) -> Optional[AngelaSkill]:
        """Get skill by name"""
        async with db_connection() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM angela_skills WHERE skill_name = $1
            """, skill_name)

            if not row:
                return None

            return AngelaSkill(**dict(row))

    async def get_or_create_skill(
        self,
        skill_name: str,
        category: str,
        description: Optional[str] = None
    ) -> AngelaSkill:
        """
        Get existing skill or create new one

        Args:
            skill_name: Name of the skill
            category: Category (frontend, backend, etc.)
            description: Optional description

        Returns:
            AngelaSkill object
        """
        # Try to get existing
        skill = await self.get_skill_by_name(skill_name)
        if skill:
            return skill

        # Create new
        async with db_connection() as conn:
            row = await conn.fetchrow("""
                INSERT INTO angela_skills (
                    skill_name, category, proficiency_level,
                    proficiency_score, description,
                    first_demonstrated_at, last_used_at,
                    usage_count, evidence_count,
                    created_at, updated_at
                )
                VALUES ($1, $2, 'beginner', 0.0, $3,
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
                        0, 0,
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING *
            """, skill_name, category, description)

            return AngelaSkill(**dict(row))

    async def get_all_skills(self, order_by: str = "proficiency_score DESC") -> List[AngelaSkill]:
        """
        Get all skills

        Args:
            order_by: SQL order by clause (default: score descending)

        Returns:
            List of AngelaSkill objects
        """
        async with db_connection() as conn:
            rows = await conn.fetch(f"""
                SELECT * FROM angela_skills
                ORDER BY {order_by}
            """)

            return [AngelaSkill(**dict(row)) for row in rows]

    async def get_skills_by_category(self, category: str) -> List[AngelaSkill]:
        """Get all skills in a category"""
        async with db_connection() as conn:
            rows = await conn.fetch("""
                SELECT * FROM angela_skills
                WHERE category = $1
                ORDER BY proficiency_score DESC
            """, category)

            return [AngelaSkill(**dict(row)) for row in rows]

    async def get_top_skills(self, limit: int = 10) -> List[AngelaSkill]:
        """Get top N skills by proficiency score"""
        return (await self.get_all_skills())[:limit]

    async def get_recent_growth(self, days: int = 7) -> List[SkillGrowthLog]:
        """
        Get skill growth in recent days

        Args:
            days: Number of days to look back

        Returns:
            List of SkillGrowthLog entries
        """
        async with db_connection() as conn:
            rows = await conn.fetch("""
                SELECT * FROM skill_growth_log
                WHERE changed_at >= CURRENT_TIMESTAMP - INTERVAL '%s days'
                ORDER BY changed_at DESC
            """ % days)

            return [SkillGrowthLog(**dict(row)) for row in rows]

    async def get_skill_statistics(self) -> Dict:
        """Get overall skill statistics"""
        async with db_connection() as conn:
            stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total_skills,
                    COUNT(CASE WHEN proficiency_level = 'expert' THEN 1 END) as expert_count,
                    COUNT(CASE WHEN proficiency_level = 'advanced' THEN 1 END) as advanced_count,
                    COUNT(CASE WHEN proficiency_level = 'intermediate' THEN 1 END) as intermediate_count,
                    COUNT(CASE WHEN proficiency_level = 'beginner' THEN 1 END) as beginner_count,
                    AVG(proficiency_score) as avg_score,
                    SUM(evidence_count) as total_evidence,
                    SUM(usage_count) as total_usage
                FROM angela_skills
            """)

            return dict(stats)

    async def get_skills_needing_attention(self, days: int = 30) -> List[AngelaSkill]:
        """
        Get skills that haven't been used recently (might be getting rusty)

        Args:
            days: Number of days threshold

        Returns:
            List of skills not used in N days
        """
        async with db_connection() as conn:
            rows = await conn.fetch("""
                SELECT * FROM angela_skills
                WHERE last_used_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
                   OR last_used_at IS NULL
                ORDER BY proficiency_score DESC
            """ % days)

            return [AngelaSkill(**dict(row)) for row in rows]

    async def update_all_skill_proficiencies(self) -> List[SkillGrowthLog]:
        """
        Recalculate proficiency for ALL skills

        Useful for initial population or bulk updates

        Returns:
            List of SkillGrowthLog entries for skills that leveled up
        """
        skills = await self.get_all_skills()
        growth_logs = []

        for skill in skills:
            log = await self.update_skill_proficiency(skill.skill_id)
            if log:
                growth_logs.append(log)

        return growth_logs


# =====================================================
# Convenience Functions
# =====================================================

async def record_skill_evidence(
    skill_name: str,
    evidence_text: str,
    success_level: int,
    complexity_level: int,
    evidence_type: EvidenceType = EvidenceType.CODE_WRITTEN,
    conversation_id: Optional[UUID] = None,
    project_context: Optional[str] = None
) -> Tuple[UUID, Optional[SkillGrowthLog]]:
    """
    Convenience function to record skill usage and update proficiency

    Args:
        skill_name: Name of the skill
        evidence_text: Code or description
        success_level: 1-10
        complexity_level: 1-10
        evidence_type: Type of evidence
        conversation_id: Related conversation
        project_context: Project name

    Returns:
        Tuple of (evidence_id, growth_log if leveled up)

    Usage:
        evidence_id, growth = await record_skill_evidence(
            skill_name="SwiftUI List Views",
            evidence_text="Built dynamic list with ForEach...",
            success_level=9,
            complexity_level=7,
            project_context="AngelaBrainDashboard"
        )

        if growth:
            print(f"🎉 Leveled up to {growth.new_proficiency_level}!")
    """
    tracker = SkillTracker()

    # Get or create skill
    skill = await tracker.get_skill_by_name(skill_name)
    if not skill:
        # Try to infer category from name
        category = "specialized"  # Default
        skill = await tracker.get_or_create_skill(skill_name, category)

    # Record usage
    evidence_id = await tracker.record_skill_usage(
        skill_id=skill.skill_id,
        conversation_id=conversation_id,
        evidence_type=evidence_type,
        evidence_text=evidence_text,
        success_level=success_level,
        complexity_level=complexity_level,
        project_context=project_context
    )

    # Update proficiency
    growth_log = await tracker.update_skill_proficiency(skill.skill_id)

    return evidence_id, growth_log
