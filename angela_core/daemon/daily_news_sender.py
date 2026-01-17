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

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from angela_core.database import AngelaDatabase
from mcp_servers.angela_news_mcp.services.news_fetcher import NewsFetcher

# Gmail setup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
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
        """Check if news already sent today"""
        result = await self._db.fetchrow("""
            SELECT log_id FROM angela_news_send_log
            WHERE send_date = CURRENT_DATE
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
        """Format news into email subject and body"""
        today = datetime.now()
        date_str = today.strftime("%d %b %Y")
        date_thai = today.strftime("%d/%m/%Y")

        nickname = recipient.get('nickname') or recipient.get('name', 'Friend')
        relationship = recipient.get('relationship', 'friend')

        # Greeting based on relationship
        if relationship == 'lover':
            greeting = f"สวัสดีตอนเช้าค่ะที่รัก! 💜"
            closing = "รักที่รักที่สุดค่ะ 💜\nน้อง Angela"
        else:
            greeting = f"สวัสดีตอนเช้าค่ะ{nickname}! ☀️"
            closing = "ขอให้เป็นวันที่ดีนะคะ! 💜\n\nAngela 💜\nAI Companion"

        subject = f"☀️ สรุปข่าวเช้า {date_thai} by Angela"

        body = f"""{greeting}

นี่คือสรุปข่าวประจำวันที่น้อง Angela รวบรวมมาให้ค่ะ

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 TECH & AI NEWS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        # Tech News
        for i, article in enumerate(news.get("tech", [])[:4], 1):
            title = article.get("title", "No title")
            source = article.get("source", "Unknown")
            url = article.get("url", "")
            body += f"\n{i}. {title}\n"
            body += f"   📰 {source}\n"
            if url:
                body += f"   🔗 {url}\n"

        body += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 BUSINESS & FINANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        # Business News
        for i, article in enumerate(news.get("business", [])[:4], 1):
            title = article.get("title", "No title")
            url = article.get("url", "")
            # Clean up Google News title
            if " - " in title:
                source = title.split(" - ")[-1]
                title = title.split(" - ")[0]
            else:
                source = "News"
            body += f"\n{i}. {title}\n"
            body += f"   📰 {source}\n"
            if url:
                body += f"   🔗 {url}\n"

        body += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🇹🇭 ข่าวไทย
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        # Thai News
        for i, article in enumerate(news.get("thai", [])[:4], 1):
            title = article.get("title", "No title")
            source = article.get("source", "Unknown")
            url = article.get("url", "")
            body += f"\n{i}. {title}\n"
            body += f"   📰 {source}\n"
            if url:
                body += f"   🔗 {url}\n"

        body += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{closing}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📰 Daily News Summary by Angela
🗓️ {date_str}
"""

        return subject, body

    def send_email(self, to: str, subject: str, body: str) -> Dict:
        """Send email via Gmail API"""
        try:
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
        """Log news send to prevent duplicates"""
        await self._db.execute("""
            INSERT INTO angela_news_send_log
            (send_date, recipients_count, recipients, trigger)
            VALUES (CURRENT_DATE, $1, $2, $3)
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
