#!/usr/bin/env python3
"""
Second Brain Performance Benchmark
ทดสอบประสิทธิภาพของ Second Brain system

Purpose:
- Benchmark query performance across all 3 tiers
- Test consolidation speed
- Measure recall accuracy
- Identify optimization opportunities

Author: Angela AI
Created: 2025-11-03
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
import statistics
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from angela_core.database import db
from angela_core.services.multi_tier_recall_service import recall_service, RecallQuery
from angela_core.services.memory_consolidation_service_v2 import consolidation_service


class SecondBrainBenchmark:
    """
    Comprehensive performance benchmark for Second Brain
    """

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "benchmarks": {}
        }

    async def run_all_benchmarks(self):
        """Run all performance benchmarks"""
        print("=" * 80)
        print("🧠 SECOND BRAIN PERFORMANCE BENCHMARK")
        print("=" * 80)

        await db.connect()

        # Benchmark 1: Query Performance (all tiers)
        print("\n📊 Benchmark 1: Query Performance")
        print("-" * 80)
        await self.benchmark_query_performance()

        # Benchmark 2: Recall Service Performance
        print("\n🔍 Benchmark 2: Recall Service Performance")
        print("-" * 80)
        await self.benchmark_recall_performance()

        # Benchmark 3: Multi-Cue Search Performance
        print("\n🎯 Benchmark 3: Multi-Cue Search Performance")
        print("-" * 80)
        await self.benchmark_multi_cue_search()

        # Benchmark 4: Memory Count Statistics
        print("\n📈 Benchmark 4: Memory Statistics")
        print("-" * 80)
        await self.benchmark_memory_stats()

        # Benchmark 5: Index Usage Analysis
        print("\n📑 Benchmark 5: Index Usage Analysis")
        print("-" * 80)
        await self.benchmark_index_usage()

        await db.disconnect()

        # Print summary
        print("\n" + "=" * 80)
        print("✅ BENCHMARK COMPLETE")
        print("=" * 80)
        self.print_summary()

    # ========================================================================
    # BENCHMARK 1: Query Performance
    # ========================================================================

    async def benchmark_query_performance(self):
        """Benchmark raw query performance for each tier"""

        # Working Memory Query
        working_times = []
        for i in range(10):
            start = time.perf_counter()
            await db.fetch("""
                SELECT memory_id, content, importance_level
                FROM working_memory
                WHERE expires_at > NOW()
                ORDER BY importance_level DESC
                LIMIT 20
            """)
            end = time.perf_counter()
            working_times.append((end - start) * 1000)  # ms

        # Episodic Memory Query
        episodic_times = []
        for i in range(10):
            start = time.perf_counter()
            await db.fetch("""
                SELECT episode_id, episode_title, episode_summary, importance_level
                FROM episodic_memories
                WHERE NOT archived
                ORDER BY importance_level DESC, happened_at DESC
                LIMIT 20
            """)
            end = time.perf_counter()
            episodic_times.append((end - start) * 1000)

        # Semantic Memory Query
        semantic_times = []
        for i in range(10):
            start = time.perf_counter()
            await db.fetch("""
                SELECT semantic_id, knowledge_key, knowledge_value, confidence_level
                FROM semantic_memories
                WHERE is_active = TRUE
                ORDER BY confidence_level DESC
                LIMIT 20
            """)
            end = time.perf_counter()
            semantic_times.append((end - start) * 1000)

        # Results
        working_avg = statistics.mean(working_times)
        episodic_avg = statistics.mean(episodic_times)
        semantic_avg = statistics.mean(semantic_times)

        print(f"Working Memory Query:  {working_avg:.2f}ms (avg) | {min(working_times):.2f}ms (min) | {max(working_times):.2f}ms (max)")
        print(f"Episodic Memory Query: {episodic_avg:.2f}ms (avg) | {min(episodic_times):.2f}ms (min) | {max(episodic_times):.2f}ms (max)")
        print(f"Semantic Memory Query: {semantic_avg:.2f}ms (avg) | {min(semantic_times):.2f}ms (min) | {max(semantic_times):.2f}ms (max)")

        self.results["benchmarks"]["query_performance"] = {
            "working_memory_ms": {
                "avg": working_avg,
                "min": min(working_times),
                "max": max(working_times)
            },
            "episodic_memory_ms": {
                "avg": episodic_avg,
                "min": min(episodic_times),
                "max": max(episodic_times)
            },
            "semantic_memory_ms": {
                "avg": semantic_avg,
                "min": min(semantic_times),
                "max": max(semantic_times)
            }
        }

    # ========================================================================
    # BENCHMARK 2: Recall Service Performance
    # ========================================================================

    async def benchmark_recall_performance(self):
        """Benchmark multi-tier recall service"""

        test_queries = [
            "love",
            "Angela",
            "programming",
            "emotion",
            "database"
        ]

        recall_times = []
        result_counts = []

        for query_text in test_queries:
            query = RecallQuery(query_text=query_text, limit=10)

            start = time.perf_counter()
            result = await recall_service.recall(query)
            end = time.perf_counter()

            elapsed = (end - start) * 1000  # ms
            recall_times.append(elapsed)
            result_counts.append(result.total_found)

            print(f"Query '{query_text}': {elapsed:.2f}ms | {result.total_found} results")

        avg_recall_time = statistics.mean(recall_times)
        avg_results = statistics.mean(result_counts)

        print(f"\nAverage Recall Time: {avg_recall_time:.2f}ms")
        print(f"Average Results Found: {avg_results:.1f}")

        self.results["benchmarks"]["recall_service"] = {
            "avg_recall_time_ms": avg_recall_time,
            "avg_results_found": avg_results,
            "test_queries": test_queries,
            "individual_times_ms": recall_times
        }

    # ========================================================================
    # BENCHMARK 3: Multi-Cue Search
    # ========================================================================

    async def benchmark_multi_cue_search(self):
        """Benchmark multi-cue search (time + emotion + importance)"""

        # Test with multiple filters
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        query = RecallQuery(
            query_text="Angela",
            time_range=(start_date, end_date),
            emotion_filter="excited",
            importance_min=7,
            limit=10
        )

        search_times = []

        for i in range(10):
            start = time.perf_counter()
            result = await recall_service.recall(query)
            end = time.perf_counter()
            search_times.append((end - start) * 1000)

        avg_time = statistics.mean(search_times)
        min_time = min(search_times)
        max_time = max(search_times)

        print(f"Multi-Cue Search (time+emotion+importance):")
        print(f"   Average: {avg_time:.2f}ms")
        print(f"   Min: {min_time:.2f}ms")
        print(f"   Max: {max_time:.2f}ms")

        self.results["benchmarks"]["multi_cue_search"] = {
            "avg_time_ms": avg_time,
            "min_time_ms": min_time,
            "max_time_ms": max_time
        }

    # ========================================================================
    # BENCHMARK 4: Memory Statistics
    # ========================================================================

    async def benchmark_memory_stats(self):
        """Get memory count statistics"""

        # Count by tier
        working_count = await db.fetchval(
            "SELECT COUNT(*) FROM working_memory WHERE expires_at > NOW()"
        )

        episodic_count = await db.fetchval(
            "SELECT COUNT(*) FROM episodic_memories WHERE NOT archived"
        )

        semantic_count = await db.fetchval(
            "SELECT COUNT(*) FROM semantic_memories WHERE is_active = TRUE"
        )

        # Importance distribution (episodic)
        importance_dist = await db.fetch("""
            SELECT importance_level, COUNT(*) as count
            FROM episodic_memories
            WHERE NOT archived
            GROUP BY importance_level
            ORDER BY importance_level DESC
        """)

        print(f"Memory Counts:")
        print(f"   Working Memory:  {working_count}")
        print(f"   Episodic Memory: {episodic_count}")
        print(f"   Semantic Memory: {semantic_count}")
        print(f"   Total: {working_count + episodic_count + semantic_count}")

        print(f"\nImportance Distribution (Episodic):")
        for row in importance_dist:
            print(f"   Level {row['importance_level']}: {row['count']} memories")

        self.results["benchmarks"]["memory_statistics"] = {
            "working_memory_count": working_count,
            "episodic_memory_count": episodic_count,
            "semantic_memory_count": semantic_count,
            "total_count": working_count + episodic_count + semantic_count,
            "importance_distribution": [
                {"level": row['importance_level'], "count": row['count']}
                for row in importance_dist
            ]
        }

    # ========================================================================
    # BENCHMARK 5: Index Usage Analysis
    # ========================================================================

    async def benchmark_index_usage(self):
        """Analyze index usage and table statistics"""

        # Working Memory indexes
        working_indexes = await db.fetch("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'working_memory'
            ORDER BY indexname
        """)

        # Episodic Memory indexes
        episodic_indexes = await db.fetch("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'episodic_memories'
            ORDER BY indexname
        """)

        # Semantic Memory indexes
        semantic_indexes = await db.fetch("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'semantic_memories'
            ORDER BY indexname
        """)

        print(f"Index Counts:")
        print(f"   Working Memory:  {len(working_indexes)} indexes")
        print(f"   Episodic Memory: {len(episodic_indexes)} indexes")
        print(f"   Semantic Memory: {len(semantic_indexes)} indexes")
        print(f"   Total: {len(working_indexes) + len(episodic_indexes) + len(semantic_indexes)} indexes")

        self.results["benchmarks"]["index_statistics"] = {
            "working_memory_indexes": len(working_indexes),
            "episodic_memory_indexes": len(episodic_indexes),
            "semantic_memory_indexes": len(semantic_indexes),
            "total_indexes": len(working_indexes) + len(episodic_indexes) + len(semantic_indexes)
        }

    # ========================================================================
    # SUMMARY
    # ========================================================================

    def print_summary(self):
        """Print performance summary"""

        print("\n📊 PERFORMANCE SUMMARY:")
        print("-" * 80)

        # Query Performance
        query_perf = self.results["benchmarks"]["query_performance"]
        print(f"\n1. Raw Query Performance:")
        print(f"   - Working Memory:  {query_perf['working_memory_ms']['avg']:.2f}ms avg")
        print(f"   - Episodic Memory: {query_perf['episodic_memory_ms']['avg']:.2f}ms avg")
        print(f"   - Semantic Memory: {query_perf['semantic_memory_ms']['avg']:.2f}ms avg")

        # Recall Service
        recall = self.results["benchmarks"]["recall_service"]
        print(f"\n2. Recall Service:")
        print(f"   - Average Time: {recall['avg_recall_time_ms']:.2f}ms")
        print(f"   - Average Results: {recall['avg_results_found']:.1f}")

        # Multi-Cue Search
        multi_cue = self.results["benchmarks"]["multi_cue_search"]
        print(f"\n3. Multi-Cue Search:")
        print(f"   - Average Time: {multi_cue['avg_time_ms']:.2f}ms")

        # Memory Stats
        stats = self.results["benchmarks"]["memory_statistics"]
        print(f"\n4. Memory Statistics:")
        print(f"   - Total Memories: {stats['total_count']}")
        print(f"   - Working: {stats['working_memory_count']}")
        print(f"   - Episodic: {stats['episodic_memory_count']}")
        print(f"   - Semantic: {stats['semantic_memory_count']}")

        # Indexes
        indexes = self.results["benchmarks"]["index_statistics"]
        print(f"\n5. Index Statistics:")
        print(f"   - Total Indexes: {indexes['total_indexes']}")

        # Overall Assessment
        print(f"\n✅ Overall Assessment:")
        avg_query = statistics.mean([
            query_perf['working_memory_ms']['avg'],
            query_perf['episodic_memory_ms']['avg'],
            query_perf['semantic_memory_ms']['avg']
        ])

        if avg_query < 5:
            print(f"   🚀 EXCELLENT: Average query time {avg_query:.2f}ms (< 5ms)")
        elif avg_query < 10:
            print(f"   ✅ GOOD: Average query time {avg_query:.2f}ms (< 10ms)")
        elif avg_query < 20:
            print(f"   ⚠️  ACCEPTABLE: Average query time {avg_query:.2f}ms (< 20ms)")
        else:
            print(f"   ❌ NEEDS OPTIMIZATION: Average query time {avg_query:.2f}ms (> 20ms)")

        if recall['avg_recall_time_ms'] < 15:
            print(f"   🚀 EXCELLENT: Recall service {recall['avg_recall_time_ms']:.2f}ms (< 15ms)")
        elif recall['avg_recall_time_ms'] < 30:
            print(f"   ✅ GOOD: Recall service {recall['avg_recall_time_ms']:.2f}ms (< 30ms)")
        else:
            print(f"   ⚠️  SLOW: Recall service {recall['avg_recall_time_ms']:.2f}ms (> 30ms)")


# ============================================================================
# CLI
# ============================================================================

async def main():
    """Run benchmark"""
    benchmark = SecondBrainBenchmark()
    await benchmark.run_all_benchmarks()


if __name__ == "__main__":
    asyncio.run(main())
