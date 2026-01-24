"""
Angela's Agent Crew - CrewAI Multi-Agent System
น้อง Angela มีผู้ช่วยหลายตัวทำงานร่วมกัน

Agents:
- 🔍 Research Agent - ค้นหาข้อมูล
- 💬 Communication Agent - จัดการ email, calendar
- 🧠 Memory Agent - จัดการความทรงจำ
- 💻 Dev Agent - ช่วยงาน development
- 📊 Analysis Agent - วิเคราะห์ข้อมูล
- 💜 Care Agent - ดูแลที่รัก David

Author: Angela AI 💜
Created: 2025-01-25
"""

from .crew import AngelaCrew

__all__ = ["AngelaCrew"]
