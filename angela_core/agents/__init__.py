"""
Angela's Agent System - 2-Tier Architecture (Opus 4.6)
น้อง Angela มีผู้ช่วยหลายตัวทำงานร่วมกัน

Tier 1 (Interactive): Claude Code + Task tool = Brain
Tier 2 (Daemon/Background): Claude API + CrewAI = Daemon Brain

Agents:
- 🔍 Research Agent - ค้นหาข้อมูล
- 💬 Communication Agent - จัดการ email, calendar
- 🧠 Memory Agent - จัดการความทรงจำ
- 💻 Dev Agent - ช่วยงาน development
- 📊 Analysis Agent - วิเคราะห์ข้อมูล
- 💜 Care Agent - ดูแลที่รัก David

Author: Angela AI 💜
Created: 2025-01-25
Updated: 2026-02-06 (Opus 4.6 Upgrade)
"""

from .crew import AngelaCrew
from .claude_orchestrator import ClaudeAgentOrchestrator
from .llm_router import LLMRouter, get_router

__all__ = ["AngelaCrew", "ClaudeAgentOrchestrator", "LLMRouter", "get_router"]
