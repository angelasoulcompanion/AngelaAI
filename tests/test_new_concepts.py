#!/usr/bin/env python3
"""
Test New Concepts Extraction
ทดสอบการสกัด concepts ใหม่ที่ไม่เคยมี
"""

import asyncio
import logging
import sys
import uuid
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.database import db
from angela_core.services.continuous_memory_capture import continuous_memory

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('NewConceptsTest')


async def test_new_concepts():
    """Test extraction of brand new concepts"""
    logger.info("=" * 80)
    logger.info("TEST: EXTRACT NEW CONCEPTS")
    logger.info("=" * 80)

    await db.connect()

    # Baseline
    baseline = await db.fetchval("SELECT COUNT(*) FROM knowledge_nodes")
    logger.info(f"\n📊 Baseline: {baseline} knowledge nodes")

    # Create unique concept names for this test
    unique_id = str(uuid.uuid4())[:8]
    concept1 = f"QuantumComputing_{unique_id}"
    concept2 = f"NeuralArchitecture_{unique_id}"
    concept3 = f"EdgeAI_{unique_id}"

    logger.info(f"\n📝 Testing with unique concepts:")
    logger.info(f"  • {concept1}")
    logger.info(f"  • {concept2}")
    logger.info(f"  • {concept3}")

    # Test conversation with NEW concepts
    result = await continuous_memory.capture_interaction(
        david_message=f"""ที่รักคะ น้องกำลังเรียนรู้เรื่อง {concept1}
        และ {concept2} ซึ่งเป็นเทคโนโลยีใหม่สำหรับ AI systems
        น้องคิดว่า {concept3} จะเป็นอนาคตของ edge computing""",
        angela_response=f"""น้องเข้าใจค่ะที่รัก! {concept1} เป็นเทคโนโลยีที่น่าสนใจมาก
        ร่วมกับ {concept2} จะช่วยให้ AI systems ทำงานได้เร็วและมีประสิทธิภาพขึ้น
        และ {concept3} ก็จะทำให้ AI สามารถทำงานบน edge devices ได้ดีขึ้น
        น้องจะศึกษาเพิ่มเติมค่ะ! 💜""",
        auto_analyze=True
    )

    logger.info(f"\n✅ Captured:")
    logger.info(f"   Topic: {result['analysis']['topic']}")
    logger.info(f"   Importance: {result['analysis']['importance']}/10")

    # Wait for processing
    logger.info("\n⏳ Waiting for knowledge extraction...")
    await asyncio.sleep(4)

    # Check results
    new_count = await db.fetchval("SELECT COUNT(*) FROM knowledge_nodes")
    created = new_count - baseline

    logger.info("\n" + "=" * 80)
    logger.info("RESULTS:")
    logger.info("=" * 80)
    logger.info(f"Baseline: {baseline} nodes")
    logger.info(f"After: {new_count} nodes")
    logger.info(f"Created: {created} NEW nodes")

    # Show ALL recent nodes (not just new ones)
    logger.info("\n📚 Recent knowledge nodes (last 15):")
    query = """
        SELECT
            concept_name,
            concept_category,
            understanding_level,
            times_referenced,
            created_at
        FROM knowledge_nodes
        ORDER BY created_at DESC
        LIMIT 15
    """
    nodes = await db.fetch(query)

    for i, node in enumerate(nodes, 1):
        logger.info(f"  {i}. {node['concept_name']} ({node['concept_category']})")
        logger.info(f"     Level: {node['understanding_level']:.2f}, Refs: {node['times_referenced']}")

    # Check if our unique concepts were created
    found_concepts = []
    for concept in [concept1, concept2, concept3]:
        exists = await db.fetchval(
            "SELECT concept_name FROM knowledge_nodes WHERE concept_name ILIKE $1",
            f"%{concept}%"
        )
        if exists:
            found_concepts.append(concept)
            logger.info(f"\n  ✅ Found: {concept}")

    logger.info("\n" + "=" * 80)
    if len(found_concepts) > 0:
        logger.info(f"🎉 SUCCESS! Created {len(found_concepts)} new concept nodes!")
        logger.info("   Knowledge extraction is working properly!")
        success = True
    else:
        logger.warning("⚠️ WARNING: Expected new concepts not found")
        logger.warning("   Check LLM extraction or concept matching")
        success = False
    logger.info("=" * 80)

    await db.disconnect()
    return success


if __name__ == '__main__':
    success = asyncio.run(test_new_concepts())
    exit(0 if success else 1)
