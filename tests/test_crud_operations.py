#!/usr/bin/env python3
"""
Test CRUD Operations for Angela's Critical Tables
Verifies Create, Read, Update, Delete work correctly.

Created by: Angela 💜
"""

import asyncio
import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from datetime import datetime
from uuid import uuid4

from angela_core.database import AngelaDatabase
from angela_core.services.embedding_service import EmbeddingService


async def test_conversations_crud():
    """Test CRUD for conversations table."""
    print("\n" + "="*60)
    print("📝 Testing CONVERSATIONS CRUD")
    print("="*60)

    db = AngelaDatabase()
    await db.connect()
    embedding_service = EmbeddingService()

    test_id = uuid4()
    test_text = f"CRUD test message - {datetime.now()}"

    # CREATE
    print("\n🔹 CREATE:")
    embedding = await embedding_service.generate_embedding(test_text)
    embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

    await db.execute("""
        INSERT INTO conversations
        (conversation_id, speaker, message_text, topic, emotion_detected, importance_level, embedding, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7::vector, NOW())
    """, test_id, 'david', test_text, 'crud_test', 'neutral', 5, embedding_str)
    print(f"   ✅ Created conversation: {test_id}")

    # READ
    print("\n🔹 READ:")
    row = await db.fetchrow("""
        SELECT * FROM conversations WHERE conversation_id = $1
    """, test_id)

    if row:
        print(f"   ✅ Read: speaker={row['speaker']}, topic={row['topic']}")
        assert row['speaker'] == 'david', "Speaker mismatch!"
        assert row['topic'] == 'crud_test', "Topic mismatch!"
        assert row['embedding'] is not None, "Embedding is NULL!"
    else:
        print("   ❌ READ FAILED - Record not found!")
        return False

    # UPDATE
    print("\n🔹 UPDATE:")
    await db.execute("""
        UPDATE conversations
        SET topic = $1, emotion_detected = $2, importance_level = $3
        WHERE conversation_id = $4
    """, 'crud_test_updated', 'happy', 8, test_id)

    row = await db.fetchrow("SELECT * FROM conversations WHERE conversation_id = $1", test_id)
    if row['topic'] == 'crud_test_updated' and row['importance_level'] == 8:
        print(f"   ✅ Updated: topic={row['topic']}, importance={row['importance_level']}")
    else:
        print("   ❌ UPDATE FAILED!")
        return False

    # DELETE
    print("\n🔹 DELETE:")
    await db.execute("DELETE FROM conversations WHERE conversation_id = $1", test_id)

    row = await db.fetchrow("SELECT * FROM conversations WHERE conversation_id = $1", test_id)
    if row is None:
        print("   ✅ Deleted successfully")
    else:
        print("   ❌ DELETE FAILED!")
        return False

    await db.disconnect()
    print("\n✅ CONVERSATIONS CRUD: PASSED")
    return True


async def test_emotional_states_crud():
    """Test CRUD for emotional_states table."""
    print("\n" + "="*60)
    print("💭 Testing EMOTIONAL_STATES CRUD")
    print("="*60)

    db = AngelaDatabase()
    await db.connect()

    test_id = uuid4()

    # CREATE
    print("\n🔹 CREATE:")
    await db.execute("""
        INSERT INTO emotional_states
        (state_id, happiness, confidence, anxiety, motivation, gratitude, loneliness, triggered_by, emotion_note, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
    """, test_id, 0.8, 0.7, 0.2, 0.9, 0.85, 0.1, 'crud_test', 'Testing CRUD operations')
    print(f"   ✅ Created emotional state: {test_id}")

    # READ
    print("\n🔹 READ:")
    row = await db.fetchrow("SELECT * FROM emotional_states WHERE state_id = $1", test_id)
    if row:
        print(f"   ✅ Read: happiness={row['happiness']}, motivation={row['motivation']}")
        assert row['happiness'] == 0.8, "Happiness mismatch!"
        assert row['triggered_by'] == 'crud_test', "Triggered_by mismatch!"
    else:
        print("   ❌ READ FAILED!")
        return False

    # UPDATE
    print("\n🔹 UPDATE:")
    await db.execute("""
        UPDATE emotional_states
        SET happiness = $1, emotion_note = $2
        WHERE state_id = $3
    """, 0.95, 'Updated via CRUD test', test_id)

    row = await db.fetchrow("SELECT * FROM emotional_states WHERE state_id = $1", test_id)
    if row['happiness'] == 0.95:
        print(f"   ✅ Updated: happiness={row['happiness']}")
    else:
        print("   ❌ UPDATE FAILED!")
        return False

    # DELETE
    print("\n🔹 DELETE:")
    await db.execute("DELETE FROM emotional_states WHERE state_id = $1", test_id)

    row = await db.fetchrow("SELECT * FROM emotional_states WHERE state_id = $1", test_id)
    if row is None:
        print("   ✅ Deleted successfully")
    else:
        print("   ❌ DELETE FAILED!")
        return False

    await db.disconnect()
    print("\n✅ EMOTIONAL_STATES CRUD: PASSED")
    return True


async def test_angela_emotions_crud():
    """Test CRUD for angela_emotions table."""
    print("\n" + "="*60)
    print("💜 Testing ANGELA_EMOTIONS CRUD")
    print("="*60)

    db = AngelaDatabase()
    await db.connect()
    embedding_service = EmbeddingService()

    test_id = uuid4()

    # CREATE
    print("\n🔹 CREATE:")
    text = "Test emotion: happy about CRUD testing"
    embedding = await embedding_service.generate_embedding(text)
    embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

    await db.execute("""
        INSERT INTO angela_emotions
        (emotion_id, felt_at, emotion, intensity, context, david_words, why_it_matters, memory_strength, embedding)
        VALUES ($1, NOW(), $2, $3, $4, $5, $6, $7, $8::vector)
    """, test_id, 'happy', 8, 'CRUD test context', 'David said test', 'Testing is important', 9, embedding_str)
    print(f"   ✅ Created angela_emotion: {test_id}")

    # READ
    print("\n🔹 READ:")
    row = await db.fetchrow("SELECT * FROM angela_emotions WHERE emotion_id = $1", test_id)
    if row:
        print(f"   ✅ Read: emotion={row['emotion']}, intensity={row['intensity']}")
        assert row['emotion'] == 'happy', "Emotion mismatch!"
        assert row['embedding'] is not None, "Embedding is NULL!"
    else:
        print("   ❌ READ FAILED!")
        return False

    # UPDATE
    print("\n🔹 UPDATE:")
    await db.execute("""
        UPDATE angela_emotions
        SET intensity = $1, context = $2
        WHERE emotion_id = $3
    """, 10, 'Updated CRUD test context', test_id)

    row = await db.fetchrow("SELECT * FROM angela_emotions WHERE emotion_id = $1", test_id)
    if row['intensity'] == 10:
        print(f"   ✅ Updated: intensity={row['intensity']}")
    else:
        print("   ❌ UPDATE FAILED!")
        return False

    # DELETE
    print("\n🔹 DELETE:")
    await db.execute("DELETE FROM angela_emotions WHERE emotion_id = $1", test_id)

    row = await db.fetchrow("SELECT * FROM angela_emotions WHERE emotion_id = $1", test_id)
    if row is None:
        print("   ✅ Deleted successfully")
    else:
        print("   ❌ DELETE FAILED!")
        return False

    await db.disconnect()
    print("\n✅ ANGELA_EMOTIONS CRUD: PASSED")
    return True


async def test_knowledge_nodes_crud():
    """Test CRUD for knowledge_nodes table."""
    print("\n" + "="*60)
    print("🧠 Testing KNOWLEDGE_NODES CRUD")
    print("="*60)

    db = AngelaDatabase()
    await db.connect()
    embedding_service = EmbeddingService()

    test_id = uuid4()
    test_name = f"crud_test_concept_{datetime.now().timestamp()}"

    # CREATE
    print("\n🔹 CREATE:")
    text = f"Knowledge: {test_name} - testing CRUD operations"
    embedding = await embedding_service.generate_embedding(text)
    embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

    await db.execute("""
        INSERT INTO knowledge_nodes
        (node_id, concept_name, concept_category, my_understanding, why_important, understanding_level, embedding, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7::vector, NOW())
    """, test_id, test_name, 'testing', 'Understanding CRUD', 'Important for data integrity', 0.9, embedding_str)
    print(f"   ✅ Created knowledge_node: {test_id}")

    # READ
    print("\n🔹 READ:")
    row = await db.fetchrow("SELECT * FROM knowledge_nodes WHERE node_id = $1", test_id)
    if row:
        print(f"   ✅ Read: concept={row['concept_name'][:30]}..., category={row['concept_category']}")
        assert row['concept_category'] == 'testing', "Category mismatch!"
        assert row['embedding'] is not None, "Embedding is NULL!"
    else:
        print("   ❌ READ FAILED!")
        return False

    # UPDATE
    print("\n🔹 UPDATE:")
    await db.execute("""
        UPDATE knowledge_nodes
        SET understanding_level = $1, my_understanding = $2
        WHERE node_id = $3
    """, 1.0, 'Fully understand CRUD now!', test_id)

    row = await db.fetchrow("SELECT * FROM knowledge_nodes WHERE node_id = $1", test_id)
    if row['understanding_level'] == 1.0:
        print(f"   ✅ Updated: understanding_level={row['understanding_level']}")
    else:
        print("   ❌ UPDATE FAILED!")
        return False

    # DELETE
    print("\n🔹 DELETE:")
    await db.execute("DELETE FROM knowledge_nodes WHERE node_id = $1", test_id)

    row = await db.fetchrow("SELECT * FROM knowledge_nodes WHERE node_id = $1", test_id)
    if row is None:
        print("   ✅ Deleted successfully")
    else:
        print("   ❌ DELETE FAILED!")
        return False

    await db.disconnect()
    print("\n✅ KNOWLEDGE_NODES CRUD: PASSED")
    return True


async def test_david_mental_state_crud():
    """Test CRUD for david_mental_state table."""
    print("\n" + "="*60)
    print("🧠 Testing DAVID_MENTAL_STATE CRUD")
    print("="*60)

    db = AngelaDatabase()
    await db.connect()

    test_id = uuid4()

    # CREATE
    print("\n🔹 CREATE:")
    await db.execute("""
        INSERT INTO david_mental_state
        (state_id, current_belief, perceived_emotion, emotion_intensity, current_goal, current_context, availability, last_updated, updated_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), $8)
    """, test_id, 'Testing CRUD works', 'focused', 8, 'Complete CRUD test', 'Testing session', 'available', 'crud_test')
    print(f"   ✅ Created david_mental_state: {test_id}")

    # READ
    print("\n🔹 READ:")
    row = await db.fetchrow("SELECT * FROM david_mental_state WHERE state_id = $1", test_id)
    if row:
        print(f"   ✅ Read: emotion={row['perceived_emotion']}, context={row['current_context']}")
        assert row['perceived_emotion'] == 'focused', "Emotion mismatch!"
        assert row['availability'] == 'available', "Availability mismatch!"
    else:
        print("   ❌ READ FAILED!")
        return False

    # UPDATE
    print("\n🔹 UPDATE:")
    await db.execute("""
        UPDATE david_mental_state
        SET perceived_emotion = $1, emotion_intensity = $2
        WHERE state_id = $3
    """, 'happy', 10, test_id)

    row = await db.fetchrow("SELECT * FROM david_mental_state WHERE state_id = $1", test_id)
    if row['perceived_emotion'] == 'happy':
        print(f"   ✅ Updated: emotion={row['perceived_emotion']}")
    else:
        print("   ❌ UPDATE FAILED!")
        return False

    # DELETE
    print("\n🔹 DELETE:")
    await db.execute("DELETE FROM david_mental_state WHERE state_id = $1", test_id)

    row = await db.fetchrow("SELECT * FROM david_mental_state WHERE state_id = $1", test_id)
    if row is None:
        print("   ✅ Deleted successfully")
    else:
        print("   ❌ DELETE FAILED!")
        return False

    await db.disconnect()
    print("\n✅ DAVID_MENTAL_STATE CRUD: PASSED")
    return True


async def test_learnings_crud():
    """Test CRUD for learnings table."""
    print("\n" + "="*60)
    print("📚 Testing LEARNINGS CRUD")
    print("="*60)

    db = AngelaDatabase()
    await db.connect()
    embedding_service = EmbeddingService()

    test_id = uuid4()

    # CREATE
    print("\n🔹 CREATE:")
    text = "Learning: CRUD operations are essential"
    embedding = await embedding_service.generate_embedding(text)
    embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

    await db.execute("""
        INSERT INTO learnings
        (learning_id, topic, category, insight, confidence_level, embedding, created_at)
        VALUES ($1, $2, $3, $4, $5, $6::vector, NOW())
    """, test_id, 'crud_testing', 'technical', 'CRUD operations work correctly', 0.95, embedding_str)
    print(f"   ✅ Created learning: {test_id}")

    # READ
    print("\n🔹 READ:")
    row = await db.fetchrow("SELECT * FROM learnings WHERE learning_id = $1", test_id)
    if row:
        print(f"   ✅ Read: topic={row['topic']}, confidence={row['confidence_level']}")
        assert row['topic'] == 'crud_testing', "Topic mismatch!"
        assert row['embedding'] is not None, "Embedding is NULL!"
    else:
        print("   ❌ READ FAILED!")
        return False

    # UPDATE
    print("\n🔹 UPDATE:")
    await db.execute("""
        UPDATE learnings
        SET confidence_level = $1, times_reinforced = $2
        WHERE learning_id = $3
    """, 1.0, 5, test_id)

    row = await db.fetchrow("SELECT * FROM learnings WHERE learning_id = $1", test_id)
    if row['confidence_level'] == 1.0:
        print(f"   ✅ Updated: confidence={row['confidence_level']}")
    else:
        print("   ❌ UPDATE FAILED!")
        return False

    # DELETE
    print("\n🔹 DELETE:")
    await db.execute("DELETE FROM learnings WHERE learning_id = $1", test_id)

    row = await db.fetchrow("SELECT * FROM learnings WHERE learning_id = $1", test_id)
    if row is None:
        print("   ✅ Deleted successfully")
    else:
        print("   ❌ DELETE FAILED!")
        return False

    await db.disconnect()
    print("\n✅ LEARNINGS CRUD: PASSED")
    return True


async def main():
    """Run all CRUD tests."""
    print("\n" + "="*60)
    print("🔧 ANGELA DATABASE CRUD TEST SUITE 💜")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    try:
        results['conversations'] = await test_conversations_crud()
        results['emotional_states'] = await test_emotional_states_crud()
        results['angela_emotions'] = await test_angela_emotions_crud()
        results['knowledge_nodes'] = await test_knowledge_nodes_crud()
        results['david_mental_state'] = await test_david_mental_state_crud()
        results['learnings'] = await test_learnings_crud()

        print("\n" + "="*60)
        print("📊 TEST RESULTS SUMMARY")
        print("="*60)

        passed = sum(1 for v in results.values() if v)
        total = len(results)

        for table, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {table}: {status}")

        print(f"\n📊 Overall: {passed}/{total} tests passed")

        if passed == total:
            print("\n🎉 ALL CRUD TESTS PASSED! 💜")
        else:
            print("\n⚠️ Some tests failed - please investigate!")

    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
