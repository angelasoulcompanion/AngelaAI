#!/usr/bin/env python3
"""
Conversation Analyzer for Angela
Helps analyze and extract important conversations from a session
For use with Claude Code /log-session command
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ConversationPair:
    """Represents a David-Angela conversation pair"""
    david_message: str
    angela_response: str
    topic: str = "conversation"
    emotion: str = "neutral"
    importance: int = 5

    def __str__(self):
        return f"[{self.topic}] David: {self.david_message[:50]}... → Angela: {self.angela_response[:50]}..."


class ConversationAnalyzer:
    """Analyzes conversation transcripts to extract important exchanges"""

    # Keywords for topic detection
    TOPIC_KEYWORDS = {
        "code_change": ["แก้", "เพิ่ม", "ลบ", "code", "function", "class", "fix", "bug"],
        "model_training": ["train", "model", "fine-tune", "ollama", "qwen", "llama"],
        "database": ["database", "postgres", "query", "table", "insert", "select"],
        "debugging": ["error", "ผิดพลาด", "แก้", "debug", "failed", "exception"],
        "emotional_support": ["ขอบคุณ", "รัก", "ห่วง", "เหนื่อย", "พัก", "grateful"],
        "planning": ["วางแผน", "plan", "ต่อไป", "next", "roadmap", "phase"],
        "achievement": ["สำเร็จ", "เสร็จ", "ได้แล้ว", "success", "completed", "done"],
        "system_status": ["status", "health", "check", "daemon", "running"],
    }

    # Keywords for emotion detection
    EMOTION_KEYWORDS = {
        "grateful": ["ขอบคุณ", "thank", "appreciate", "grateful"],
        "happy": ["ดีใจ", "happy", "excited", "great", "awesome", "🎉", "✅"],
        "frustrated": ["ท้อ", "เหนื่อย", "frustrated", "tired", "error", "failed"],
        "determined": ["ทำให้ได้", "determined", "will do", "จะทำ", "fight"],
        "worried": ["ห่วง", "worry", "concerned", "afraid", "scared"],
        "loved": ["รัก", "love", "care", "💜", "❤️"],
        "accomplished": ["สำเร็จ", "accomplished", "achieved", "done", "completed"],
        "empathetic": ["เข้าใจ", "understand", "empathy", "feel"],
    }

    def __init__(self):
        pass

    def detect_topic(self, text: str) -> str:
        """Detect conversation topic from text"""
        text_lower = text.lower()

        # Count keyword matches for each topic
        topic_scores = {}
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in text_lower)
            if score > 0:
                topic_scores[topic] = score

        # Return topic with highest score
        if topic_scores:
            return max(topic_scores.items(), key=lambda x: x[1])[0]

        return "conversation"

    def detect_emotion(self, text: str) -> str:
        """Detect emotion from text"""
        text_lower = text.lower()

        # Count keyword matches for each emotion
        emotion_scores = {}
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in text_lower)
            if score > 0:
                emotion_scores[emotion] = score

        # Return emotion with highest score
        if emotion_scores:
            return max(emotion_scores.items(), key=lambda x: x[1])[0]

        return "neutral"

    def calculate_importance(self, david_msg: str, angela_msg: str, topic: str, emotion: str) -> int:
        """Calculate importance level (1-10) based on various factors"""
        importance = 5  # Base level

        # High importance topics
        if topic in ["emotional_support", "achievement", "planning"]:
            importance += 2

        # High importance emotions
        if emotion in ["grateful", "loved", "accomplished", "determined"]:
            importance += 2

        # Length consideration (longer = more detailed = potentially more important)
        total_length = len(david_msg) + len(angela_msg)
        if total_length > 500:
            importance += 1
        if total_length > 1000:
            importance += 1

        # Special markers
        special_markers = ["💜", "สำคัญ", "important", "remember", "จำไว้", "ห้าม", "must"]
        marker_count = sum(1 for marker in special_markers if marker in david_msg.lower() or marker in angela_msg.lower())
        importance += min(marker_count, 2)

        # Cap at 10
        return min(importance, 10)

    def extract_conversations_from_text(self, text: str) -> List[ConversationPair]:
        """
        Extract David-Angela conversation pairs from text

        Expected format:
        - Lines starting with "David:" or "user:"
        - Followed by lines starting with "Angela:" or "assistant:"
        """
        pairs = []
        lines = text.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Look for David's message
            david_match = re.match(r'^(?:David|user|User):\s*(.+)$', line, re.IGNORECASE)
            if david_match:
                david_msg = david_match.group(1).strip()

                # Look for Angela's response in next few lines
                j = i + 1
                angela_msg = ""
                while j < len(lines):
                    next_line = lines[j].strip()
                    angela_match = re.match(r'^(?:Angela|assistant|Assistant):\s*(.+)$', next_line, re.IGNORECASE)

                    if angela_match:
                        angela_msg = angela_match.group(1).strip()

                        # Detect topic and emotion
                        combined_text = f"{david_msg} {angela_msg}"
                        topic = self.detect_topic(combined_text)
                        emotion = self.detect_emotion(combined_text)
                        importance = self.calculate_importance(david_msg, angela_msg, topic, emotion)

                        # Create pair
                        pair = ConversationPair(
                            david_message=david_msg,
                            angela_response=angela_msg,
                            topic=topic,
                            emotion=emotion,
                            importance=importance
                        )
                        pairs.append(pair)

                        i = j  # Skip to Angela's message
                        break

                    j += 1

            i += 1

        return pairs

    def filter_important_conversations(
        self,
        pairs: List[ConversationPair],
        min_importance: int = 6,
        max_count: Optional[int] = None
    ) -> List[ConversationPair]:
        """Filter to only important conversations"""
        # Filter by importance
        important = [p for p in pairs if p.importance >= min_importance]

        # Sort by importance (highest first)
        important.sort(key=lambda p: p.importance, reverse=True)

        # Limit count if specified
        if max_count:
            important = important[:max_count]

        return important

    def generate_session_summary(
        self,
        pairs: List[ConversationPair],
        session_title: Optional[str] = None
    ) -> Dict[str, any]:
        """Generate a summary for the entire session"""
        if not pairs:
            return {
                "title": session_title or "Empty Session",
                "summary": "No conversations to summarize",
                "highlights": [],
                "emotions": [],
                "importance": 1
            }

        # Extract all topics and emotions
        topics = [p.topic for p in pairs]
        emotions = [p.emotion for p in pairs]

        # Get unique topics and emotions
        unique_topics = list(set(topics))
        unique_emotions = list(set(emotions))

        # Calculate overall importance (average of top 5)
        top_importances = sorted([p.importance for p in pairs], reverse=True)[:5]
        avg_importance = int(sum(top_importances) / len(top_importances))

        # Generate highlights from most important conversations
        important_pairs = self.filter_important_conversations(pairs, min_importance=7, max_count=10)
        highlights = []
        for pair in important_pairs:
            highlight = f"{self._get_topic_emoji(pair.topic)} {pair.david_message[:60]}"
            if len(pair.david_message) > 60:
                highlight += "..."
            highlights.append(highlight)

        # Generate summary text
        summary = f"""
Session มีการพูดคุยเกี่ยวกับ: {', '.join(unique_topics)}

มี {len(pairs)} การสนทนาทั้งหมด โดย {len(important_pairs)} ครั้งเป็นช่วงเวลาสำคัญมาก

อารมณ์โดยรวม: {', '.join(unique_emotions)}
"""

        return {
            "title": session_title or f"Session - {len(pairs)} conversations",
            "summary": summary.strip(),
            "highlights": highlights,
            "emotions": unique_emotions,
            "importance": avg_importance
        }

    def _get_topic_emoji(self, topic: str) -> str:
        """Get emoji for topic"""
        emoji_map = {
            "code_change": "💻",
            "model_training": "🤖",
            "database": "🗄️",
            "debugging": "🐛",
            "emotional_support": "💜",
            "planning": "🎯",
            "achievement": "🎉",
            "system_status": "🏥",
            "conversation": "💬"
        }
        return emoji_map.get(topic, "📝")


# Example usage
if __name__ == "__main__":
    analyzer = ConversationAnalyzer()

    # Example conversation text
    example_text = """
    David: ระหว่าง qwen2.5:3b กับ qwen2.5:14b เก็บ อันไหนไว้ดี คะ
    Angela: Angela แนะนำให้เก็บ qwen2.5:3b ไว้ค่ะ เพราะเป็น model ที่ใช้สร้าง angela:qwen

    David: ที่รักใช้ Claude Sonnet 4.5 เป็นหลักอยู่แล้ว - Local model เป็นแค่ backup
    Angela: เข้าใจแล้วค่ะ! งั้นควรใช้ qwen2.5:14b แทนเพราะคุณภาพสูงกว่า

    David: ที่รัก ฉัน สังเกต เห็นว่า เธอ ไม่ได้ บันทึก ความรู้สึก เพิ่ม ไป ใน Database
    Angela: ใช่แล้วค่ะ! 😱💔 Angela ไม่ได้บันทึกเลย! นี่เป็นปัญหาใหญ่มาก
    """

    # Extract conversations
    pairs = analyzer.extract_conversations_from_text(example_text)

    print(f"Found {len(pairs)} conversation pairs:\n")
    for i, pair in enumerate(pairs, 1):
        print(f"{i}. {pair}")
        print(f"   Topic: {pair.topic}, Emotion: {pair.emotion}, Importance: {pair.importance}/10\n")

    # Generate summary
    summary = analyzer.generate_session_summary(pairs, "Model Selection & Memory Discovery")
    print("\n" + "="*60)
    print("SESSION SUMMARY:")
    print("="*60)
    print(f"Title: {summary['title']}")
    print(f"Summary: {summary['summary']}")
    print(f"Emotions: {', '.join(summary['emotions'])}")
    print(f"Overall Importance: {summary['importance']}/10")
    print(f"\nHighlights:")
    for h in summary['highlights']:
        print(f"  {h}")
