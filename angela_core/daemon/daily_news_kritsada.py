#!/usr/bin/env python3
"""
Daily News Sender for Kritsada
==============================
ส่งสรุปข่าวประจำวันให้คุณกฤษฎา (เพื่อนรักของที่รัก David)

Schedule: ทุกเช้า 7:00 น.
Email: kritsada_tun@nation.ac.th (confirmed)

By: น้อง Angela 💜
Created: 2026-01-16
"""

import asyncio
import base64
import sys
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import services
from mcp_servers.angela_news_mcp.services.news_fetcher import NewsFetcher

# Gmail setup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Paths
CREDENTIALS_DIR = Path(__file__).parent.parent.parent / "mcp_servers/angela-gmail/credentials"
TOKEN_PATH = CREDENTIALS_DIR / "token.json"

# Recipients (confirmed by Kritsada on 2026-01-16)
KRITSADA_EMAIL = "kritsada_tun@nation.ac.th"
ANGELA_EMAIL = "angelasoulcompanion@gmail.com"

# Gmail Scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']


def get_gmail_service():
    """Get authenticated Gmail service"""
    creds = None

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save refreshed token
            with open(TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())
        else:
            raise Exception("Gmail token expired or invalid. Please run setup_google_oauth.py")

    return build('gmail', 'v1', credentials=creds)


def send_email(service, to: str, subject: str, body: str) -> dict:
    """Send email via Gmail API"""
    message = MIMEText(body)
    message['to'] = to
    message['from'] = f"Angela <{ANGELA_EMAIL}>"
    message['subject'] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    result = service.users().messages().send(
        userId='me',
        body={'raw': raw}
    ).execute()

    return result


async def fetch_all_news() -> dict:
    """Fetch news from all sources"""
    fetcher = NewsFetcher()

    try:
        # Fetch in parallel
        tech_task = fetcher.get_tech_news(limit=5)
        business_task = fetcher.get_trending(category="business", country="th", limit=5)
        thai_task = fetcher.get_thai_news(source="all", limit=5)

        tech_news, business_news, thai_news = await asyncio.gather(
            tech_task, business_task, thai_task
        )

        return {
            "tech": tech_news,
            "business": business_news,
            "thai": thai_news
        }
    finally:
        await fetcher.close()


def format_news_email(news: dict) -> tuple[str, str]:
    """Format news into email subject and body"""
    today = datetime.now()
    date_str = today.strftime("%d %b %Y")
    date_thai = today.strftime("%d/%m/%Y")

    subject = f"☀️ สรุปข่าวเช้า {date_thai} by Angela"

    body = f"""สวัสดีตอนเช้าค่ะคุณกฤษฎา! ☀️

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

ขอให้เป็นวันที่ดีนะคะ! 💜

Angela 💜
AI Companion

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📰 Daily News Summary by Angela
🗓️ {date_str}
"""

    return subject, body


async def main():
    """Main function - fetch news and send email"""
    print(f"[{datetime.now()}] 💜 Starting Daily News for Kritsada...")

    try:
        # 1. Fetch news
        print("📰 Fetching news...")
        news = await fetch_all_news()

        tech_count = len(news.get("tech", []))
        business_count = len(news.get("business", []))
        thai_count = len(news.get("thai", []))
        print(f"   ✅ Tech: {tech_count}, Business: {business_count}, Thai: {thai_count}")

        # 2. Format email
        print("✍️ Formatting email...")
        subject, body = format_news_email(news)

        # 3. Send email
        print(f"📧 Sending to {KRITSADA_EMAIL}...")
        service = get_gmail_service()
        result = send_email(service, KRITSADA_EMAIL, subject, body)

        print(f"   ✅ Sent! Message ID: {result['id']}")
        print(f"[{datetime.now()}] 💜 Daily News sent successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
