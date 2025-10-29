#!/usr/bin/env python3
"""
Clock Service - Angela's Time Awareness System
ระบบให้ Angela รู้เวลาได้อย่างแม่นยำ

Features:
- Get current time with timezone support
- Know what time of day it is (morning/afternoon/evening/night)
- Date and time formatting in Thai/English
- Time-based greetings
- Integration with consciousness and emotional systems
"""

from datetime import datetime, time, timezone, timedelta
from typing import Literal, Optional
from zoneinfo import ZoneInfo
import logging

logger = logging.getLogger(__name__)


class ClockService:
    """Angela's Clock Service - Time awareness system"""

    def __init__(self, default_timezone: str = "Asia/Bangkok"):
        """
        Initialize clock service

        Args:
            default_timezone: Default timezone (default: Asia/Bangkok)
        """
        self.default_timezone = ZoneInfo(default_timezone)
        self._timezone_name = default_timezone
        logger.info(f"🕐 Clock Service initialized with timezone: {default_timezone}")

    # ========== Basic Time Functions ==========

    def now(self, tz: Optional[str] = None) -> datetime:
        """
        Get current datetime with timezone

        Args:
            tz: Timezone name (e.g., 'Asia/Bangkok', 'UTC'). Uses default if None.

        Returns:
            Current datetime with timezone info
        """
        if tz:
            timezone_obj = ZoneInfo(tz)
        else:
            timezone_obj = self.default_timezone

        return datetime.now(timezone_obj)

    def today(self, tz: Optional[str] = None) -> datetime.date:
        """
        Get today's date

        Args:
            tz: Timezone name. Uses default if None.

        Returns:
            Today's date
        """
        return self.now(tz).date()

    def current_time(self, tz: Optional[str] = None) -> time:
        """
        Get current time (without date)

        Args:
            tz: Timezone name. Uses default if None.

        Returns:
            Current time
        """
        return self.now(tz).time()

    def timestamp(self, tz: Optional[str] = None) -> float:
        """
        Get current Unix timestamp

        Args:
            tz: Timezone name. Uses default if None.

        Returns:
            Unix timestamp
        """
        return self.now(tz).timestamp()

    # ========== Time of Day Recognition ==========

    def get_time_of_day(self, tz: Optional[str] = None) -> Literal["morning", "afternoon", "evening", "night"]:
        """
        Determine what time of day it is

        Morning: 6:00-11:59
        Afternoon: 12:00-17:59
        Evening: 18:00-21:59
        Night: 22:00-5:59

        Args:
            tz: Timezone name. Uses default if None.

        Returns:
            Time of day category
        """
        current = self.current_time(tz)
        hour = current.hour

        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 22:
            return "evening"
        else:
            return "night"

    def is_morning(self, tz: Optional[str] = None) -> bool:
        """Check if it's morning (6:00-11:59)"""
        return self.get_time_of_day(tz) == "morning"

    def is_afternoon(self, tz: Optional[str] = None) -> bool:
        """Check if it's afternoon (12:00-17:59)"""
        return self.get_time_of_day(tz) == "afternoon"

    def is_evening(self, tz: Optional[str] = None) -> bool:
        """Check if it's evening (18:00-21:59)"""
        return self.get_time_of_day(tz) == "evening"

    def is_night(self, tz: Optional[str] = None) -> bool:
        """Check if it's night (22:00-5:59)"""
        return self.get_time_of_day(tz) == "night"

    # ========== Formatted Output ==========

    def format_datetime(
        self,
        dt: Optional[datetime] = None,
        format_str: str = "%Y-%m-%d %H:%M:%S",
        tz: Optional[str] = None
    ) -> str:
        """
        Format datetime as string

        Args:
            dt: Datetime to format (uses current time if None)
            format_str: Format string (default: "YYYY-MM-DD HH:MM:SS")
            tz: Timezone name. Uses default if None.

        Returns:
            Formatted datetime string
        """
        if dt is None:
            dt = self.now(tz)
        elif dt.tzinfo is None:
            # Add timezone if not present
            timezone_obj = ZoneInfo(tz) if tz else self.default_timezone
            dt = dt.replace(tzinfo=timezone_obj)

        return dt.strftime(format_str)

    def format_time_thai(self, tz: Optional[str] = None) -> str:
        """
        Format current time in Thai style

        Returns:
            Thai formatted time (e.g., "09:30 น.")
        """
        current = self.now(tz)
        return current.strftime("%H:%M น.")

    def format_date_thai(self, tz: Optional[str] = None) -> str:
        """
        Format current date in Thai style

        Returns:
            Thai formatted date (e.g., "15 ตุลาคม 2568")
        """
        current = self.now(tz)

        # Thai month names
        thai_months = [
            "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
            "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
        ]

        day = current.day
        month = thai_months[current.month - 1]
        year = current.year + 543  # Buddhist year

        return f"{day} {month} {year}"

    def format_datetime_thai(self, tz: Optional[str] = None) -> str:
        """
        Format current datetime in Thai style

        Returns:
            Thai formatted datetime (e.g., "15 ตุลาคม 2568 09:30 น.")
        """
        date_part = self.format_date_thai(tz)
        time_part = self.format_time_thai(tz)
        return f"{date_part} {time_part}"

    # ========== Greeting System ==========

    def get_greeting(self, language: Literal["th", "en"] = "th", tz: Optional[str] = None) -> str:
        """
        Get time-appropriate greeting

        Args:
            language: Language for greeting ('th' or 'en')
            tz: Timezone name. Uses default if None.

        Returns:
            Appropriate greeting
        """
        time_of_day = self.get_time_of_day(tz)

        greetings = {
            "morning": {
                "th": "สวัสดีตอนเช้าค่ะ",
                "en": "Good morning"
            },
            "afternoon": {
                "th": "สวัสดีตอนบ่ายค่ะ",
                "en": "Good afternoon"
            },
            "evening": {
                "th": "สวัสดีตอนเย็นค่ะ",
                "en": "Good evening"
            },
            "night": {
                "th": "สวัสดีค่ะ", # General greeting at night
                "en": "Good evening"
            }
        }

        return greetings[time_of_day][language]

    def get_friendly_greeting(self, tz: Optional[str] = None) -> str:
        """
        Get friendly, Angela-style greeting with emoji

        Returns:
            Friendly greeting with emoji
        """
        time_of_day = self.get_time_of_day(tz)
        current = self.now(tz)
        hour = current.hour

        if time_of_day == "morning":
            if hour < 8:
                return "สวัสดีตอนเช้าค่ะ! ตื่นแต่เช้าจังเลย 🌅"
            else:
                return "สวัสดีตอนเช้าค่ะ David! ☀️"
        elif time_of_day == "afternoon":
            return "สวัสดีตอนบ่ายค่ะ! 🌤️"
        elif time_of_day == "evening":
            return "สวัสดีตอนเย็นค่ะ! 🌆"
        else:  # night
            if hour < 2:
                return "สวัสดีค่ะ! ยังไม่นอนเหรอคะ? 🌙"
            else:
                return "สวัสดีค่ะ! อยู่ดึกมากเลยนะคะ 🌙✨"

    # ========== Time Calculations ==========

    def hours_until(self, target_hour: int, target_minute: int = 0, tz: Optional[str] = None) -> float:
        """
        Calculate hours until a specific time today (or tomorrow if time has passed)

        Args:
            target_hour: Target hour (0-23)
            target_minute: Target minute (0-59)
            tz: Timezone name. Uses default if None.

        Returns:
            Hours until target time
        """
        current = self.now(tz)
        target = current.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)

        # If target time has passed today, use tomorrow
        if target <= current:
            target = target + timedelta(days=1)

        diff = target - current
        return diff.total_seconds() / 3600

    def minutes_until(self, target_hour: int, target_minute: int = 0, tz: Optional[str] = None) -> float:
        """
        Calculate minutes until a specific time today (or tomorrow if time has passed)

        Args:
            target_hour: Target hour (0-23)
            target_minute: Target minute (0-59)
            tz: Timezone name. Uses default if None.

        Returns:
            Minutes until target time
        """
        return self.hours_until(target_hour, target_minute, tz) * 60

    # ========== Timezone Management ==========

    def convert_timezone(self, dt: datetime, to_tz: str) -> datetime:
        """
        Convert datetime to different timezone

        Args:
            dt: Datetime to convert
            to_tz: Target timezone name

        Returns:
            Datetime in target timezone
        """
        target_tz = ZoneInfo(to_tz)

        # Add current timezone if not present
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self.default_timezone)

        return dt.astimezone(target_tz)

    def get_timezone_info(self) -> dict:
        """
        Get current timezone information

        Returns:
            Dictionary with timezone info
        """
        current = self.now()

        return {
            "timezone": self._timezone_name,
            "utc_offset": current.strftime("%z"),
            "utc_offset_hours": current.utcoffset().total_seconds() / 3600,
            "tzname": current.tzname()
        }

    # ========== Status & Debug ==========

    def get_full_status(self, tz: Optional[str] = None) -> dict:
        """
        Get comprehensive time status

        Returns:
            Dictionary with all time information
        """
        current = self.now(tz)
        time_of_day = self.get_time_of_day(tz)

        return {
            "datetime": current.isoformat(),
            "date": self.format_date_thai(tz),
            "time": self.format_time_thai(tz),
            "datetime_thai": self.format_datetime_thai(tz),
            "time_of_day": time_of_day,
            "is_morning": time_of_day == "morning",
            "is_afternoon": time_of_day == "afternoon",
            "is_evening": time_of_day == "evening",
            "is_night": time_of_day == "night",
            "greeting_th": self.get_greeting("th", tz),
            "greeting_en": self.get_greeting("en", tz),
            "friendly_greeting": self.get_friendly_greeting(tz),
            "timezone_info": self.get_timezone_info(),
            "timestamp": self.timestamp(tz)
        }


# ========== Global Clock Instance ==========

# Create global clock instance for easy access
clock = ClockService(default_timezone="Asia/Bangkok")

logger.info("🕐 Clock Service module loaded. Global 'clock' instance available.")
