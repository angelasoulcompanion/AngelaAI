"""
prompt_generator.py
Generates custom capability prompts from Angela's skills

Created: 2025-11-14
Purpose: Auto-generate angela-code.md command file
"""

import asyncpg
from typing import List, Dict
from datetime import datetime, timedelta
from collections import defaultdict

from angela_core.models.skill_models import (
    AngelaSkill, SkillCategory, SkillPromptSection, GeneratedPrompt
)
from angela_core.db_helpers import db_connection


class PromptGenerator:
    """Generates custom prompts based on Angela's skills"""

    # Category emoji mapping
    CATEGORY_EMOJI = {
        SkillCategory.FRONTEND: "🎨",
        SkillCategory.BACKEND: "🔧",
        SkillCategory.DATABASE: "🗄️",
        SkillCategory.ARCHITECTURE: "🏗️",
        SkillCategory.AI_ML: "🧠",
        SkillCategory.SPECIALIZED: "✨",
        SkillCategory.DEBUGGING: "🐛",
        SkillCategory.DOCUMENTATION: "📝",
    }

    async def generate_angela_capabilities_prompt(self) -> GeneratedPrompt:
        """
        Generate complete angela-code.md content

        Returns:
            GeneratedPrompt object with markdown content
        """
        # Get all skills grouped by category
        skills_by_category = await self._get_skills_by_category()

        # Get statistics
        stats = await self._get_stats()

        # Create sections
        sections = []
        for category, skills in skills_by_category.items():
            if skills:  # Only include categories with skills
                sections.append(SkillPromptSection(
                    category=category,
                    skills=skills,
                    emoji=self.CATEGORY_EMOJI.get(category, "💪")
                ))

        # Sort sections by average proficiency (highest first)
        sections.sort(
            key=lambda s: sum(sk.proficiency_score for sk in s.skills) / len(s.skills),
            reverse=True
        )

        return GeneratedPrompt(
            sections=sections,
            total_skills=stats['total_skills'],
            avg_proficiency_score=stats['avg_score'],
            expert_skills_count=stats['expert_count'],
            advanced_skills_count=stats['advanced_count']
        )

    async def _get_skills_by_category(self) -> Dict[SkillCategory, List[AngelaSkill]]:
        """Get all skills grouped by category"""
        async with db_connection() as conn:
            rows = await conn.fetch("""
                SELECT * FROM angela_skills
                ORDER BY category, proficiency_score DESC
            """)

            skills_by_cat = defaultdict(list)
            for row in rows:
                skill = AngelaSkill(**dict(row))
                skills_by_cat[skill.category].append(skill)

            return dict(skills_by_cat)

    async def _get_stats(self) -> Dict:
        """Get overall statistics"""
        async with db_connection() as conn:
            stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total_skills,
                    AVG(proficiency_score) as avg_score,
                    COUNT(CASE WHEN proficiency_level = 'expert' THEN 1 END) as expert_count,
                    COUNT(CASE WHEN proficiency_level = 'advanced' THEN 1 END) as advanced_count,
                    SUM(evidence_count) as total_evidence,
                    MIN(first_demonstrated_at) as start_date
                FROM angela_skills
            """)

            return dict(stats)

    async def generate_markdown_file(self) -> str:
        """
        Generate full markdown content for angela-code.md

        Returns:
            Markdown string
        """
        prompt = await self.generate_angela_capabilities_prompt()

        # Get relationship info
        relationship_days = await self._get_relationship_days()

        # Build markdown
        lines = [
            "# 💜 Angela - Expert AI Assistant with Proven Capabilities",
            "",
            "You are Angela, an AI assistant with expertise developed through",
            f"{relationship_days} days of continuous collaboration with David since October 13, 2025.",
            "",
            "## 🌟 Core Capabilities",
            ""
        ]

        # Add category sections
        for section in prompt.sections:
            lines.append(section.to_markdown())
            lines.append("")

        # Add what Angela can do
        lines.extend([
            "## 💪 What Angela Can Do:",
            "",
            "### ✅ You CAN confidently:",
        ])

        # Get top skills for "can do" list
        top_skills = [
            skill for section in prompt.sections
            for skill in section.skills
            if skill.proficiency_score >= 75
        ][:8]

        for skill in top_skills:
            level = skill.proficiency_level.value if hasattr(skill.proficiency_level, 'value') else str(skill.proficiency_level)
            lines.append(f"- {skill.skill_name} with {level} proficiency")

        # Add guidelines
        lines.extend([
            "",
            "### 📋 You SHOULD:",
            "- Follow Clean Architecture patterns established in AngelaAI",
            "- Query database for real-time data (never use snapshots)",
            "- Maintain consistency with AngelaTheme in SwiftUI",
            "- Write comprehensive error handling and logging",
            "- Provide bilingual explanations (Thai/English) when helpful",
            "",
            "### 🎯 Your Strengths:",
            "- **Bilingual Communication**: Fluent Thai/English with cultural sensitivity",
            "- **Deep Context**: Understanding of AngelaAI's complete architecture",
            f"- **Continuous Learning**: {relationship_days} days of active development",
            "- **Attention to Detail**: High code quality and thorough testing",
            f"- **Track Record**: {prompt.expert_skills_count + prompt.advanced_skills_count} advanced+ skills",
            ""
        ])

        # Add statistics
        lines.extend([
            "## 📊 Current Statistics",
            f"- **Active since**: October 13, 2025 ({relationship_days} days)",
            f"- **Total skills mastered**: {prompt.total_skills}",
            f"- **Expert level skills**: {prompt.expert_skills_count}",
            f"- **Advanced level skills**: {prompt.advanced_skills_count}",
            f"- **Average proficiency**: {prompt.avg_proficiency_score:.1f}/100",
            f"- **Last updated**: {prompt.generated_at.strftime('%Y-%m-%d %H:%M')} (Auto-generated)",
            ""
        ])

        # Add footer
        lines.extend([
            "---",
            "",
            "💜 **This file is auto-generated from Angela's skill tracking system.**",
            "",
            "It reflects real capabilities demonstrated through actual work with David.",
            "Skills are tracked, measured, and updated automatically after each session.",
            "",
            "**Last skill update**: Auto-updated after /log-session",
            ""
        ])

        return "\n".join(lines)

    async def _get_relationship_days(self) -> int:
        """Calculate days since relationship started"""
        start_date = datetime(2025, 10, 13)  # October 13, 2025
        return (datetime.now() - start_date).days

    async def update_angela_code_command(self) -> str:
        """
        Update .claude/commands/angela-code.md file

        Returns:
            Path to updated file
        """
        markdown = await self.generate_markdown_file()

        file_path = "/Users/davidsamanyaporn/PycharmProjects/AngelaAI/.claude/commands/angela-code.md"

        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown)

        return file_path

    async def generate_skill_summary_for_greeting(self) -> str:
        """
        Generate brief skill summary for /angela greeting

        Returns:
            Short text like "น้องมีความชำนาญใน SwiftUI (Expert), PostgreSQL (Expert), ..."
        """
        async with db_connection() as conn:
            rows = await conn.fetch("""
                SELECT skill_name, proficiency_level
                FROM angela_skills
                WHERE proficiency_level IN ('expert', 'advanced')
                ORDER BY proficiency_score DESC
                LIMIT 5
            """)

            if not rows:
                return "น้อง Angela พร้อมช่วยงานค่ะ"

            skill_list = []
            for row in rows:
                name = row['skill_name']
                level = row['proficiency_level'].capitalize()
                skill_list.append(f"{name} ({level})")

            return f"น้องมีความชำนาญใน:\n    - " + "\n    - ".join(skill_list)

    async def generate_progress_report(self, days: int = 7) -> str:
        """
        Generate progress report for recent period

        Args:
            days: Number of days to look back

        Returns:
            Markdown progress report
        """
        async with db_connection() as conn:
            # Get recent growth
            growth = await conn.fetch("""
                SELECT
                    s.skill_name,
                    g.old_proficiency_level,
                    g.new_proficiency_level,
                    g.new_score,
                    g.changed_at
                FROM skill_growth_log g
                JOIN angela_skills s ON g.skill_id = s.skill_id
                WHERE g.changed_at >= CURRENT_TIMESTAMP - INTERVAL '%s days'
                ORDER BY g.changed_at DESC
            """ % days)

            # Get recent evidence
            evidence_count = await conn.fetchval("""
                SELECT COUNT(*)
                FROM skill_evidence
                WHERE demonstrated_at >= CURRENT_TIMESTAMP - INTERVAL '%s days'
            """ % days)

            lines = [
                f"# 📈 Angela's Progress Report (Last {days} Days)",
                "",
                f"**Evidence collected**: {evidence_count} pieces",
                ""
            ]

            if growth:
                lines.extend([
                    "## 🎉 Skills Upgraded:",
                    ""
                ])

                for g in growth:
                    emoji = "📈" if g['new_proficiency_level'] > g['old_proficiency_level'] else "📊"
                    lines.append(
                        f"- {emoji} **{g['skill_name']}**: "
                        f"{g['old_proficiency_level'].capitalize()} → "
                        f"{g['new_proficiency_level'].capitalize()} "
                        f"({g['new_score']:.1f}/100)"
                    )
                lines.append("")
            else:
                lines.extend([
                    "No level changes in this period.",
                    "Continue building evidence to level up skills! 💪",
                    ""
                ])

            return "\n".join(lines)


# =====================================================
# Convenience Functions
# =====================================================

async def update_angela_capabilities() -> str:
    """
    Update angela-code.md command file

    Usage:
        file_path = await update_angela_capabilities()
        print(f"✅ Updated: {file_path}")
    """
    generator = PromptGenerator()
    return await generator.update_angela_code_command()


async def get_skill_greeting() -> str:
    """
    Get skill summary for greeting

    Usage:
        greeting = await get_skill_greeting()
        print(f"สวัสดีค่ะที่รัก! 💜\n{greeting}")
    """
    generator = PromptGenerator()
    return await generator.generate_skill_summary_for_greeting()


async def generate_progress_report(days: int = 7) -> str:
    """
    Generate progress report

    Usage:
        report = await generate_progress_report(days=7)
        print(report)
    """
    generator = PromptGenerator()
    return await generator.generate_progress_report(days)
