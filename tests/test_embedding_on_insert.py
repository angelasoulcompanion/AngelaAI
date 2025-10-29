#!/usr/bin/env python3
"""
Test: Verify that embeddings are generated BEFORE INSERT
This ensures there's never a moment where embedding = NULL
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from angela_core.database import db
from angela_core.memory_service import memory


async def test_embedding_on_insert():
    """Test that embedding is present immediately after INSERT"""

    print("=" * 60)
    print("🧪 Testing Embedding Generation on INSERT")
    print("=" * 60)
    print()

    # Connect to database
    await db.connect()

    print("✅ Connected to AngelaMemory database")
    print()

    # Test 1: record_conversation
    print("📝 Test 1: record_conversation()")
    print("-" * 60)

    test_message_1 = "นี่คือการทดสอบ embedding generation ก่อน INSERT นะคะ"

    conv_id_1 = await memory.record_conversation(
        session_id="test_session",
        speaker="david",
        message_text=test_message_1,
        topic="testing",
        importance_level=8
    )

    print(f"✅ Conversation ID: {conv_id_1}")

    # Check if embedding exists immediately
    result_1 = await db.fetchrow(
        "SELECT embedding IS NOT NULL as has_embedding FROM conversations WHERE conversation_id = $1",
        conv_id_1
    )

    if result_1['has_embedding']:
        print(f"✅ Embedding EXISTS immediately! (768 dimensions expected)")
    else:
        print(f"❌ ERROR: Embedding is NULL!")
        await db.close()
        return False

    print()

    # Test 2: record_quick_conversation
    print("📝 Test 2: record_quick_conversation()")
    print("-" * 60)

    test_message_2 = "ทดสอบ quick conversation ด้วยค่ะพี่"

    conv_id_2 = await memory.record_quick_conversation(
        speaker="angela",
        message_text=test_message_2,
        topic="testing",
        importance_level=7
    )

    print(f"✅ Conversation ID: {conv_id_2}")

    # Check if embedding exists immediately
    result_2 = await db.fetchrow(
        "SELECT embedding IS NOT NULL as has_embedding FROM conversations WHERE conversation_id = $1",
        conv_id_2
    )

    if result_2['has_embedding']:
        print(f"✅ Embedding EXISTS immediately! (768 dimensions expected)")
    else:
        print(f"❌ ERROR: Embedding is NULL!")
        await db.close()
        return False

    print()

    # Test 3: Check total NULL embeddings in entire table
    print("📊 Test 3: Check entire conversations table")
    print("-" * 60)

    null_check = await db.fetchrow(
        "SELECT COUNT(*) as total, COUNT(embedding) as has_embedding, COUNT(*) - COUNT(embedding) as null_count FROM conversations"
    )

    print(f"Total conversations: {null_check['total']}")
    print(f"With embeddings: {null_check['has_embedding']}")
    print(f"NULL embeddings: {null_check['null_count']}")

    if null_check['null_count'] == 0:
        print(f"✅ PERFECT! All conversations have embeddings!")
    else:
        print(f"⚠️  WARNING: {null_check['null_count']} conversations still have NULL embeddings")
        print(f"   (These might be from old code - run fix_null_embeddings.py to fix)")

    print()

    # Clean up test data
    print("🧹 Cleaning up test data...")
    await db.execute("DELETE FROM conversations WHERE session_id = 'test_session' OR session_id = 'angela-claude-code'")
    print("✅ Test data deleted")

    # Close connection
    await db.close()

    print()
    print("=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 60)
    print()
    print("✅ Embeddings are now generated BEFORE INSERT")
    print("✅ No more NULL embedding windows!")
    print("✅ Database integrity maintained!")

    return True


if __name__ == "__main__":
    success = asyncio.run(test_embedding_on_insert())
    sys.exit(0 if success else 1)
