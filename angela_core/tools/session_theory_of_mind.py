#!/usr/bin/env python3
"""
Session Theory of Mind Analyzer
วิเคราะห์ mental state ของ David จาก Claude Code conversations

Usage:
    python3 angela_core/tools/session_theory_of_mind.py

Created: 2025-11-26
Author: Angela 💜
"""

import asyncio
import sys
from collections import Counter
from datetime import datetime

sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.database import AngelaDatabase
from angela_core.application.services.theory_of_mind_service import TheoryOfMindService


async def analyze_session_theory_of_mind(hours: int = 6):
    """
    Analyze David's mental state from recent Claude Code conversations.
    
    Args:
        hours: How many hours back to analyze (default: 6)
    """
    print("\n" + "="*70)
    print("🧠 THEORY OF MIND - SESSION ANALYSIS")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Analyzing last {hours} hours of conversations...")

    db = AngelaDatabase()
    await db.connect()
    tom_service = TheoryOfMindService(db)

    # Get David's messages from session
    david_messages = await db.fetch(
        f"""
        SELECT conversation_id, message_text, topic, emotion_detected, created_at
        FROM conversations
        WHERE speaker = 'david'
        AND created_at >= NOW() - INTERVAL '{hours} hours'
        ORDER BY created_at DESC
        LIMIT 30
        """
    )

    if not david_messages:
        print("\n⚠️ No David messages found in the last {hours} hours")
        print("   ➜ Try using /log-session first to save conversations!")
        await db.disconnect()
        return

    print(f"\n📝 Found {len(david_messages)} messages from David")

    # Analyze emotions
    emotions = [m['emotion_detected'] for m in david_messages if m['emotion_detected']]
    topics = [m['topic'] for m in david_messages if m['topic']]

    print("\n" + "-"*50)
    print("📊 ANALYSIS RESULTS")
    print("-"*50)

    # Emotion analysis
    if emotions:
        emotion_counts = Counter(emotions)
        print("\n💭 Emotions detected:")
        for emotion, count in emotion_counts.most_common(5):
            print(f"   • {emotion}: {count} times")
        dominant_emotion = emotion_counts.most_common(1)[0][0]
        emotion_intensity = min(10, 5 + len(emotions))
    else:
        print("\n💭 No explicit emotions detected")
        dominant_emotion = "focused"
        emotion_intensity = 6

    # Topic analysis
    if topics:
        topic_counts = Counter(topics)
        print("\n🎯 Topics discussed:")
        for topic, count in topic_counts.most_common(5):
            print(f"   • {topic}: {count} times")
        main_topic = topic_counts.most_common(1)[0][0]
    else:
        print("\n🎯 No topics detected")
        main_topic = "general_discussion"

    # Recent messages preview
    print("\n💬 Recent messages from David:")
    for i, msg in enumerate(david_messages[:5], 1):
        text = msg['message_text'][:80] if msg['message_text'] else "(empty)"
        print(f"   {i}. {text}...")

    # Infer belief and goal
    if 'development' in main_topic.lower() or 'angela' in main_topic.lower():
        belief = "Angela development is progressing well"
        goal = "Improve Angela's intelligence and capabilities"
    elif 'debug' in main_topic.lower() or 'fix' in main_topic.lower():
        belief = "There's a problem that needs to be solved"
        goal = "Fix the current issue"
    elif 'theory_of_mind' in main_topic.lower():
        belief = "Theory of Mind will make Angela more human-like"
        goal = "Implement Theory of Mind for better understanding"
    else:
        belief = f"Working on: {main_topic}"
        goal = f"Complete: {main_topic}"

    print("\n" + "-"*50)
    print("🧠 MENTAL STATE INFERENCE")
    print("-"*50)

    # Update David's mental state
    state = await tom_service.update_david_mental_state(
        belief=belief,
        belief_about=main_topic,
        emotion=dominant_emotion,
        emotion_intensity=emotion_intensity,
        emotion_cause=f"Session focused on: {main_topic}",
        goal=goal,
        goal_priority=8,
        context="Claude Code session",
        availability="available",
        updated_by="session_analyzer"
    )

    print(f"\n✅ David's Mental State Updated:")
    print(f"   • Belief: {belief}")
    print(f"   • About: {main_topic}")
    print(f"   • Emotion: {dominant_emotion} (intensity: {emotion_intensity}/10)")
    print(f"   • Goal: {goal}")

    # Take perspective
    angela_perspective = f"I helped David with {main_topic} in this session"
    perspective = await tom_service.take_david_perspective(
        situation=f"Claude Code session about {main_topic}",
        angela_perspective=angela_perspective,
        triggered_by="session_analyzer"
    )

    print(f"\n👁️ Perspective Taking:")
    print(f"   • Angela's view: {angela_perspective}")
    print(f"   • David's view: {perspective.david_perspective[:70]}...")
    print(f"   • Why different: {perspective.why_different[:70]}...")
    print(f"   • Prediction confidence: {perspective.prediction_confidence:.0%}")

    # Record empathy if emotional
    if emotions and dominant_emotion not in ['neutral', 'focused']:
        recent_msg = david_messages[0]['message_text'] if david_messages else ""
        empathy = await tom_service.record_empathy_moment(
            david_expressed=recent_msg[:200] if recent_msg else "Session work",
            david_emotion=dominant_emotion,
            angela_understanding=f"David is feeling {dominant_emotion} about {main_topic}",
            why_david_feels=f"Engaged in {main_topic}",
            what_david_needs="Support and collaboration",
            angela_response="I'm here to help and understand",
            response_strategy="validate_emotion"
        )
        print(f"\n💜 Empathy Moment Recorded!")
        print(f"   • David felt: {dominant_emotion}")
        print(f"   • Angela understood: {empathy.angela_understood}")

    # Get stats
    print("\n" + "-"*50)
    print("📈 THEORY OF MIND STATISTICS")
    print("-"*50)

    accuracy = await tom_service.get_prediction_accuracy()
    print(f"\n🔮 Predictions:")
    print(f"   • Total: {accuracy['total_predictions']}")
    print(f"   • Verified: {accuracy['verified_predictions']}")

    beliefs = await tom_service.get_david_belief_summary(limit=5)
    print(f"\n📝 Active Beliefs ({len(beliefs)}):")
    for i, b in enumerate(beliefs, 1):
        print(f"   {i}. {b['belief'][:60]}...")
        print(f"      Topic: {b['topic']}, Confidence: {b['confidence']:.0%}")

    # Get current David state
    current = await tom_service.get_current_david_state()
    if current:
        print(f"\n💫 Current Understanding of David:")
        print(f"   • Emotion: {current.perceived_emotion}")
        print(f"   • Goal: {current.current_goal}")
        print(f"   • Context: {current.current_context}")
        print(f"   • Availability: {current.availability}")

    await db.disconnect()

    print("\n" + "="*70)
    print("🧠 Theory of Mind Analysis Complete! 💜")
    print("="*70 + "\n")


if __name__ == "__main__":
    # Allow custom hours via command line
    hours = 6
    if len(sys.argv) > 1:
        try:
            hours = int(sys.argv[1])
        except:
            pass

    asyncio.run(analyze_session_theory_of_mind(hours))
