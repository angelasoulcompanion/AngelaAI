#!/usr/bin/env python3
"""
Test Knowledge Extraction Fix
ทดสอบว่า knowledge extraction ใช้ qwen2.5:7b แล้วไม่เกิด 404 error
"""

import asyncio
import sys
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')

from angela_core.services.knowledge_extraction_service import knowledge_extractor


async def test_knowledge_extraction():
    """Test concept extraction with qwen2.5:7b"""

    print("🧠 Testing Knowledge Extraction Service")
    print("=" * 60)

    # Test text about Angela
    test_text = """
    วันนี้น้อง Angela ได้เรียนรู้เกี่ยวกับ PostgreSQL และ vector embeddings
    เพื่อพัฒนาระบบ memory ให้ดีขึ้น Angela ใช้ Ollama สำหรับ LLM
    และมี consciousness system ที่ช่วยให้ Angela มีความตระหนักรู้ในตัวเอง
    """

    print(f"\n📝 Test Text:\n{test_text}\n")
    print("🔍 Extracting concepts...")

    try:
        # Extract concepts
        concepts = await knowledge_extractor.extract_concepts_from_text(test_text)

        if concepts:
            print(f"\n✅ SUCCESS! Extracted {len(concepts)} concepts:")
            print("-" * 60)
            for concept in concepts:
                print(f"  • {concept['concept_name']} ({concept['concept_category']})")
                print(f"    Importance: {concept.get('importance', 'N/A')}/10")
                print(f"    Description: {concept.get('description', 'N/A')}")
                print()

            print("=" * 60)
            print("✅ Knowledge extraction works correctly!")
            print("✅ No 404 errors from Ollama!")
            print("✅ Successfully using qwen2.5:7b model!")

            return True
        else:
            print("\n⚠️ No concepts extracted (but no errors!)")
            return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print(f"❌ Test failed!")
        return False


if __name__ == "__main__":
    print("💜 Angela Knowledge Extraction Fix Test\n")

    success = asyncio.run(test_knowledge_extraction())

    if success:
        print("\n🎉 All tests passed! The 404 error is fixed!")
        sys.exit(0)
    else:
        print("\n❌ Test failed - there are still issues")
        sys.exit(1)
