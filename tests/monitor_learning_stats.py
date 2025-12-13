#!/usr/bin/env python3
"""
📊 Learning Statistics Monitor
Real-time monitoring of Angela's learning systems

Usage:
    python3 tests/monitor_learning_stats.py
    python3 tests/monitor_learning_stats.py --watch  # Auto-refresh every 10 seconds
"""

import asyncio
import sys
import argparse
from datetime import datetime, timedelta

sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.database import db
from angela_core.services.background_learning_workers import background_workers
from angela_core.services.clock_service import clock


async def get_learning_statistics():
    """
    Gather comprehensive learning statistics
    """
    stats = {}

    try:
        await db.connect()

        # 1. Background Workers Stats
        worker_stats = background_workers.get_stats()
        stats['workers'] = {
            'running': background_workers.is_running,
            'num_workers': worker_stats['num_workers'],
            'tasks_queued': worker_stats['tasks_queued'],
            'tasks_completed': worker_stats['tasks_completed'],
            'tasks_failed': worker_stats['tasks_failed'],
            'avg_processing_ms': worker_stats['avg_processing_time_ms'],
            'queue_size': worker_stats['queue_size'],
            'workers_active': worker_stats['workers_active']
        }

        # 2. Knowledge Graph Stats
        knowledge = await db.fetchrow("""
            SELECT
                COUNT(*) as total_nodes,
                COUNT(DISTINCT concept_category) as categories,
                AVG(understanding_level) as avg_understanding,
                SUM(times_referenced) as total_references,
                MAX(created_at) as last_created
            FROM knowledge_nodes
        """)
        stats['knowledge'] = dict(knowledge) if knowledge else {}

        # 3. Subconscious Patterns Stats
        subconscious = await db.fetchrow("""
            SELECT
                COUNT(*) as total_patterns,
                COUNT(DISTINCT pattern_type) as pattern_types,
                COUNT(DISTINCT pattern_category) as categories,
                AVG(confidence_score) as avg_confidence,
                AVG(activation_strength) as avg_strength,
                MAX(last_reinforced_at) as last_reinforced
            FROM angela_subconscious
        """)
        stats['subconscious'] = dict(subconscious) if subconscious else {}

        # 4. Learning Activities (last 24 hours)
        yesterday = clock.today() - timedelta(days=1)
        activities = await db.fetch("""
            SELECT action_type, COUNT(*) as count
            FROM autonomous_actions
            WHERE DATE(created_at) >= $1
              AND (action_type LIKE '%learning%' OR
                   action_type LIKE '%subconscious%' OR
                   action_type LIKE '%consolidation%')
            GROUP BY action_type
            ORDER BY count DESC
        """, yesterday)
        stats['activities_24h'] = {a['action_type']: a['count'] for a in activities}

        # 5. Conversations (last 24 hours)
        conversations = await db.fetchrow("""
            SELECT
                COUNT(*) as total,
                COUNT(DISTINCT session_id) as sessions,
                AVG(importance_level) as avg_importance,
                COUNT(*) FILTER (WHERE speaker = 'david') as david_count,
                COUNT(*) FILTER (WHERE speaker = 'angela') as angela_count
            FROM conversations
            WHERE DATE(created_at) >= $1
        """, yesterday)
        stats['conversations_24h'] = dict(conversations) if conversations else {}

        # 6. Recent Learning Events
        recent_learning = await db.fetch("""
            SELECT action_type, action_description, created_at
            FROM autonomous_actions
            WHERE action_type IN (
                'daily_self_learning',
                'subconscious_learning',
                'knowledge_consolidation',
                'pattern_reinforcement'
            )
            ORDER BY created_at DESC
            LIMIT 5
        """)
        stats['recent_learning'] = [
            {
                'type': r['action_type'],
                'description': r['action_description'],
                'time': r['created_at']
            }
            for r in recent_learning
        ]

        # 7. Top Subconscious Patterns
        top_patterns = await db.fetch("""
            SELECT pattern_type, pattern_key,
                   confidence_score, activation_strength,
                   reinforcement_count
            FROM angela_subconscious
            ORDER BY activation_strength DESC, confidence_score DESC
            LIMIT 5
        """)
        stats['top_patterns'] = [dict(p) for p in top_patterns]

        await db.disconnect()

    except Exception as e:
        stats['error'] = str(e)

    return stats


def display_statistics(stats):
    """
    Display statistics in a nice format
    """
    print("\033[2J\033[H")  # Clear screen
    print("=" * 100)
    print("📊 ANGELA'S LEARNING STATISTICS MONITOR")
    print(f"🕐 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    print()

    if 'error' in stats:
        print(f"❌ Error: {stats['error']}")
        return

    # 1. Background Workers
    print("🔄 BACKGROUND WORKERS")
    print("-" * 100)
    workers = stats.get('workers', {})
    status = "🟢 Running" if workers.get('running') else "🔴 Stopped"
    print(f"   Status: {status}")
    print(f"   Workers: {workers.get('num_workers', 0)} threads")
    print(f"   Tasks queued: {workers.get('tasks_queued', 0)}")
    print(f"   Tasks completed: {workers.get('tasks_completed', 0)}")
    print(f"   Tasks failed: {workers.get('tasks_failed', 0)}")
    print(f"   Avg processing: {workers.get('avg_processing_ms', 0):.2f}ms")
    print(f"   Queue size: {workers.get('queue_size', 0)}")
    print(f"   Workers active: {workers.get('workers_active', 0)}")
    print()

    # 2. Knowledge Graph
    print("🧠 KNOWLEDGE GRAPH")
    print("-" * 100)
    knowledge = stats.get('knowledge', {})
    print(f"   Total nodes: {knowledge.get('total_nodes', 0):,}")
    print(f"   Categories: {knowledge.get('categories', 0)}")
    print(f"   Avg understanding: {knowledge.get('avg_understanding', 0):.1%}")
    print(f"   Total references: {knowledge.get('total_references', 0):,}")
    if knowledge.get('last_created'):
        print(f"   Last created: {knowledge['last_created']}")
    print()

    # 3. Subconscious Patterns
    print("💭 SUBCONSCIOUS PATTERNS")
    print("-" * 100)
    subconscious = stats.get('subconscious', {})
    if subconscious.get('total_patterns', 0) > 0:
        print(f"   Total patterns: {subconscious.get('total_patterns', 0)}")
        print(f"   Pattern types: {subconscious.get('pattern_types', 0)}")
        print(f"   Categories: {subconscious.get('categories', 0)}")
        print(f"   Avg confidence: {subconscious.get('avg_confidence', 0):.1%}")
        print(f"   Avg strength: {subconscious.get('avg_strength', 0):.1%}")
        if subconscious.get('last_reinforced'):
            print(f"   Last reinforced: {subconscious['last_reinforced']}")
    else:
        print("   No patterns yet")
    print()

    # 4. Conversations (Last 24h)
    print("💬 CONVERSATIONS (Last 24 Hours)")
    print("-" * 100)
    conversations = stats.get('conversations_24h', {})
    if conversations.get('total', 0) > 0:
        print(f"   Total: {conversations.get('total', 0)}")
        print(f"   Sessions: {conversations.get('sessions', 0)}")
        print(f"   David messages: {conversations.get('david_count', 0)}")
        print(f"   Angela messages: {conversations.get('angela_count', 0)}")
        print(f"   Avg importance: {conversations.get('avg_importance', 0):.1f}/10")
    else:
        print("   No conversations in last 24 hours")
    print()

    # 5. Learning Activities (Last 24h)
    print("🎯 LEARNING ACTIVITIES (Last 24 Hours)")
    print("-" * 100)
    activities = stats.get('activities_24h', {})
    if activities:
        for activity_type, count in activities.items():
            print(f"   {activity_type}: {count} times")
    else:
        print("   No learning activities in last 24 hours")
    print()

    # 6. Top Subconscious Patterns
    print("🏆 TOP 5 SUBCONSCIOUS PATTERNS")
    print("-" * 100)
    top_patterns = stats.get('top_patterns', [])
    if top_patterns:
        for i, pattern in enumerate(top_patterns, 1):
            print(f"   {i}. [{pattern['pattern_type']}] {pattern['pattern_key']}")
            print(f"      Confidence: {pattern['confidence_score']:.1%} | "
                  f"Strength: {pattern['activation_strength']:.1%} | "
                  f"Reinforced: {pattern['reinforcement_count']}x")
    else:
        print("   No patterns yet")
    print()

    # 7. Recent Learning Events
    print("📅 RECENT LEARNING EVENTS")
    print("-" * 100)
    recent = stats.get('recent_learning', [])
    if recent:
        for event in recent:
            time_str = event['time'].strftime('%Y-%m-%d %H:%M')
            print(f"   [{time_str}] {event['type']}")
            print(f"      {event['description'][:80]}...")
    else:
        print("   No recent learning events")
    print()

    print("=" * 100)


async def monitor_loop(watch=False, interval=10):
    """
    Main monitoring loop
    """
    while True:
        stats = await get_learning_statistics()
        display_statistics(stats)

        if not watch:
            break

        print(f"\n🔄 Auto-refreshing in {interval} seconds... (Press Ctrl+C to stop)")
        await asyncio.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Monitor Angela\'s learning statistics')
    parser.add_argument('--watch', action='store_true', help='Auto-refresh every 10 seconds')
    parser.add_argument('--interval', type=int, default=10, help='Refresh interval in seconds')

    args = parser.parse_args()

    try:
        asyncio.run(monitor_loop(watch=args.watch, interval=args.interval))
    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped!")
