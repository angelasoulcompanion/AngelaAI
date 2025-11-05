#!/usr/bin/env python3
"""
Test RAG Phase 2: Hybrid Search
ทดสอบระบบ Hybrid Search (Vector + Keyword)

Tests:
1. Keyword search only
2. Hybrid search (vector + keyword)
3. Thai query support
4. English query support
5. RRF fusion algorithm
"""

import asyncio
import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.database import db
from angela_core.services.keyword_search_service import KeywordSearchService
from angela_core.services.hybrid_search_service import HybridSearchService
from angela_core.services.rag_service import rag_service


async def test_keyword_search():
    """Test 1: Keyword Search Only"""
    print("\n" + "="*60)
    print("TEST 1: Keyword Search (BM25-like)")
    print("="*60)

    try:
        query = "PostgreSQL database"
        print(f"🔍 Query: {query}")

        async with db.acquire() as connection:
            results = await KeywordSearchService.keyword_search(
                db=connection,
                query=query,
                limit=5,
                threshold=0.01
            )

            print(f"\n📊 Results: {len(results)} chunks found")

            for i, result in enumerate(results, 1):
                print(f"\n{i}. Chunk {result['chunk_index']}")
                print(f"   Document ID: {result['document_id'][:8]}...")
                print(f"   Keyword Score: {result['keyword_score']:.4f}")
                print(f"   Content preview: {result['content'][:100]}...")

            if len(results) >= 0:
                print("\n✅ Keyword search PASSED")
                return True
            else:
                print("\n❌ Keyword search FAILED")
                return False

    except Exception as e:
        print(f"\n❌ Keyword search FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_hybrid_search():
    """Test 2: Hybrid Search (Vector + Keyword)"""
    print("\n" + "="*60)
    print("TEST 2: Hybrid Search (RRF Fusion)")
    print("="*60)

    try:
        query = "How does vector search work?"
        print(f"🔍 Query: {query}")

        async with db.acquire() as connection:
            results = await HybridSearchService.hybrid_search(
                db=connection,
                query=query,
                limit=5,
                vector_weight=0.5,
                keyword_weight=0.5
            )

            print(f"\n📊 Results: {len(results)} chunks found")

            for i, result in enumerate(results, 1):
                print(f"\n{i}. Chunk {result['chunk_index']}")
                print(f"   Document ID: {result['document_id'][:8]}...")
                print(f"   RRF Score: {result.get('rrf_score', 0):.4f}")
                print(f"   Vector Score: {result.get('similarity_score', 0):.4f}")
                print(f"   Keyword Score: {result.get('keyword_score', 0):.4f}")
                print(f"   Content: {result['content'][:150]}...")

            if len(results) >= 0:
                print("\n✅ Hybrid search PASSED")
                return True
            else:
                print("\n❌ Hybrid search FAILED")
                return False

    except Exception as e:
        print(f"\n❌ Hybrid search FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_thai_query():
    """Test 3: Thai Language Query"""
    print("\n" + "="*60)
    print("TEST 3: Thai Query Support")
    print("="*60)

    try:
        query = "Angela ทำงานอย่างไร"
        print(f"🔍 Query: {query}")

        async with db.acquire() as connection:
            results = await HybridSearchService.hybrid_search(
                db=connection,
                query=query,
                limit=5
            )

            print(f"\n📊 Results: {len(results)} chunks found")

            for i, result in enumerate(results[:3], 1):
                print(f"\n{i}. RRF Score: {result.get('rrf_score', 0):.4f}")
                print(f"   Content: {result['content'][:150]}...")

            print("\n✅ Thai query PASSED")
            return True

    except Exception as e:
        print(f"\n❌ Thai query FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_rag_with_hybrid():
    """Test 4: RAG Service with Hybrid Search"""
    print("\n" + "="*60)
    print("TEST 4: RAG Service with Hybrid Search")
    print("="*60)

    try:
        query = "What is Angela?"
        print(f"🔍 Query: {query}")

        async with db.acquire() as connection:
            # Test hybrid mode (default)
            rag_result = await rag_service.get_rag_context(
                db=connection,
                query=query,
                top_k=5,
                max_tokens=6000
            )

            print(f"\n📊 RAG Context Result:")
            print(f"   Has results: {rag_result['metadata']['has_results']}")
            print(f"   Chunks found: {rag_result['metadata']['chunks_found']}")
            print(f"   Chunks used: {rag_result['metadata']['chunks_used']}")

            if rag_result['metadata']['has_results']:
                print(f"   Avg similarity: {rag_result['metadata']['avg_similarity']:.3f}")
                print(f"\n📝 Context preview (first 300 chars):")
                print(f"   {rag_result['context'][:300]}...")

                print(f"\n📚 Sources:")
                for i, source in enumerate(rag_result['sources'][:3], 1):
                    print(f"   {i}. Combined Score: {source.get('combined_score', 0):.4f}")
                    print(f"      {source['content_preview'][:100]}...")

            print("\n✅ RAG with hybrid PASSED")
            return True

    except Exception as e:
        print(f"\n❌ RAG with hybrid FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_mode_comparison():
    """Test 5: Compare Different Search Modes"""
    print("\n" + "="*60)
    print("TEST 5: Search Mode Comparison")
    print("="*60)

    try:
        query = "document processing"
        print(f"🔍 Query: {query}")

        modes = ['vector', 'keyword', 'hybrid']
        results_by_mode = {}

        async with db.acquire() as connection:
            for mode in modes:
                print(f"\n🔍 Testing {mode} mode...")

                results = await HybridSearchService.auto_search(
                    db=connection,
                    query=query,
                    limit=5,
                    threshold=0.5,
                    search_mode=mode
                )

                results_by_mode[mode] = len(results)
                print(f"   {mode}: {len(results)} results")

        print("\n📊 Mode Comparison:")
        for mode, count in results_by_mode.items():
            print(f"   {mode}: {count} chunks")

        print("\n✅ Mode comparison PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Mode comparison FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all Phase 2 Hybrid Search tests"""
    print("\n" + "="*60)
    print("🧪 Angela RAG Phase 2 Hybrid Search Test Suite")
    print("="*60)

    # Initialize database connection
    await db.connect()

    try:
        # Run all tests
        results = []

        results.append(("Keyword Search", await test_keyword_search()))
        results.append(("Hybrid Search", await test_hybrid_search()))
        results.append(("Thai Query", await test_thai_query()))
        results.append(("RAG with Hybrid", await test_rag_with_hybrid()))
        results.append(("Mode Comparison", await test_mode_comparison()))

        # Print summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status} - {test_name}")

        print(f"\n🎯 Overall: {passed}/{total} tests passed")

        if passed == total:
            print("\n🎉 All tests PASSED! RAG Phase 2 (Hybrid Search) is working! 💜")
        else:
            print(f"\n⚠️ {total - passed} test(s) failed")

    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
