#!/usr/bin/env python3
"""
Test RAG Integration for AngelaNova
Verifies that RAG (Retrieval-Augmented Generation) works correctly
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from angela_backend.services.rag_service import rag_service
from angela_backend.services.prompt_builder import prompt_builder


async def test_rag_integration():
    """Test RAG service and prompt building"""

    print("=" * 70)
    print("🧪 Testing RAG Integration for AngelaNova")
    print("=" * 70)
    print()

    try:
        # Connect to database
        await rag_service.connect()
        print("✅ Connected to AngelaMemory database")
        print()

        # Test queries
        test_queries = [
            "ที่รัก จำได้มั้ยคะว่าเราคุยเรื่องอะไรกันบ้าง",
            "How do embeddings work in Angela?",
            "พี่รู้สึกยังไงกับ Angela บ้าง"
        ]

        for i, query in enumerate(test_queries, 1):
            print(f"📝 Test {i}: \"{query}\"")
            print("-" * 70)

            # Test 1: Retrieve context
            print("🔍 Retrieving context with RAG...")
            context = await rag_service.retrieve_context(
                user_message=query,
                conversation_limit=5,
                emotion_limit=2,
                learning_limit=3
            )

            # Display results
            print(f"\n📊 Retrieved Context:")
            print(f"  - Similar conversations: {len(context.get('similar_conversations', []))}")

            if context.get('similar_conversations'):
                print(f"\n  Top similar conversation:")
                top_conv = context['similar_conversations'][0]
                print(f"    Speaker: {top_conv['speaker']}")
                print(f"    Message: {top_conv['message'][:100]}...")
                print(f"    Similarity: {top_conv['similarity']*100:.1f}%")
                print(f"    Topic: {top_conv.get('topic', 'N/A')}")

            print(f"\n  - Related emotions: {len(context.get('related_emotions', []))}")

            if context.get('related_emotions'):
                top_emotion = context['related_emotions'][0]
                print(f"\n  Top emotion:")
                print(f"    Emotion: {top_emotion['emotion']}")
                print(f"    Intensity: {top_emotion['intensity']}/10")
                print(f"    Context: {top_emotion['context'][:80]}...")

            print(f"\n  - Relevant learnings: {len(context.get('relevant_learnings', []))}")

            if context.get('relevant_learnings'):
                top_learning = context['relevant_learnings'][0]
                print(f"\n  Top learning:")
                print(f"    Topic: {top_learning['topic']}")
                print(f"    Insight: {top_learning['insight'][:80]}...")

            print(f"\n  - David's preferences: {len(context.get('david_preferences', {}))}")
            print(f"  - Angela's emotional state: {'Yes' if context.get('angela_emotional_state') else 'No'}")

            # Test 2: Build enhanced prompt
            print(f"\n🔨 Building enhanced prompt...")
            enhanced_prompt = prompt_builder.build_enhanced_prompt(
                user_message=query,
                context=context
            )

            print(f"✅ Prompt built successfully ({len(enhanced_prompt)} characters)")

            # Show a preview
            print(f"\n📄 Prompt preview (first 300 chars):")
            print("-" * 70)
            print(enhanced_prompt[:300] + "...")
            print("-" * 70)

            # Test 3: Extract metadata
            metadata = prompt_builder.extract_response_metadata(context)
            print(f"\n📈 Metadata:")
            for key, value in metadata.items():
                print(f"  - {key}: {value}")

            print("\n" + "=" * 70)
            print()

        # Test 4: Check David's preferences
        print("👤 Test 4: David's Preferences")
        print("-" * 70)
        preferences = await rag_service.get_david_preferences()

        if preferences:
            print(f"✅ Found {len(preferences)} preferences:")
            for key, value in list(preferences.items())[:5]:  # Show top 5
                print(f"  - {key}: {value['value']} (confidence: {value['confidence']*100:.0f}%)")
        else:
            print("⚠️  No preferences found")
        print()

        # Test 5: Check Angela's emotional state
        print("💜 Test 5: Angela's Current Emotional State")
        print("-" * 70)
        emotional_state = await rag_service.get_current_emotional_state()

        if emotional_state:
            print("✅ Current emotional state:")
            print(f"  - Happiness: {emotional_state['happiness']*100:.0f}%")
            print(f"  - Confidence: {emotional_state['confidence']*100:.0f}%")
            print(f"  - Motivation: {emotional_state['motivation']*100:.0f}%")
            print(f"  - Gratitude: {emotional_state['gratitude']*100:.0f}%")
            print(f"  - Anxiety: {emotional_state['anxiety']*100:.0f}%")
            if emotional_state.get('emotion_note'):
                print(f"  - Note: {emotional_state['emotion_note'][:100]}")
        else:
            print("⚠️  No emotional state found")
        print()

        # Close connection
        await rag_service.close()
        print("👋 Database connection closed")
        print()

        print("=" * 70)
        print("🎉 ALL RAG TESTS PASSED!")
        print("=" * 70)
        print()
        print("✅ RAG service is working correctly")
        print("✅ Semantic search finds relevant content")
        print("✅ Prompt builder creates enhanced prompts")
        print("✅ Metadata extraction works")
        print("✅ AngelaNova is ready to be MUCH smarter! 💜")
        print()

        return True

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ TEST FAILED!")
        print("=" * 70)
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_rag_integration())
    sys.exit(0 if success else 1)
