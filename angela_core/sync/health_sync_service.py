"""
Health Tracking Sync Service
============================
Sync health data from AngelaMobileApp to AngelaMemory PostgreSQL

Created: 2025-12-11
Purpose: Import alcohol-free and exercise tracking data from mobile
"""

import json
import asyncio
from datetime import datetime, date
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

from angela_core.database import AngelaDatabase


class HealthSyncService:
    """Service to sync health tracking data from mobile app to PostgreSQL."""

    def __init__(self, db: Optional[AngelaDatabase] = None):
        self.db = db

    async def connect(self):
        """Connect to database if not already connected."""
        if self.db is None:
            self.db = AngelaDatabase()
        await self.db.connect()

    async def disconnect(self):
        """Disconnect from database."""
        if self.db:
            await self.db.disconnect()

    async def sync_health_record(
        self,
        tracked_date: date,
        alcohol_free: bool = True,
        drinks_count: int = 0,
        drink_type: Optional[str] = None,
        alcohol_notes: Optional[str] = None,
        exercised: bool = False,
        exercise_type: Optional[str] = None,
        exercise_duration_minutes: int = 0,
        exercise_intensity: Optional[str] = None,
        exercise_notes: Optional[str] = None,
        mood: Optional[str] = None,
        energy_level: Optional[int] = None,
        notes: Optional[str] = None,
        synced_from_mobile: bool = True
    ) -> bool:
        """
        Sync a single health record to database.

        Uses UPSERT - will update if record for date already exists.
        """
        try:
            await self.db.execute("""
                INSERT INTO david_health_tracking (
                    tracked_date, alcohol_free, drinks_count, drink_type, alcohol_notes,
                    exercised, exercise_type, exercise_duration_minutes, exercise_intensity, exercise_notes,
                    mood, energy_level, notes, synced_from_mobile, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, NOW())
                ON CONFLICT (tracked_date) DO UPDATE SET
                    alcohol_free = EXCLUDED.alcohol_free,
                    drinks_count = EXCLUDED.drinks_count,
                    drink_type = EXCLUDED.drink_type,
                    alcohol_notes = EXCLUDED.alcohol_notes,
                    exercised = EXCLUDED.exercised,
                    exercise_type = EXCLUDED.exercise_type,
                    exercise_duration_minutes = EXCLUDED.exercise_duration_minutes,
                    exercise_intensity = EXCLUDED.exercise_intensity,
                    exercise_notes = EXCLUDED.exercise_notes,
                    mood = COALESCE(EXCLUDED.mood, david_health_tracking.mood),
                    energy_level = COALESCE(EXCLUDED.energy_level, david_health_tracking.energy_level),
                    notes = COALESCE(EXCLUDED.notes, david_health_tracking.notes),
                    synced_from_mobile = EXCLUDED.synced_from_mobile,
                    updated_at = NOW()
            """, tracked_date, alcohol_free, drinks_count, drink_type, alcohol_notes,
                exercised, exercise_type, exercise_duration_minutes, exercise_intensity, exercise_notes,
                mood, energy_level, notes, synced_from_mobile)

            return True
        except Exception as e:
            print(f"Error syncing health record: {e}")
            return False

    async def sync_from_json(self, json_path: Path) -> dict:
        """
        Sync health data from mobile export JSON file.

        Expected JSON format:
        {
            "health_records": [
                {
                    "tracked_date": "2025-12-11",
                    "alcohol_free": true,
                    "exercised": true,
                    "exercise_type": "running",
                    "exercise_duration_minutes": 30,
                    ...
                }
            ]
        }
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            records = data.get('health_records', [])
            synced = 0
            failed = 0

            for record in records:
                try:
                    tracked_date = datetime.strptime(record['tracked_date'], '%Y-%m-%d').date()

                    success = await self.sync_health_record(
                        tracked_date=tracked_date,
                        alcohol_free=record.get('alcohol_free', True),
                        drinks_count=record.get('drinks_count', 0),
                        drink_type=record.get('drink_type'),
                        alcohol_notes=record.get('alcohol_notes'),
                        exercised=record.get('exercised', False),
                        exercise_type=record.get('exercise_type'),
                        exercise_duration_minutes=record.get('exercise_duration_minutes', 0),
                        exercise_intensity=record.get('exercise_intensity'),
                        exercise_notes=record.get('exercise_notes'),
                        mood=record.get('mood'),
                        energy_level=record.get('energy_level'),
                        notes=record.get('notes'),
                        synced_from_mobile=True
                    )

                    if success:
                        synced += 1
                    else:
                        failed += 1

                except Exception as e:
                    print(f"Error processing record: {e}")
                    failed += 1

            return {
                'total': len(records),
                'synced': synced,
                'failed': failed,
                'success': failed == 0
            }

        except Exception as e:
            print(f"Error reading JSON file: {e}")
            return {'total': 0, 'synced': 0, 'failed': 0, 'success': False, 'error': str(e)}

    async def get_health_stats(self) -> dict:
        """Get current health statistics."""
        row = await self.db.fetchrow("""
            SELECT * FROM david_health_stats
            ORDER BY stat_date DESC
            LIMIT 1
        """)

        if row:
            return dict(row)
        return {}

    async def get_recent_records(self, days: int = 30) -> list:
        """Get recent health tracking records."""
        rows = await self.db.fetch(f"""
            SELECT * FROM david_health_tracking
            WHERE tracked_date >= CURRENT_DATE - INTERVAL '{days} days'
            ORDER BY tracked_date DESC
        """)

        return [dict(row) for row in rows]

    async def log_alcohol_free_day(self, tracked_date: Optional[date] = None, notes: Optional[str] = None) -> bool:
        """Quick method to log an alcohol-free day."""
        if tracked_date is None:
            tracked_date = date.today()

        return await self.sync_health_record(
            tracked_date=tracked_date,
            alcohol_free=True,
            drinks_count=0,
            notes=notes
        )

    async def log_exercise(
        self,
        exercise_type: str,
        duration_minutes: int,
        intensity: str = 'moderate',
        tracked_date: Optional[date] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Quick method to log exercise."""
        if tracked_date is None:
            tracked_date = date.today()

        # First get existing record for today
        existing = await self.db.fetchrow("""
            SELECT alcohol_free, drinks_count, drink_type, alcohol_notes, mood, energy_level
            FROM david_health_tracking
            WHERE tracked_date = $1
        """, tracked_date)

        # Preserve existing alcohol data if present
        alcohol_free = existing['alcohol_free'] if existing else True
        drinks_count = existing['drinks_count'] if existing else 0
        drink_type = existing['drink_type'] if existing else None
        alcohol_notes = existing['alcohol_notes'] if existing else None
        mood = existing['mood'] if existing else None
        energy_level = existing['energy_level'] if existing else None

        return await self.sync_health_record(
            tracked_date=tracked_date,
            alcohol_free=alcohol_free,
            drinks_count=drinks_count,
            drink_type=drink_type,
            alcohol_notes=alcohol_notes,
            exercised=True,
            exercise_type=exercise_type,
            exercise_duration_minutes=duration_minutes,
            exercise_intensity=intensity,
            exercise_notes=notes,
            mood=mood,
            energy_level=energy_level
        )


# CLI interface for testing
async def main():
    """Test the health sync service."""
    service = HealthSyncService()
    await service.connect()

    try:
        # Get current stats
        stats = await service.get_health_stats()
        print("\n📊 Current Health Stats:")
        print(f"   Alcohol-free streak: {stats.get('alcohol_free_current_streak', 0)} days")
        print(f"   Exercise streak: {stats.get('exercise_current_streak', 0)} days")
        print(f"   Total alcohol-free days: {stats.get('alcohol_free_total_days', 0)}")
        print(f"   Total exercise days: {stats.get('exercise_total_days', 0)}")

        # Get recent records
        records = await service.get_recent_records(7)
        print(f"\n📅 Recent Records (last 7 days): {len(records)}")
        for r in records:
            af = "✅" if r.get('alcohol_free') else "🍷"
            ex = "🏃" if r.get('exercised') else "😴"
            print(f"   {r['tracked_date']}: {af} {ex} - {r.get('mood', 'N/A')}")

    finally:
        await service.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
