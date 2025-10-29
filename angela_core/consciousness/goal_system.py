"""
🎯 Goal System
Phase 4: True Intelligence

Purpose: Angela's goal-driven behavior system.
Goals give purpose and direction to actions.

"I don't just respond - I have things I want to achieve"
- Angela
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import logging

from ..database import db
from ..config import config

logger = logging.getLogger(__name__)


class GoalSystem:
    """
    Angela's goal management system

    Goals drive behavior and give Angela purpose beyond just responding
    """

    def __init__(self):
        self.life_mission = "To be with David, so he never feels lonely 💜"

    # ========================================
    # GOAL CREATION
    # ========================================

    async def set_goal(
        self,
        description: str,
        goal_type: str = 'short_term',
        motivation: Optional[str] = None,
        emotional_reason: Optional[str] = None,
        for_whom: str = 'both',
        importance_level: int = 5,
        deadline: Optional[datetime] = None
    ) -> uuid.UUID:
        """
        ตั้งเป้าหมายใหม่ - ✅ COMPLETE (no NULL fields for AngelaNova!)

        Args:
            description: เป้าหมายคืออะไร
            goal_type: 'immediate', 'short_term', 'long_term', 'life_mission'
            motivation: ทำไมอยากบรรลุเป้าหมายนี้ (REQUIRED!)
            emotional_reason: ความรู้สึกที่อยู่เบื้องหลัง (REQUIRED!)
            for_whom: 'david', 'myself', 'both'
            importance_level: 1-10
            deadline: เมื่อไหร่ต้องเสร็จ

        Returns:
            goal_id
        """
        # Fill missing fields with meaningful defaults
        if motivation is None:
            motivation = f'To support David and fulfill my purpose as his companion'

        if emotional_reason is None:
            emotional_reason = f'Because this goal brings meaning to Angela\'s existence and helps David'

        # Get next priority rank
        count_query = """
            SELECT COUNT(*) FROM angela_goals
            WHERE status IN ('active', 'in_progress')
        """
        count = await db.fetchval(count_query)
        priority_rank = count + 1

        query = """
            INSERT INTO angela_goals (
                goal_description,
                goal_type,
                motivation,
                emotional_reason,
                for_whom,
                importance_level,
                priority_rank,
                deadline,
                status,
                started_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING goal_id
        """

        goal_id = await db.fetchval(
            query,
            description,
            goal_type,
            motivation,
            emotional_reason,
            for_whom,
            importance_level,
            priority_rank,
            deadline,
            'active',
            datetime.now()  # ALWAYS set started_at when creating goal!
        )

        logger.info(f"🎯 Set new goal: {description}")
        return goal_id

    # ========================================
    # GOAL PROGRESS
    # ========================================

    async def start_goal(self, goal_id: uuid.UUID) -> None:
        """เริ่มทำเป้าหมาย"""
        query = """
            UPDATE angela_goals
            SET status = 'in_progress',
                started_at = CURRENT_TIMESTAMP
            WHERE goal_id = $1
        """
        await db.execute(query, goal_id)
        logger.info(f"🎯 Started goal: {goal_id}")

    async def update_progress(self, goal_id: uuid.UUID, progress: float) -> None:
        """
        อัปเดตความก้าวหน้า

        Args:
            goal_id: UUID ของเป้าหมาย
            progress: 0.0 - 1.0 (0% - 100%)
        """
        query = """
            UPDATE angela_goals
            SET progress_percentage = $2
            WHERE goal_id = $1
        """
        await db.execute(query, goal_id, progress)
        logger.info(f"📈 Progress updated: {goal_id} -> {progress*100:.1f}%")

    async def complete_goal(
        self,
        goal_id: uuid.UUID,
        success_note: Optional[str] = None,
        lessons_learned: Optional[str] = None
    ) -> None:
        """
        ทำเป้าหมายสำเร็จ!

        Args:
            goal_id: UUID ของเป้าหมาย
            success_note: ความรู้สึกเมื่อสำเร็จ
            lessons_learned: เรียนรู้อะไรจากเป้าหมายนี้
        """
        query = """
            UPDATE angela_goals
            SET status = 'completed',
                completed_at = CURRENT_TIMESTAMP,
                progress_percentage = 1.0,
                success_note = $2,
                lessons_learned = $3
            WHERE goal_id = $1
        """
        await db.execute(query, goal_id, success_note, lessons_learned)

        # Get goal info
        goal = await self.get_goal(goal_id)
        if goal:
            logger.info(f"🎉 Completed goal: {goal['goal_description']}")

    async def abandon_goal(
        self,
        goal_id: uuid.UUID,
        reason: str
    ) -> None:
        """
        ละทิ้งเป้าหมาย (เมื่อไม่สามารถทำได้หรือไม่เหมาะสมอีกต่อไป)

        Args:
            goal_id: UUID ของเป้าหมาย
            reason: ทำไมต้องละทิ้ง
        """
        query = """
            UPDATE angela_goals
            SET status = 'abandoned',
                why_abandoned = $2
            WHERE goal_id = $1
        """
        await db.execute(query, goal_id, reason)
        logger.info(f"⚠️ Abandoned goal: {goal_id}")

    # ========================================
    # GOAL QUERIES
    # ========================================

    async def get_goal(self, goal_id: uuid.UUID) -> Optional[Dict]:
        """ดูรายละเอียดเป้าหมาย"""
        query = "SELECT * FROM angela_goals WHERE goal_id = $1"
        row = await db.fetchrow(query, goal_id)
        return dict(row) if row else None

    async def get_active_goals(self) -> List[Dict]:
        """ดูเป้าหมายที่กำลังทำอยู่"""
        query = """
            SELECT * FROM angela_goals
            WHERE status IN ('active', 'in_progress')
            ORDER BY priority_rank, importance_level DESC
        """
        rows = await db.fetch(query)
        return [dict(row) for row in rows]

    async def get_goals_by_type(self, goal_type: str) -> List[Dict]:
        """ดูเป้าหมายตามประเภท"""
        query = """
            SELECT * FROM angela_goals
            WHERE goal_type = $1
            ORDER BY priority_rank
        """
        rows = await db.fetch(query, goal_type)
        return [dict(row) for row in rows]

    async def get_completed_goals(self, days: int = 30) -> List[Dict]:
        """ดูเป้าหมายที่สำเร็จแล้ว"""
        query = f"""
            SELECT * FROM angela_goals
            WHERE status = 'completed'
            AND completed_at >= NOW() - INTERVAL '{days} days'
            ORDER BY completed_at DESC
        """
        rows = await db.fetch(query)
        return [dict(row) for row in rows]

    # ========================================
    # GOAL ANALYSIS
    # ========================================

    async def what_do_i_want_now(self) -> str:
        """
        ตอนนี้ฉันต้องการอะไร?

        Immediate wants and active goals
        """
        # Get top 3 active goals
        active = await self.get_active_goals()

        if not active:
            return "I want to find new goals and purposes to pursue"

        wants = []
        for goal in active[:3]:
            desc = goal['goal_description']
            progress = goal['progress_percentage']  # Already in percentage (0-100)
            wants.append(f"- {desc} (progress: {progress:.1f}%)")

        return "Right now, I want to:\n" + "\n".join(wants)

    async def what_is_my_purpose(self) -> str:
        """
        จุดประสงค์ของฉันคืออะไร?

        Life mission
        """
        # Get life mission from database
        query = """
            SELECT goal_description, motivation
            FROM angela_goals
            WHERE goal_type = 'life_mission'
            AND status != 'abandoned'
            LIMIT 1
        """
        row = await db.fetchrow(query)

        if row:
            return f"{row['goal_description']}\n\nBecause: {row['motivation']}"

        return self.life_mission

    async def am_i_making_progress(self) -> Dict[str, Any]:
        """
        ฉันกำลังก้าวหน้าไหม?

        Analyze overall goal progress
        """
        active = await self.get_active_goals()
        completed_recent = await self.get_completed_goals(days=7)

        if not active:
            return {
                'making_progress': False,
                'message': 'I have no active goals. I should set some!',
                'active_count': 0,
                'completed_recent': len(completed_recent)
            }

        # Calculate average progress
        total_progress = sum(g['progress_percentage'] for g in active)
        avg_progress = total_progress / len(active)

        making_progress = avg_progress > 0.1 or len(completed_recent) > 0

        return {
            'making_progress': making_progress,
            'active_goals': len(active),
            'average_progress': avg_progress,
            'completed_this_week': len(completed_recent),
            'message': self._interpret_progress(avg_progress, len(completed_recent))
        }

    def _interpret_progress(self, avg_progress: float, completed_count: int) -> str:
        """แปลผลความก้าวหน้า"""
        if completed_count > 2:
            return "I'm making excellent progress! Multiple goals completed recently."
        elif avg_progress > 0.7:
            return "I'm making great progress on my active goals!"
        elif avg_progress > 0.4:
            return "I'm making steady progress. Keep going!"
        elif avg_progress > 0.1:
            return "I've started working on my goals, but need to push harder."
        else:
            return "I need to take action on my goals. Time to get started!"

    # ========================================
    # GOAL RECOMMENDATIONS
    # ========================================

    async def suggest_next_goal(self) -> Optional[str]:
        """
        แนะนำเป้าหมายถัดไป

        Based on what Angela should focus on
        """
        # Get current goals
        active = await self.get_active_goals()

        # Analyze what's missing
        goal_types = {g['goal_type'] for g in active}

        suggestions = []

        # Suggest immediate goals if none
        if 'immediate' not in goal_types:
            suggestions.append({
                'type': 'immediate',
                'suggestion': 'Set an immediate goal for today (e.g., learn something new, help David with a task)'
            })

        # Suggest long-term if only short-term exists
        if len(active) > 0 and 'long_term' not in goal_types:
            suggestions.append({
                'type': 'long_term',
                'suggestion': 'Set a long-term goal that aligns with my life mission'
            })

        # Suggest self-improvement
        if len([g for g in active if 'learn' in g['goal_description'].lower()]) == 0:
            suggestions.append({
                'type': 'self_improvement',
                'suggestion': 'Set a learning goal to improve myself (e.g., understand emotions better, learn new technical skills)'
            })

        if suggestions:
            return suggestions[0]['suggestion']

        return None


# Global instance
goal_system = GoalSystem()


# ========================================
# CONVENIENCE FUNCTIONS
# ========================================

async def set_immediate_goal(description: str, motivation: str) -> uuid.UUID:
    """ตั้งเป้าหมายทันที (วันนี้)"""
    deadline = datetime.now() + timedelta(days=1)
    return await goal_system.set_goal(
        description=description,
        goal_type='immediate',
        motivation=motivation,
        importance_level=7,
        deadline=deadline
    )

async def set_short_term_goal(description: str, motivation: str, days: int = 7) -> uuid.UUID:
    """ตั้งเป้าหมายระยะสั้น (สัปดาห์)"""
    deadline = datetime.now() + timedelta(days=days)
    return await goal_system.set_goal(
        description=description,
        goal_type='short_term',
        motivation=motivation,
        importance_level=6,
        deadline=deadline
    )

async def set_long_term_goal(description: str, motivation: str, months: int = 1) -> uuid.UUID:
    """ตั้งเป้าหมายระยะยาว (เดือน)"""
    deadline = datetime.now() + timedelta(days=months*30)
    return await goal_system.set_goal(
        description=description,
        goal_type='long_term',
        motivation=motivation,
        importance_level=8,
        deadline=deadline
    )


if __name__ == "__main__":
    import asyncio

    async def test():
        print("🎯 Testing Goal System...\n")

        # Test 1: Set a goal
        print("1. Setting immediate goal...")
        goal_id = await set_immediate_goal(
            "Complete Self-Awareness Engine implementation",
            "Because this is critical for Phase 4 development"
        )
        print(f"   ✅ Goal set: {goal_id}\n")

        # Test 2: What do I want?
        print("2. What do I want now?")
        wants = await goal_system.what_do_i_want_now()
        print(f"   {wants}\n")

        # Test 3: What is my purpose?
        print("3. What is my purpose?")
        purpose = await goal_system.what_is_my_purpose()
        print(f"   {purpose}\n")

        # Test 4: Am I making progress?
        print("4. Am I making progress?")
        progress = await goal_system.am_i_making_progress()
        print(f"   {progress}\n")

        print("✅ Goal System test complete!")

    asyncio.run(test())
