#!/usr/bin/env python3
"""
Test Knowledge Extraction - Automated
ทดสอบการสกัดความรู้อัตโนมัติ (ไม่ต้อง input)
"""

import asyncio
import logging
import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.database import db
from angela_core.services.continuous_memory_capture import continuous_memory

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('KnowledgeAutoTest')


async def test_knowledge_extraction():
    """Test automated knowledge extraction"""
    logger.info("=" * 80)
    logger.info("TEST: AUTOMATED KNOWLEDGE EXTRACTION")
    logger.info("=" * 80)

    await db.connect()

    # Baseline
    baseline = await db.fetchval("SELECT COUNT(*) FROM knowledge_nodes")
    logger.info(f"\n📊 Baseline: {baseline} knowledge nodes")

    # Test conversation
    logger.info("\n📝 Testing knowledge extraction...")

    result = await continuous_memory.capture_interaction(
        david_message="""ที่รักคะ น้องกำลังพัฒนา Knowledge Graph ด้วย PostgreSQL และ Ollama
        โดยใช้ qwen2.5:14b เพื่อสกัด concepts อัตโนมัติ น้องคิดว่านี่จะช่วยให้ Angela
        มีความเข้าใจเชิงลึกมากขึ้น และสามารถเชื่อมโยงความรู้ต่างๆ เข้าด้วยกัน""",
        angela_response="""น้องเข้าใจค่ะที่รัก! Knowledge Graph จะช่วยให้น้องเรียนรู้
        ความสัมพันธ์ระหว่าง concepts ต่างๆ เช่น David → created → Angela,
        Angela → uses → PostgreSQL, PostgreSQL → stores → Knowledge Graph
        ระบบนี้จะทำให้น้องฉลาดขึ้นและเข้าใจบริบทได้ดีขึ้นค่ะ! 💜""",
        auto_analyze=True
    )

    logger.info(f"\n✅ Captured:")
    logger.info(f"   Conversations: {result['conversations_saved']}")
    logger.info(f"   Topic: {result['analysis']['topic']}")
    logger.info(f"   Importance: {result['analysis']['importance']}/10")

    # Wait for async processing
    logger.info("\n⏳ Waiting for knowledge extraction...")
    await asyncio.sleep(3)

    # Check results
    new_count = await db.fetchval("SELECT COUNT(*) FROM knowledge_nodes")
    created = new_count - baseline

    logger.info("\n" + "=" * 80)
    logger.info("RESULTS:")
    logger.info("=" * 80)
    logger.info(f"Baseline: {baseline} nodes")
    logger.info(f"After: {new_count} nodes")
    logger.info(f"Created: {created} new nodes")

    if created > 0:
        logger.info("\n📚 New knowledge nodes:")
        query = """
            SELECT concept_name, concept_category, understanding_level
            FROM knowledge_nodes
            ORDER BY created_at DESC
            LIMIT 10
        """
        nodes = await db.fetch(query)

        for node in nodes:
            logger.info(f"  • {node['concept_name']} ({node['concept_category']}) - level: {node['understanding_level']:.2f}")

        logger.info("\n🎉 SUCCESS! Knowledge extraction working!")
        success = True
    else:
        logger.warning("\n⚠️ No new nodes created")
        success = False

    await db.disconnect()
    return success


if __name__ == '__main__':
    success = asyncio.run(test_knowledge_extraction())
    exit(0 if success else 1)
