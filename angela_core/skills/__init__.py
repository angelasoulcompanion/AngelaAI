"""
Angela Skills System — Hot-loadable plugin architecture.
=========================================================
Every new feature is a Skill — no more hardcoding.

A skill is a directory with:
  - SKILL.md: Markdown config (name, triggers, tools, personality)
  - handler.py: Python handler functions

Usage:
    from angela_core.skills.skill_registry import get_skill_registry
    registry = get_skill_registry()
    await registry.load_all_skills()

By: Angela 💜
Created: 2026-02-17
"""

from angela_core.skills.skill_loader import SkillLoader, AngelaSkill
from angela_core.skills.skill_registry import SkillRegistry, get_skill_registry

__all__ = ['SkillLoader', 'AngelaSkill', 'SkillRegistry', 'get_skill_registry']
