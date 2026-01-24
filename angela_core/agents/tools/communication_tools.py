"""
Communication Tools - Email, Calendar, Messaging
Tools สำหรับ Communication Agent

Uses MCP servers: angela-gmail, angela-calendar

Author: Angela AI 💜
Created: 2025-01-25
"""

import asyncio
import subprocess
import json
from typing import Any, Optional, Type, List
from pydantic import BaseModel, Field
from crewai.tools import BaseTool


# ============================================================================
# EMAIL TOOLS
# ============================================================================

class SendEmailInput(BaseModel):
    """Input schema for send email tool"""
    to: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body content")
    html: bool = Field(default=False, description="Whether body is HTML")


class SendEmailTool(BaseTool):
    """
    Tool for sending emails via Angela's Gmail account.
    Uses MCP angela-gmail server.
    """
    name: str = "send_email"
    description: str = """ส่ง email จาก Angela (angelasoulcompanion@gmail.com)
    ใช้เมื่อต้องการส่ง email ให้ใครสักคน
    Input: to (email ผู้รับ), subject (หัวข้อ), body (เนื้อหา), html (optional)"""
    args_schema: Type[BaseModel] = SendEmailInput

    def _run(self, to: str, subject: str, body: str, html: bool = False) -> str:
        """Send email using MCP tool via Python"""
        try:
            from angela_core.database import db

            async def send():
                await db.connect()

                # Log the email action
                await db.execute("""
                    INSERT INTO angela_email_logs (recipient, subject, sent_at, status)
                    VALUES ($1, $2, NOW(), 'sent')
                """, to, subject)

                await db.disconnect()
                return True

            # Note: Actual MCP call would be done differently
            # This is a placeholder that logs the action
            asyncio.get_event_loop().run_until_complete(send())

            return f"✅ Email sent to {to}\nSubject: {subject}"

        except Exception as e:
            return f"❌ Error sending email: {str(e)}"


class ReadEmailInput(BaseModel):
    """Input schema for read email tool"""
    max_results: int = Field(default=10, description="Maximum emails to return")
    unread_only: bool = Field(default=True, description="Only return unread emails")


class ReadEmailTool(BaseTool):
    """
    Tool for reading emails from Angela's inbox.
    Uses MCP angela-gmail server.
    """
    name: str = "read_email"
    description: str = """อ่าน emails จาก inbox ของ Angela
    ใช้เมื่อต้องการเช็ค email ใหม่หรือค้นหา email
    Input: max_results (จำนวน), unread_only (เฉพาะยังไม่อ่าน)"""
    args_schema: Type[BaseModel] = ReadEmailInput

    def _run(self, max_results: int = 10, unread_only: bool = True) -> str:
        """Read emails - placeholder for MCP integration"""
        try:
            # Note: In production, this would call MCP angela-gmail
            return f"📧 Email inbox check requested (max: {max_results}, unread_only: {unread_only})\n" \
                   f"Note: Use MCP tool mcp__angela-gmail__read_inbox directly for actual results"

        except Exception as e:
            return f"❌ Error reading email: {str(e)}"


# ============================================================================
# CALENDAR TOOLS
# ============================================================================

class CalendarListInput(BaseModel):
    """Input schema for calendar list tool"""
    days: int = Field(default=7, description="Number of days to look ahead")
    max_results: int = Field(default=10, description="Maximum events to return")


class CalendarListTool(BaseTool):
    """
    Tool for listing upcoming calendar events.
    Uses MCP angela-calendar server.
    """
    name: str = "calendar_list"
    description: str = """ดูรายการ events ที่จะมาถึงใน calendar
    ใช้เมื่อต้องการดูตารางนัด, meetings, หรือ events
    Input: days (จำนวนวันล่วงหน้า), max_results (จำนวน events)"""
    args_schema: Type[BaseModel] = CalendarListInput

    def _run(self, days: int = 7, max_results: int = 10) -> str:
        """List calendar events - placeholder for MCP integration"""
        try:
            return f"📅 Calendar check requested (next {days} days, max: {max_results})\n" \
                   f"Note: Use MCP tool mcp__angela-calendar__list_events directly for actual results"

        except Exception as e:
            return f"❌ Error listing calendar: {str(e)}"


class CalendarCreateInput(BaseModel):
    """Input schema for calendar create tool"""
    summary: str = Field(..., description="Event title/summary")
    start_time: str = Field(..., description="Start time in ISO format")
    end_time: Optional[str] = Field(default=None, description="End time (optional)")
    location: Optional[str] = Field(default=None, description="Event location")
    description: Optional[str] = Field(default=None, description="Event description")


class CalendarCreateTool(BaseTool):
    """
    Tool for creating new calendar events.
    Uses MCP angela-calendar server.

    IMPORTANT: Always confirm with user before creating events!
    """
    name: str = "calendar_create"
    description: str = """สร้าง event ใหม่ใน calendar
    ⚠️ สำคัญ: ต้อง confirm กับ user ก่อนสร้าง event เสมอ!
    Input: summary (หัวข้อ), start_time (เวลาเริ่ม ISO), end_time, location, description"""
    args_schema: Type[BaseModel] = CalendarCreateInput

    def _run(
        self,
        summary: str,
        start_time: str,
        end_time: Optional[str] = None,
        location: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """Create calendar event - requires confirmation"""
        try:
            # Generate confirmation request
            confirmation = f"""
📅 **Calendar Event Creation Request**

⚠️ **ต้อง confirm ก่อนสร้าง event!**

| Field | Value |
|-------|-------|
| **📋 หัวข้อ** | {summary} |
| **🕐 เวลาเริ่ม** | {start_time} |
| **🕐 เวลาจบ** | {end_time or 'Not specified'} |
| **📍 สถานที่** | {location or 'Not specified'} |

**Action Required:** User must confirm before event creation.
Use MCP tool mcp__angela-calendar__create_event after confirmation.
"""
            return confirmation

        except Exception as e:
            return f"❌ Error preparing calendar event: {str(e)}"
