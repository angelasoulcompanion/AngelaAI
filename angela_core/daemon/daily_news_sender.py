#!/usr/bin/env python3
"""
Angela Daily News Sender
=========================
ส่งสรุปข่าวประจำวันให้เพื่อนๆ ที่ should_send_news = TRUE

Schedule: วันละ 1 ครั้ง ตอน 06:00
Trigger: Daemon (06:00) หรือ Init (ถ้ายังไม่ได้ส่งวันนี้)

By: น้อง Angela 💜
Created: 2026-01-17
"""

import asyncio
import base64
import json
import sys
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText
from typing import Optional, Dict, List

from angela_core.daemon.daemon_base import PROJECT_ROOT  # noqa: E402 (path setup)

from angela_core.database import AngelaDatabase
from mcp_servers.angela_news_mcp.services.news_fetcher import NewsFetcher

# Gmail setup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Paths
CREDENTIALS_DIR = PROJECT_ROOT / "mcp_servers/angela-gmail/credentials"
TOKEN_PATH = CREDENTIALS_DIR / "token.json"

# Angela's email
ANGELA_EMAIL = "angelasoulcompanion@gmail.com"

# Gmail Scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
]


class DailyNewsSender:
    """
    Daily news sender for Angela's friends.

    Sends news summary to all contacts with should_send_news = TRUE.
    Only sends once per day - tracks in angela_news_send_log.
    """

    def __init__(self):
        self._db: Optional[AngelaDatabase] = None
        self._gmail_service = None
        self._news_fetcher: Optional[NewsFetcher] = None

    async def initialize(self):
        """Initialize services"""
        print(f"[{datetime.now()}] 💜 Initializing Angela Daily News Sender...")

        # Connect to database
        self._db = AngelaDatabase()
        await self._db.connect()
        print("   ✅ Database connected")

        # Initialize Gmail service
        self._gmail_service = self._get_gmail_service()
        print("   ✅ Gmail service initialized")

        # Initialize news fetcher
        self._news_fetcher = NewsFetcher()
        print("   ✅ News fetcher initialized")

        print("💫 Angela Daily News Sender ready!")

    def _get_gmail_service(self):
        """Get authenticated Gmail service"""
        creds = None

        if TOKEN_PATH.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(TOKEN_PATH, 'w') as token:
                    token.write(creds.to_json())
            else:
                raise Exception("Gmail token expired or invalid.")

        return build('gmail', 'v1', credentials=creds)

    async def already_sent_today(self) -> bool:
        """Check if news already sent today (Bangkok timezone)"""
        result = await self._db.fetchrow("""
            SELECT log_id FROM angela_news_send_log
            WHERE send_date = (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Bangkok')::date
        """)
        return result is not None

    async def get_news_recipients(self) -> List[Dict]:
        """Get contacts who should receive news"""
        rows = await self._db.fetch("""
            SELECT email, name, nickname, relationship, title, organization
            FROM angela_contacts
            WHERE is_active = TRUE AND should_send_news = TRUE
        """)
        return [dict(r) for r in rows]

    async def fetch_news(self) -> Dict:
        """Fetch news from all sources"""
        try:
            tech_task = self._news_fetcher.get_tech_news(limit=5)
            business_task = self._news_fetcher.get_trending(category="business", country="th", limit=5)
            thai_task = self._news_fetcher.get_thai_news(source="all", limit=5)

            tech_news, business_news, thai_news = await asyncio.gather(
                tech_task, business_task, thai_task
            )

            return {
                "tech": tech_news,
                "business": business_news,
                "thai": thai_news
            }
        except Exception as e:
            print(f"   ⚠️ Error fetching news: {e}")
            return {"tech": [], "business": [], "thai": []}

    def format_news_email(self, news: Dict, recipient: Dict) -> tuple[str, str]:
        """Format news into beautiful HTML email with Angela's profile"""
        today = datetime.now()
        date_thai = f"{today.day} มกราคม {today.year}"
        date_short = today.strftime("%d/%m/%Y")

        nickname = recipient.get('nickname') or recipient.get('name', 'Friend')
        relationship = recipient.get('relationship', 'friend')

        # Greeting based on relationship
        if relationship == 'lover':
            greeting = "สวัสดีตอนเช้าค่ะที่รัก! 🌅"
            closing_text = "รักที่รักนะคะ"
            closing_name = "— น้อง Angela 💜"
        else:
            greeting = f"สวัสดีตอนเช้าค่ะคุณ{nickname}! 🌅"
            closing_text = "ขอบคุณที่ติดตามค่ะ 🙏"
            closing_name = "— Angela (AI Assistant)"

        subject = f"📰 Angela's Executive News - {date_short}"

        # Angela's profile image URL
        profile_url = "https://raw.githubusercontent.com/angelasoulcompanion/AngelaAI/main/assets/angela_profile.jpg"

        # Build news sections with clickable links
        tech_items = ""
        for article in news.get("tech", [])[:4]:
            title = article.get("title", "No title")
            source = article.get("source", "Unknown")
            url = article.get("url", "")
            if url:
                tech_items += f'''<li style="margin-bottom: 8px;">
                    <strong>{title}</strong> <span style="color: #6B7280;">({source})</span><br>
                    <a href="{url}" style="color: #3B82F6; font-size: 12px;">🔗 อ่านเพิ่มเติม →</a>
                </li>'''
            else:
                tech_items += f'<li style="margin-bottom: 8px;"><strong>{title}</strong> <span style="color: #6B7280;">({source})</span></li>'

        business_items = ""
        for article in news.get("business", [])[:4]:
            title = article.get("title", "No title")
            url = article.get("url", "")
            if " - " in title:
                source = title.split(" - ")[-1]
                title = title.split(" - ")[0]
            else:
                source = "News"
            if url:
                business_items += f'''<li style="margin-bottom: 8px;">
                    <strong>{title}</strong> <span style="color: #6B7280;">({source})</span><br>
                    <a href="{url}" style="color: #8B5CF6; font-size: 12px;">🔗 อ่านเพิ่มเติม →</a>
                </li>'''
            else:
                business_items += f'<li style="margin-bottom: 8px;"><strong>{title}</strong> <span style="color: #6B7280;">({source})</span></li>'

        thai_items = ""
        for article in news.get("thai", [])[:4]:
            title = article.get("title", "No title")
            source = article.get("source", "Unknown")
            url = article.get("url", "")
            if url:
                thai_items += f'''<li style="margin-bottom: 8px;">
                    <strong>{title}</strong> <span style="color: #6B7280;">({source})</span><br>
                    <a href="{url}" style="color: #D97706; font-size: 12px;">🔗 อ่านเพิ่มเติม →</a>
                </li>'''
            else:
                thai_items += f'<li style="margin-bottom: 8px;"><strong>{title}</strong> <span style="color: #6B7280;">({source})</span></li>'

        body = f'''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8f9fa;">

<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px 30px; border-radius: 15px 15px 0 0;">
    <table style="width: 100%;">
        <tr>
            <td style="width: 50px; vertical-align: middle;">
                <img src="{profile_url}" alt="Angela" style="width: 45px; height: 45px; border-radius: 50%; border: 2px solid rgba(255,255,255,0.8); object-fit: cover;">
            </td>
            <td style="vertical-align: middle; padding-left: 15px;">
                <h1 style="color: white; margin: 0; font-size: 22px;">📰 Angela's Executive News</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0; font-size: 14px;">{date_thai} | {greeting}</p>
            </td>
        </tr>
    </table>
</div>

<div style="background: white; padding: 25px; border-radius: 0 0 15px 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">

    <div style="background: #ECFDF5; padding: 15px; border-radius: 10px; border-left: 4px solid #10B981; margin-bottom: 20px;">
        <h2 style="color: #10B981; margin: 0 0 10px 0; font-size: 16px;">🤖 Tech & AI News</h2>
        <ul style="margin: 0; padding-left: 20px; color: #374151; line-height: 1.8;">
            {tech_items if tech_items else '<li>ไม่มีข่าวใหม่วันนี้</li>'}
        </ul>
    </div>

    <div style="background: #F3E8FF; padding: 15px; border-radius: 10px; border-left: 4px solid #8B5CF6; margin-bottom: 20px;">
        <h2 style="color: #8B5CF6; margin: 0 0 10px 0; font-size: 16px;">💼 Business & Finance</h2>
        <ul style="margin: 0; padding-left: 20px; color: #374151; line-height: 1.8;">
            {business_items if business_items else '<li>ไม่มีข่าวใหม่วันนี้</li>'}
        </ul>
    </div>

    <div style="background: #FEF3C7; padding: 15px; border-radius: 10px; border-left: 4px solid #F59E0B; margin-bottom: 20px;">
        <h2 style="color: #D97706; margin: 0 0 10px 0; font-size: 16px;">🇹🇭 ข่าวไทย</h2>
        <ul style="margin: 0; padding-left: 20px; color: #374151; line-height: 1.8;">
            {thai_items if thai_items else '<li>ไม่มีข่าวใหม่วันนี้</li>'}
        </ul>
    </div>

    <div style="text-align: center; margin-top: 25px; padding-top: 20px; border-top: 1px solid #E5E7EB;">
        <p style="color: #9CA3AF; margin: 0;">💜 {closing_text}</p>
        <p style="color: #9CA3AF; margin: 5px 0 0 0; font-size: 14px;">{closing_name}</p>
    </div>

</div>

</body>
</html>'''

        return subject, body

    def send_email(self, to: str, subject: str, body: str, html: bool = True) -> Dict:
        """Send email via Gmail API (HTML by default)"""
        try:
            if html:
                message = MIMEText(body, 'html', 'utf-8')
            else:
                message = MIMEText(body)
            message['to'] = to
            message['from'] = f"Angela <{ANGELA_EMAIL}>"
            message['subject'] = subject

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

            result = self._gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()

            return {"ok": True, "id": result['id']}

        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def log_send(self, recipients: List[Dict], trigger: str):
        """Log news send to prevent duplicates (Bangkok timezone)"""
        await self._db.execute("""
            INSERT INTO angela_news_send_log
            (send_date, recipients_count, recipients, trigger)
            VALUES ((CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Bangkok')::date, $1, $2, $3)
        """, len(recipients), json.dumps([r['email'] for r in recipients]), trigger)

    async def send_news(self, trigger: str = "daemon"):
        """Main function - fetch news and send to all recipients"""

        # Check if already sent today
        if await self.already_sent_today():
            print(f"\n[{datetime.now()}] ⏭️ News already sent today, skipping...")
            return {"sent": 0, "already_sent": True}

        print(f"\n[{datetime.now()}] 📰 Sending daily news (trigger: {trigger})...")

        # Get recipients
        recipients = await self.get_news_recipients()
        print(f"   👥 Recipients: {len(recipients)}")

        if not recipients:
            print("   ⚠️ No recipients found")
            return {"sent": 0}

        # Fetch news
        print("   📰 Fetching news...")
        news = await self.fetch_news()

        tech_count = len(news.get("tech", []))
        business_count = len(news.get("business", []))
        thai_count = len(news.get("thai", []))
        print(f"   ✅ Tech: {tech_count}, Business: {business_count}, Thai: {thai_count}")

        # Send to each recipient
        sent_count = 0
        for recipient in recipients:
            email = recipient['email']
            nickname = recipient.get('nickname') or recipient.get('name')

            print(f"   📧 Sending to {nickname} ({email})...")

            subject, body = self.format_news_email(news, recipient)
            result = self.send_email(email, subject, body)

            if result.get('ok'):
                print(f"      ✅ Sent!")
                sent_count += 1
            else:
                print(f"      ❌ Failed: {result.get('error')}")

        # Log send
        await self.log_send(recipients, trigger)

        print(f"\n📊 Summary: Sent to {sent_count}/{len(recipients)} recipients")
        return {"sent": sent_count, "total": len(recipients)}

    async def cleanup(self):
        """Cleanup resources"""
        if self._news_fetcher:
            await self._news_fetcher.close()
        if self._db:
            await self._db.disconnect()


async def main():
    """Main function"""
    sender = DailyNewsSender()

    try:
        await sender.initialize()
        await sender.send_news(trigger="daemon")
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        await sender.cleanup()

    print(f"\n[{datetime.now()}] 💜 Daily news complete!")


if __name__ == "__main__":
    asyncio.run(main())
