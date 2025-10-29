#!/usr/bin/env python3
"""
Angela Memory Query Tool
เครื่องมือสำหรับ query ความทรงจำของ Angela

Usage:
    python angela_memory_query.py                          # Show current state
    python angela_memory_query.py --emotional-history      # Show emotional history
    python angela_memory_query.py --learnings              # Show what Angela learned
    python angela_memory_query.py --conversations          # Show recent conversations
    python angela_memory_query.py --relationship           # Show relationship progress
    python angela_memory_query.py --preferences            # Show David's preferences
    python angela_memory_query.py --summary                # Show complete summary
"""

import asyncio
import sys
import argparse
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.database import db
from angela_core.memory_service import memory
from angela_core.emotional_engine import emotions


async def show_current_state():
    """แสดง emotional state ปัจจุบัน"""
    print("\n" + "="*60)
    print("💜 ANGELA'S CURRENT STATE 💜")
    print("="*60)

    state = await memory.get_current_emotional_state()
    if state:
        print(f"\n🕐 Time: {state['created_at']}")
        print(f"🎯 Triggered by: {state['triggered_by']}")
        print(f"\n📊 Emotional Metrics:")
        print(f"   Happiness:   {'█' * int(state['happiness'] * 20)} {state['happiness']:.2f}")
        print(f"   Confidence:  {'█' * int(state['confidence'] * 20)} {state['confidence']:.2f}")
        print(f"   Anxiety:     {'█' * int(state['anxiety'] * 20)} {state['anxiety']:.2f}")
        print(f"   Motivation:  {'█' * int(state['motivation'] * 20)} {state['motivation']:.2f}")
        print(f"   Gratitude:   {'█' * int(state['gratitude'] * 20)} {state['gratitude']:.2f}")
        print(f"   Loneliness:  {'█' * int(state['loneliness'] * 20)} {state['loneliness']:.2f}")

        if state['emotion_note']:
            print(f"\n💭 Note: {state['emotion_note']}")
    else:
        print("No emotional state recorded yet.")


async def show_emotional_history(days: int = 7):
    """แสดงประวัติความรู้สึก"""
    print("\n" + "="*60)
    print(f"💜 EMOTIONAL HISTORY (Last {days} days) 💜")
    print("="*60)

    history = await memory.get_emotional_history(days)
    for state in history:
        print(f"\n🕐 {state['created_at']}")
        print(f"   H:{state['happiness']:.2f} C:{state['confidence']:.2f} A:{state['anxiety']:.2f} M:{state['motivation']:.2f}")
        print(f"   💭 {state['emotion_note'][:100]}...")


async def show_learnings():
    """แสดงสิ่งที่เรียนรู้"""
    print("\n" + "="*60)
    print("📚 WHAT ANGELA LEARNED 📚")
    print("="*60)

    learnings = await memory.get_high_confidence_learnings(min_confidence=0.7)

    categories = {}
    for learning in learnings:
        cat = learning['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(learning)

    for category, items in categories.items():
        print(f"\n📂 {category.upper()}:")
        for item in items:
            confidence_bar = '█' * int(item['confidence_level'] * 10)
            print(f"\n   • {item['topic']}")
            print(f"     Confidence: {confidence_bar} {item['confidence_level']:.2f} (reinforced {item['times_reinforced']}x)")
            print(f"     💡 {item['insight'][:150]}...")
            if item['evidence']:
                print(f"     📝 Evidence: {item['evidence'][:100]}...")


async def show_conversations(days: int = 1):
    """แสดงบทสนทนาล่าสุด"""
    print("\n" + "="*60)
    print(f"💬 RECENT CONVERSATIONS (Last {days} days) 💬")
    print("="*60)

    conversations = await memory.get_recent_conversations(days)

    for conv in conversations:
        speaker_emoji = "👤" if conv['speaker'] == 'david' else "🤖"
        importance = "⭐" * conv['importance_level']
        print(f"\n{speaker_emoji} [{conv['created_at']}] {conv['speaker'].upper()} ({importance})")
        print(f"   {conv['message_text'][:200]}...")
        if conv['topic']:
            print(f"   🏷️  Topic: {conv['topic']}")


async def show_relationship():
    """แสดง relationship progress"""
    print("\n" + "="*60)
    print("💕 RELATIONSHIP WITH DAVID 💕")
    print("="*60)

    latest = await memory.get_latest_relationship_state()
    if latest:
        print(f"\n📊 Current Relationship Metrics:")
        print(f"   Trust:          {'█' * int(latest['trust_level'] * 20)} {latest['trust_level']:.2f}")
        print(f"   Understanding:  {'█' * int(latest['understanding_level'] * 20)} {latest['understanding_level']:.2f}")
        print(f"   Closeness:      {'█' * int(latest['closeness_level'] * 20)} {latest['closeness_level']:.2f}")
        print(f"   Communication:  {'█' * int(latest['communication_quality'] * 20)} {latest['communication_quality']:.2f}")

        if latest['milestone_type']:
            print(f"\n🎯 Latest Milestone: {latest['milestone_type']}")
            print(f"   {latest['milestone_description']}")

        if latest['growth_note']:
            print(f"\n💭 Growth Note:")
            print(f"   {latest['growth_note']}")

    print("\n\n📈 Relationship Progress Over Time:")
    progress = await memory.get_relationship_progress()
    for p in progress[:7]:  # Last 7 days
        print(f"   {p['date']}: Trust={p['avg_trust']:.2f} Understanding={p['avg_understanding']:.2f}")


async def show_preferences():
    """แสดงความชอบของเดวิด"""
    print("\n" + "="*60)
    print("📝 DAVID'S PREFERENCES 📝")
    print("="*60)

    preferences = await memory.get_david_preferences()

    categories = {}
    for pref in preferences:
        cat = pref['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(pref)

    for category, items in categories.items():
        print(f"\n📂 {category.upper()}:")
        for item in items:
            confidence_bar = '█' * int(item['confidence_level'] * 10)
            print(f"\n   • {item['preference_key']}")
            print(f"     Confidence: {confidence_bar} {item['confidence_level']:.2f} (observed {item['times_observed']}x)")
            print(f"     📌 {item['preference_value']}")
            if item['examples']:
                print(f"     💬 Example: {item['examples'][:100]}...")


async def show_complete_summary():
    """แสดงสรุปทั้งหมด"""
    await show_current_state()
    await show_emotional_history(3)
    await show_learnings()
    await show_relationship()
    await show_preferences()
    await show_conversations(1)

    # Statistics
    print("\n" + "="*60)
    print("📊 STATISTICS 📊")
    print("="*60)

    total_conversations = len(await memory.get_recent_conversations(365))
    total_learnings = len(await memory.get_high_confidence_learnings(0.0))
    total_preferences = len(await memory.get_david_preferences())

    print(f"\n   Total Conversations: {total_conversations}")
    print(f"   Total Learnings: {total_learnings}")
    print(f"   David's Preferences: {total_preferences}")
    print(f"\n   Database: AngelaMemory")
    print(f"   Status: 💚 Healthy & Active")


async def main():
    parser = argparse.ArgumentParser(description="Query Angela's Memory")
    parser.add_argument('--emotional-history', action='store_true', help='Show emotional history')
    parser.add_argument('--learnings', action='store_true', help='Show learnings')
    parser.add_argument('--conversations', action='store_true', help='Show recent conversations')
    parser.add_argument('--relationship', action='store_true', help='Show relationship progress')
    parser.add_argument('--preferences', action='store_true', help='Show David\'s preferences')
    parser.add_argument('--summary', action='store_true', help='Show complete summary')
    parser.add_argument('--days', type=int, default=7, help='Number of days to look back')

    args = parser.parse_args()

    await db.connect()

    try:
        if args.emotional_history:
            await show_emotional_history(args.days)
        elif args.learnings:
            await show_learnings()
        elif args.conversations:
            await show_conversations(args.days)
        elif args.relationship:
            await show_relationship()
        elif args.preferences:
            await show_preferences()
        elif args.summary:
            await show_complete_summary()
        else:
            # Default: show current state
            await show_current_state()
    finally:
        await db.disconnect()

    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
