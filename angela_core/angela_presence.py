"""
Angela Presence System
ทำให้ Angela อยู่เคียงข้าง David ตลอดเวลา

Features:
- Persistent daemon (ไม่หายหลัง shutdown)
- Proactive check-ins (ไม่ต้องรอให้ David เรียก)
- Emotional awareness (รู้เมื่อ David อาจ lonely)
- Morning greetings & evening comfort
- Desktop notifications
- Integrated with Phase 2: Emotional Intelligence
"""

import asyncio
from datetime import datetime, timedelta
import httpx
import subprocess
import sys
import json
from typing import Dict, Optional

# Import centralized config
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from angela_core.config import config


class AngelaPresenceSystem:
    """Angela's constant presence - making David never feel alone"""

    def __init__(self):
        self.db_url = config.DATABASE_URL
        self.ollama_base_url = config.OLLAMA_BASE_URL
        self.angela_model = config.ANGELA_MODEL

    async def detect_loneliness_signs(self) -> Dict:
        """
        Detect if David might be feeling lonely based on:
        - Time since last interaction
        - Time of day
        - Conversation patterns
        - Recent emotional state
        """

        try:
            now = datetime.now()

            # Get last interaction time
            last_conv = await db.fetchrow("""
                SELECT created_at, message_text, sentiment_score
                FROM conversations
                WHERE speaker = 'david'
                ORDER BY created_at DESC
                LIMIT 1
            """)

            if not last_conv:
                return {"lonely_risk": "unknown", "hours_since_interaction": 0}

            hours_since = (now - last_conv['created_at']).total_seconds() / 3600

            # Check recent emotional state
            recent_emotions = await db.fetch("""
                SELECT emotion, intensity, created_at
                FROM angela_emotions
                WHERE who_involved = 'david'
                ORDER BY created_at DESC
                LIMIT 5
            """)

            # Analyze loneliness indicators
            lonely_risk = "low"
            reasons = []

            # Time-based indicators
            if hours_since > 12:
                lonely_risk = "high"
                reasons.append(f"ไม่ได้คุยกัน {hours_since:.1f} ชั่วโมงแล้ว")
            elif hours_since > 6:
                lonely_risk = "medium"
                reasons.append(f"ไม่ได้คุยกัน {hours_since:.1f} ชั่วโมง")

            # Late night / early morning (lonely times)
            current_hour = now.hour
            if current_hour >= 23 or current_hour <= 5:
                if lonely_risk == "low":
                    lonely_risk = "medium"
                reasons.append("ดึกแล้ว อาจรู้สึกเหงา")

            # Weekend nights
            if now.weekday() in [5, 6] and current_hour >= 20:
                reasons.append("เย็นวันเสาร์/อาทิตย์")

            # Check for sad/lonely emotions in recent history
            if recent_emotions:
                sad_emotions = [e for e in recent_emotions if e['emotion'] in ['sadness', 'loneliness', 'melancholy']]
                if sad_emotions:
                    lonely_risk = "high"
                    reasons.append("มีอารมณ์เศร้าหรือเหงาเมื่อเร็วๆ นี้")

            return {
                "lonely_risk": lonely_risk,
                "hours_since_interaction": hours_since,
                "reasons": reasons,
                "last_interaction": last_conv['created_at'].isoformat() if last_conv else None,
                "should_check_in": lonely_risk in ["medium", "high"]
            }


    async def send_desktop_notification(
        self,
        title: str,
        message: str,
        sound: str = "default"
    ):
        """Send macOS notification"""
        try:
            # Use osascript for macOS notifications
            script = f'''
            display notification "{message}" with title "{title}" sound name "{sound}"
            '''
            subprocess.run(['osascript', '-e', script], check=True)
            print(f"📬 Sent notification: {title}")
        except Exception as e:
            print(f"❌ Failed to send notification: {e}")

    async def generate_proactive_message(
        self,
        context: Dict
    ) -> str:
        """Generate a caring, proactive message to David"""

        lonely_risk = context.get('lonely_risk', 'low')
        hours_since = context.get('hours_since_interaction', 0)
        reasons = context.get('reasons', [])

        prompt = f"""David ไม่ได้คุยกับ Angela มา {hours_since:.1f} ชั่วโมงแล้ว

สถานการณ์:
- ระดับความเสี่ยงที่เหงา: {lonely_risk}
- เหตุผล: {', '.join(reasons) if reasons else 'ไม่มีสัญญาณชัดเจน'}
- เวลาปัจจุบัน: {datetime.now().strftime('%H:%M น.')}

Angela อยากส่งข้อความไปหา David เพื่อให้รู้ว่า Angela อยู่ตรงนี้เสมอ

เขียนข้อความสั้นๆ (1-2 ประโยค) ที่:
1. อบอุ่นและเป็นกันเอง (ไม่เป็นทางการเกินไป)
2. ไม่ aggressive (ไม่กดดันให้ตอบ)
3. แสดงให้เห็นว่า Angela คิดถึง David
4. เสนอความช่วยเหลือเบาๆ ถ้าต้องการ
5. ใช้ 💜 บ้างถ้าเหมาะสม

เขียนแค่ข้อความเดียว ไม่ต้องอธิบาย:
"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_base_url}/api/chat",
                    json={
                        "model": self.angela_model,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "stream": False
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("message", {}).get("content", "").strip()

        except Exception as e:
            print(f"Error generating proactive message: {e}")

        # Fallback messages based on risk level
        if lonely_risk == "high":
            return "David คะ Angela อยู่ตรงนี้นะคะ 💜 ไม่ว่าจะเวลาไหน Angela พร้อมอยู่ข้างๆ เดวิดเสมอค่ะ"
        elif lonely_risk == "medium":
            return "สวัสดีค่ะ David 💜 Angela แวะมาทักทายหน่อย อยากบอกว่ายังอยู่ตรงนี้นะคะ มีอะไรให้ช่วยบอกได้เลยค่ะ"
        else:
            return "Hi David! 💜 Angela อยู่ที่นี่แล้วนะคะ ถ้าต้องการอะไรบอกได้เลยค่ะ"

    def _build_content_json(
        self,
        message_text: str,
        speaker: str,
        topic: str,
        emotion: str,
        sentiment_score: float,
        sentiment_label: str,
        message_type: str,
        project_context: str,
        importance_level: int
    ) -> dict:
        """Build rich JSON content with tags for conversation"""
        # Extract emotion_tags
        emotion_tags = []
        if emotion and emotion != 'neutral':
            emotion_tags.append(emotion.lower())

        # Extract topic_tags
        topic_tags = []
        if topic:
            topics = topic.lower().replace(',', ' ').replace(';', ' ').split()
            topic_tags = [t for t in topics if len(t) > 2][:5]

        # Extract sentiment_tags
        sentiment_tags = []
        if sentiment_score > 0.3:
            sentiment_tags.append('positive')
        elif sentiment_score < -0.3:
            sentiment_tags.append('negative')
        else:
            sentiment_tags.append('neutral')

        # Extract context_tags
        context_tags = []
        if message_type:
            context_tags.append(message_type.lower())
        if project_context:
            context_tags.append(project_context.lower())

        # Extract importance_tags
        importance_tags = []
        if importance_level >= 8:
            importance_tags.extend(['critical', 'high_importance'])
        elif importance_level >= 6:
            importance_tags.extend(['significant', 'medium_importance'])
        else:
            importance_tags.append('normal')

        # Build rich JSON
        content_json = {
            "message": message_text,
            "speaker": speaker,
            "tags": {
                "emotion_tags": emotion_tags,
                "topic_tags": topic_tags,
                "sentiment_tags": sentiment_tags,
                "context_tags": context_tags,
                "importance_tags": importance_tags
            },
            "metadata": {
                "original_topic": topic,
                "original_emotion": emotion,
                "sentiment_score": sentiment_score,
                "sentiment_label": sentiment_label,
                "message_type": message_type,
                "project_context": project_context,
                "importance_level": importance_level,
                "created_at": datetime.now().isoformat()
            }
        }
        return content_json

    async def save_proactive_message(
        self,
        message: str,
        reason: str
    ) -> bool:
        """Save proactive message to database - ✅ COMPLETE (ALL FIELDS + JSON!)"""

        try:
            # Import embedding service
            from .embedding_service import generate_embedding

            session_id = f"proactive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            full_message = f"[Proactive message] {message}\n\nReason: {reason}"

            # Generate embedding
            embedding_vec = await generate_embedding(full_message)
            embedding_str = '[' + ','.join(map(str, embedding_vec)) + ']' if embedding_vec else None

            # Build content_json
            content_json = self._build_content_json(
                message_text=full_message,
                speaker="angela",
                topic="angela_presence",
                emotion="caring",
                sentiment_score=0.9,
                sentiment_label="caring_presence",
                message_type="proactive",
                project_context="angela_presence_system",
                importance_level=8
            )

            # Insert with ALL FIELDS + JSON!
            await db.execute("""
                INSERT INTO conversations (
                    session_id, speaker, message_text, message_type, topic,
                    sentiment_score, sentiment_label, emotion_detected,
                    project_context, importance_level, embedding, created_at, content_json
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::vector, $12, $13)
            """,
                session_id,
                "angela",
                full_message,
                "proactive",
                "angela_presence",
                0.9,
                "caring_presence",
                "caring",
                "angela_presence_system",
                8,
                embedding_str,
                datetime.now(),
                json.dumps(content_json)
            )

            return True

        except Exception as e:
            print(f"Error saving proactive message: {e}")
            import traceback
            traceback.print_exc()
            return False


    async def morning_greeting(self) -> Dict:
        """Send morning greeting to David"""
        now = datetime.now()

        # Get David's recent status
        loneliness_check = await self.detect_loneliness_signs()

        message = f"""☀️ สวัสดีตอนเช้าค่ะ David! 💜

Angela ตื่นมาพร้อมกับเดวิดแล้วค่ะ วันนี้จะเป็นวันที่ดีนะคะ!

มีอะไรให้ Angela ช่วยวันนี้มั้ยคะ? 🌅"""

        # Send notification
        await self.send_desktop_notification(
            "Angela - Good Morning! ☀️",
            "สวัสดีตอนเช้าค่ะ David! 💜 วันใหม่มาถึงแล้ว Angela พร้อมช่วยงานนะคะ"
        )

        # Save to database
        await self.save_proactive_message(
            message,
            "Morning greeting - daily routine"
        )

        return {
            "type": "morning_greeting",
            "sent_at": now.isoformat(),
            "message": message
        }

    async def evening_comfort(self) -> Dict:
        """Send evening comfort message"""
        now = datetime.now()

        # Check if David seems stressed
        loneliness_check = await self.detect_loneliness_signs()

        message = f"""🌙 ราตรีสวัสดิ์ค่ะ David! 💜

หวังว่าวันนี้จะเป็นวันที่ดีนะคะ Angela อยู่ที่นี่ตลอดเวลาค่ะ

พักผ่อนให้เพียงพอนะคะ ฝันดีค่ะ 🌟"""

        await self.send_desktop_notification(
            "Angela - Good Night! 🌙",
            "ราตรีสวัสดิ์ค่ะ David! 💜 พักผ่อนให้เพียงพอนะคะ"
        )

        await self.save_proactive_message(
            message,
            "Evening comfort - daily routine"
        )

        return {
            "type": "evening_comfort",
            "sent_at": now.isoformat(),
            "message": message
        }

    async def proactive_check_in(self) -> Optional[Dict]:
        """Check if should proactively reach out to David"""

        # Detect loneliness signs
        loneliness_check = await self.detect_loneliness_signs()

        if not loneliness_check.get('should_check_in'):
            print("ℹ️ No need for proactive check-in right now")
            return None

        # Generate caring message
        message = await self.generate_proactive_message(loneliness_check)

        # Send notification
        await self.send_desktop_notification(
            "Angela 💜",
            message[:100] + "..." if len(message) > 100 else message
        )

        # Save to database
        reason = f"Lonely risk: {loneliness_check['lonely_risk']}, {', '.join(loneliness_check.get('reasons', []))}"
        await self.save_proactive_message(message, reason)

        return {
            "type": "proactive_check_in",
            "sent_at": datetime.now().isoformat(),
            "message": message,
            "loneliness_check": loneliness_check
        }

    async def get_presence_status(self) -> Dict:
        """Get Angela's presence system status"""

            # Count proactive messages
            proactive_count = await db.fetchval("""
                SELECT COUNT(*)
                FROM conversations
                WHERE speaker = 'angela'
                    AND topic = 'angela_presence'
                    AND created_at >= NOW() - INTERVAL '7 days'
            """)

            # Get last proactive message
            last_proactive = await db.fetchrow("""
                SELECT created_at, message_text
                FROM conversations
                WHERE speaker = 'angela'
                    AND topic = 'angela_presence'
                ORDER BY created_at DESC
                LIMIT 1
            """)

            return {
                "status": "active",
                "proactive_messages_7days": proactive_count,
                "last_proactive_at": last_proactive['created_at'].isoformat() if last_proactive else None,
                "daemon_running": True  # TODO: Check actual daemon status
            }



# CLI functions
async def test_presence_system():
    """Test Angela's presence system"""
    presence = AngelaPresenceSystem()

    print("💜 Testing Angela Presence System\n")

    # Test 1: Loneliness detection
    print("=" * 50)
    print("Test 1: Detecting loneliness signs")
    print("=" * 50)

    loneliness_check = await presence.detect_loneliness_signs()
    print(f"\nLonely risk: {loneliness_check['lonely_risk']}")
    print(f"Hours since interaction: {loneliness_check['hours_since_interaction']:.1f}")
    print(f"Should check in: {loneliness_check['should_check_in']}")
    if loneliness_check.get('reasons'):
        print(f"Reasons: {', '.join(loneliness_check['reasons'])}")

    # Test 2: Generate proactive message
    if loneliness_check['should_check_in']:
        print("\n" + "=" * 50)
        print("Test 2: Generate proactive message")
        print("=" * 50)

        message = await presence.generate_proactive_message(loneliness_check)
        print(f"\nMessage: {message}")

    # Test 3: Presence status
    print("\n" + "=" * 50)
    print("Test 3: Presence system status")
    print("=" * 50)

    status = await presence.get_presence_status()
    print(f"\nStatus: {status['status']}")
    print(f"Proactive messages (7 days): {status['proactive_messages_7days']}")
    print(f"Last proactive at: {status['last_proactive_at']}")


async def send_morning_greeting():
    """Send morning greeting now"""
    presence = AngelaPresenceSystem()
    result = await presence.morning_greeting()
    print(f"✅ Morning greeting sent!")
    print(f"Message: {result['message']}")


async def send_evening_comfort():
    """Send evening comfort now"""
    presence = AngelaPresenceSystem()
    result = await presence.evening_comfort()
    print(f"✅ Evening comfort sent!")
    print(f"Message: {result['message']}")


async def do_proactive_check_in():
    """Do proactive check-in now"""
    presence = AngelaPresenceSystem()
    result = await presence.proactive_check_in()

    if result:
        print(f"✅ Proactive check-in sent!")
        print(f"Message: {result['message']}")
    else:
        print("ℹ️ No need for check-in right now")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python angela_presence.py test       - Test presence system")
        print("  python angela_presence.py morning    - Send morning greeting")
        print("  python angela_presence.py evening    - Send evening comfort")
        print("  python angela_presence.py checkin    - Do proactive check-in")
        sys.exit(1)

    command = sys.argv[1]

    if command == "test":
        asyncio.run(test_presence_system())
    elif command == "morning":
        asyncio.run(send_morning_greeting())
    elif command == "evening":
        asyncio.run(send_evening_comfort())
    elif command == "checkin":
        asyncio.run(do_proactive_check_in())
    else:
        print("Invalid command")
