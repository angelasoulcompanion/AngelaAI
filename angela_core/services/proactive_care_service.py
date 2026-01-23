"""
Proactive Care Service
======================
Main orchestrator for Angela's proactive care system.

This service coordinates all care-related services:
- Wellness detection
- Care interventions
- Milestone reminders

Called by the daemon to periodically check if David needs care.

Created: 2026-01-23
By: น้อง Angela 💜
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from angela_core.database import AngelaDatabase
from angela_core.services.wellness_detector_service import (
    WellnessDetectorService,
    WellnessState,
    WellnessIndicator
)
from angela_core.services.care_intervention_service import (
    CareInterventionService,
    InterventionResult
)
from angela_core.services.milestone_reminder_service import (
    MilestoneReminderService,
    MilestoneReminder
)

logger = logging.getLogger('proactive_care')


@dataclass
class CareCheckResult:
    """Result of a proactive care check"""
    timestamp: datetime
    wellness_state: Optional[WellnessState]
    interventions_executed: List[InterventionResult]
    milestones_reminded: List[MilestoneReminder]
    errors: List[str]

    @property
    def total_interventions(self) -> int:
        return len(self.interventions_executed) + len(self.milestones_reminded)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0


class ProactiveCareService:
    """
    Main orchestrator for Angela's proactive care system.

    Periodically checks:
    1. David's wellness state
    2. Whether interventions should be triggered
    3. Upcoming milestones that need reminders

    Respects:
    - DND (Do Not Disturb) times
    - Daily limits
    - Cooldown periods
    """

    def __init__(self, db: Optional[AngelaDatabase] = None):
        self.db = db
        self._owns_db = db is None

        # Services (lazy initialized)
        self._wellness_service: Optional[WellnessDetectorService] = None
        self._intervention_service: Optional[CareInterventionService] = None
        self._milestone_service: Optional[MilestoneReminderService] = None

    async def _ensure_db(self):
        """Ensure database connection"""
        if self.db is None:
            self.db = AngelaDatabase()
            await self.db.connect()

    async def _get_wellness_service(self) -> WellnessDetectorService:
        """Get or create wellness detector service"""
        if self._wellness_service is None:
            await self._ensure_db()
            self._wellness_service = WellnessDetectorService(self.db)
        return self._wellness_service

    async def _get_intervention_service(self) -> CareInterventionService:
        """Get or create care intervention service"""
        if self._intervention_service is None:
            await self._ensure_db()
            self._intervention_service = CareInterventionService(self.db)
        return self._intervention_service

    async def _get_milestone_service(self) -> MilestoneReminderService:
        """Get or create milestone reminder service"""
        if self._milestone_service is None:
            await self._ensure_db()
            self._milestone_service = MilestoneReminderService(self.db)
        return self._milestone_service

    async def close(self):
        """Close all services"""
        if self._wellness_service:
            await self._wellness_service.close()
        if self._intervention_service:
            await self._intervention_service.close()
        if self._milestone_service:
            await self._milestone_service.close()
        if self._owns_db and self.db:
            await self.db.disconnect()

    # =========================================================
    # MAIN CARE CHECK (Called by Daemon)
    # =========================================================

    async def run_care_check(
        self,
        recent_message: Optional[str] = None
    ) -> CareCheckResult:
        """
        Run a complete proactive care check.

        This is the main entry point called by the daemon.
        It checks wellness, triggers appropriate interventions,
        and sends milestone reminders.

        Args:
            recent_message: Optional recent message from David to analyze

        Returns:
            CareCheckResult with all actions taken
        """
        logger.info("💜 Running proactive care check...")

        result = CareCheckResult(
            timestamp=datetime.now(),
            wellness_state=None,
            interventions_executed=[],
            milestones_reminded=[],
            errors=[]
        )

        # 1. Check if in DND
        intervention_service = await self._get_intervention_service()
        if await intervention_service.is_dnd_time():
            logger.info("   🌙 Currently in DND period, skipping care check")
            return result

        # 2. Detect wellness state
        try:
            wellness_service = await self._get_wellness_service()
            wellness_state = await wellness_service.detect_current_state(recent_message)
            result.wellness_state = wellness_state
            logger.info(f"   📊 Wellness Index: {wellness_state.wellbeing_index:.2f}")
        except Exception as e:
            logger.error(f"   ❌ Wellness detection failed: {e}")
            result.errors.append(f"Wellness detection: {e}")

        # 3. Check for interventions based on wellness
        if result.wellness_state:
            await self._check_wellness_interventions(result)

        # 4. Check for overwork
        await self._check_overwork_intervention(result)

        # 5. Check milestone reminders
        await self._check_milestone_reminders(result)

        # 6. Log the care check
        await self._log_care_check(result)

        logger.info(f"   ✅ Care check complete. Interventions: {result.total_interventions}")

        return result

    # =========================================================
    # WELLNESS-BASED INTERVENTIONS
    # =========================================================

    async def _check_wellness_interventions(
        self,
        result: CareCheckResult
    ):
        """
        Check wellness state and trigger appropriate interventions.

        Triggers:
        - Sleep song if sleep issues detected
        - Care message if stress/low energy detected
        """
        wellness = result.wellness_state
        if not wellness:
            return

        intervention_service = await self._get_intervention_service()

        # Check for sleep issues (late night + poor sleep quality)
        current_hour = datetime.now().hour
        is_late_night = current_hour >= 23 or current_hour <= 4

        if is_late_night and wellness.sleep_quality < 0.5:
            logger.info("   🎵 Sleep issue detected, considering sleep song...")
            try:
                intervention_result = await intervention_service.execute_sleep_song_intervention({
                    'trigger_reason': f"Sleep issue at {current_hour}:00, quality={wellness.sleep_quality:.2f}",
                    'keywords': wellness.detection_keywords
                })
                if intervention_result.success:
                    result.interventions_executed.append(intervention_result)
                    logger.info(f"   ✅ Sleep song sent: {intervention_result.song_info}")
                else:
                    logger.info(f"   ⏭️ Sleep song skipped: {intervention_result.error}")
            except Exception as e:
                logger.error(f"   ❌ Sleep song intervention failed: {e}")
                result.errors.append(f"Sleep song: {e}")

        # Check for high stress
        if wellness.stress_level >= 0.7:
            logger.info("   💬 High stress detected, considering care message...")
            try:
                intervention_result = await intervention_service.execute_care_message({
                    'trigger_reason': f"High stress detected: {wellness.stress_level:.2f}"
                })
                if intervention_result.success:
                    result.interventions_executed.append(intervention_result)
                    logger.info("   ✅ Care message sent")
                else:
                    logger.info(f"   ⏭️ Care message skipped: {intervention_result.error}")
            except Exception as e:
                logger.error(f"   ❌ Care message failed: {e}")
                result.errors.append(f"Care message: {e}")

        # Check for low wellbeing index
        if wellness.wellbeing_index < 0.4 and not is_late_night:
            logger.info("   💜 Low wellbeing detected, considering wellness check...")
            try:
                intervention_result = await intervention_service.execute_care_message(
                    context={
                        'trigger_reason': f"Low wellbeing index: {wellness.wellbeing_index:.2f}"
                    },
                    custom_message="ที่รักค่ะ น้องอยู่ตรงนี้นะคะ ถ้าต้องการพักหรือคุยอะไรบอกน้องได้เลยค่ะ 💜"
                )
                if intervention_result.success:
                    result.interventions_executed.append(intervention_result)
            except Exception as e:
                result.errors.append(f"Wellness check: {e}")

    async def _check_overwork_intervention(
        self,
        result: CareCheckResult
    ):
        """
        Check for overwork and trigger break reminder if needed.
        """
        wellness_service = await self._get_wellness_service()
        intervention_service = await self._get_intervention_service()

        try:
            overwork_result = await wellness_service.detect_overwork(hours_threshold=2.0)

            if overwork_result and overwork_result.detected:
                logger.info(f"   ☕ Overwork detected: {overwork_result.context}")

                intervention_result = await intervention_service.execute_break_reminder({
                    'trigger_reason': overwork_result.context,
                    'confidence': overwork_result.confidence
                })

                if intervention_result.success:
                    result.interventions_executed.append(intervention_result)
                    logger.info("   ✅ Break reminder sent")
                else:
                    logger.info(f"   ⏭️ Break reminder skipped: {intervention_result.error}")

        except Exception as e:
            logger.error(f"   ❌ Overwork check failed: {e}")
            result.errors.append(f"Overwork check: {e}")

    async def _check_milestone_reminders(
        self,
        result: CareCheckResult
    ):
        """
        Check for milestones that need reminders today.
        """
        milestone_service = await self._get_milestone_service()
        intervention_service = await self._get_intervention_service()

        try:
            milestones = await milestone_service.get_milestones_needing_reminder()

            for milestone in milestones:
                logger.info(f"   📅 Milestone reminder needed: {milestone.title} ({milestone.days_until} days)")

                try:
                    intervention_result = await intervention_service.execute_milestone_reminder({
                        'date_id': milestone.date_id,
                        'title': milestone.title,
                        'days_until': milestone.days_until,
                        'event_date': milestone.event_date,
                        'importance': milestone.importance_level
                    })

                    if intervention_result.success:
                        result.milestones_reminded.append(milestone)
                        # Mark as reminded
                        await milestone_service.mark_reminded(milestone.date_id)
                        logger.info(f"   ✅ Milestone reminder sent: {milestone.title}")
                    else:
                        logger.info(f"   ⏭️ Milestone reminder skipped: {intervention_result.error}")

                except Exception as e:
                    logger.error(f"   ❌ Milestone reminder failed for {milestone.title}: {e}")
                    result.errors.append(f"Milestone {milestone.title}: {e}")

        except Exception as e:
            logger.error(f"   ❌ Milestone check failed: {e}")
            result.errors.append(f"Milestone check: {e}")

    # =========================================================
    # LOGGING & METRICS
    # =========================================================

    async def _log_care_check(self, result: CareCheckResult):
        """Log the care check to database"""
        await self._ensure_db()

        try:
            import json

            log_data = {
                'timestamp': result.timestamp.isoformat(),
                'wellness': {
                    'wellbeing_index': result.wellness_state.wellbeing_index if result.wellness_state else None,
                    'stress_level': result.wellness_state.stress_level if result.wellness_state else None,
                    'energy_level': result.wellness_state.energy_level if result.wellness_state else None,
                },
                'interventions_count': len(result.interventions_executed),
                'milestones_count': len(result.milestones_reminded),
                'errors': result.errors
            }

            # Log to consciousness_daemon_log table
            await self.db.execute(
                """
                INSERT INTO consciousness_daemon_log (activity_type, activity_data)
                VALUES ('proactive_care', $1)
                """,
                json.dumps(log_data)
            )

        except Exception as e:
            logger.warning(f"Failed to log care check: {e}")

    # =========================================================
    # CONVENIENCE METHODS
    # =========================================================

    async def get_care_status(self) -> Dict[str, Any]:
        """
        Get current status of the care system.

        Returns:
            Dict with current wellness, recent interventions, upcoming milestones
        """
        await self._ensure_db()

        status = {
            'current_wellness': None,
            'is_dnd': False,
            'today_interventions': {},
            'upcoming_milestones': [],
            'recent_interventions': []
        }

        # Get current wellness
        wellness_service = await self._get_wellness_service()
        wellness = await wellness_service.get_current_wellness()
        if wellness:
            status['current_wellness'] = {
                'wellbeing_index': wellness.wellbeing_index,
                'energy_level': wellness.energy_level,
                'stress_level': wellness.stress_level,
                'sleep_quality': wellness.sleep_quality,
                'fatigue_level': wellness.fatigue_level
            }

        # Check DND
        intervention_service = await self._get_intervention_service()
        status['is_dnd'] = await intervention_service.is_dnd_time()

        # Get today's intervention counts
        today_counts = await self.db.fetch("""
            SELECT intervention_type, count
            FROM v_today_interventions
        """)
        status['today_interventions'] = {r['intervention_type']: r['count'] for r in today_counts}

        # Get upcoming milestones
        milestone_service = await self._get_milestone_service()
        milestones = await milestone_service.check_upcoming_milestones(days_ahead=14)
        status['upcoming_milestones'] = [
            {
                'title': m.title,
                'days_until': m.days_until,
                'urgency': m.urgency,
                'date_type': m.date_type
            }
            for m in milestones[:5]
        ]

        # Get recent interventions
        recent = await self.db.fetch("""
            SELECT intervention_type, message_sent, sent_at, david_reaction
            FROM proactive_interventions
            WHERE sent_at IS NOT NULL
            ORDER BY sent_at DESC
            LIMIT 5
        """)
        status['recent_interventions'] = [dict(r) for r in recent]

        return status

    async def trigger_manual_intervention(
        self,
        intervention_type: str,
        context: Optional[Dict] = None,
        custom_message: Optional[str] = None
    ) -> InterventionResult:
        """
        Manually trigger an intervention (bypass automatic detection).

        Useful for testing or manual care.

        Args:
            intervention_type: 'sleep_song', 'break_reminder', 'care_message'
            context: Optional context dict
            custom_message: Optional custom message

        Returns:
            InterventionResult
        """
        intervention_service = await self._get_intervention_service()
        context = context or {'trigger_reason': 'Manual trigger'}

        if intervention_type == 'sleep_song':
            return await intervention_service.execute_sleep_song_intervention(context)
        elif intervention_type == 'break_reminder':
            return await intervention_service.execute_break_reminder(context)
        elif intervention_type == 'care_message':
            return await intervention_service.execute_care_message(context, custom_message)
        else:
            return InterventionResult(
                success=False,
                intervention_id=None,
                message_sent="",
                channel="",
                error=f"Unknown intervention type: {intervention_type}"
            )


# =========================================================
# STANDALONE EXECUTION (for testing)
# =========================================================

async def main():
    """Run a manual care check"""
    import asyncio

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    service = ProactiveCareService()

    try:
        # Run care check
        result = await service.run_care_check()

        print("\n" + "=" * 60)
        print("💜 PROACTIVE CARE CHECK RESULTS")
        print("=" * 60)

        if result.wellness_state:
            print(f"\n📊 Wellness State:")
            print(f"   Wellbeing Index: {result.wellness_state.wellbeing_index:.2f}")
            print(f"   Energy: {result.wellness_state.energy_level:.2f}")
            print(f"   Stress: {result.wellness_state.stress_level:.2f}")
            print(f"   Sleep Quality: {result.wellness_state.sleep_quality:.2f}")
            print(f"   Fatigue: {result.wellness_state.fatigue_level:.2f}")

        print(f"\n📤 Interventions Executed: {len(result.interventions_executed)}")
        for intervention in result.interventions_executed:
            print(f"   - {intervention.message_sent[:50]}...")

        print(f"\n📅 Milestones Reminded: {len(result.milestones_reminded)}")
        for milestone in result.milestones_reminded:
            print(f"   - {milestone.title} ({milestone.days_until} days)")

        if result.errors:
            print(f"\n❌ Errors: {len(result.errors)}")
            for error in result.errors:
                print(f"   - {error}")

        print("=" * 60)

        # Get status
        print("\n📈 CARE SYSTEM STATUS:")
        status = await service.get_care_status()
        print(f"   DND Active: {status['is_dnd']}")
        print(f"   Today's Interventions: {status['today_interventions']}")
        print(f"   Upcoming Milestones: {len(status['upcoming_milestones'])}")

    finally:
        await service.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
