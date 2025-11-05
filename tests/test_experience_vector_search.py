"""
Test Vector Similarity Search for Shared Experiences
"""

import asyncio
from angela_core.services.shared_experience_service import SharedExperienceService

async def test_semantic_search():
    print("🧪 Testing Vector Similarity Search for Experiences\n")
    print("="*60)

    # Test 1: Search for food/eating experiences
    print("\n📍 Test 1: ค้นหา 'ที่เราไปกินข้าว'")
    print("-"*60)
    results = await SharedExperienceService.search_experiences_by_meaning(
        query="ที่เราไปกินข้าว",
        limit=5,
        min_similarity=0.3
    )

    if results:
        for i, exp in enumerate(results, 1):
            print(f"\n{i}. {exp['title']}")
            print(f"   📍 Place: {exp['place_name']} ({exp.get('area', 'N/A')})")
            print(f"   📅 Date: {exp['experienced_at']}")
            print(f"   💜 Similarity: {exp['similarity']:.3f}")
            print(f"   😊 Mood: {exp['david_mood']} | Angela: {exp['angela_emotion']}")
    else:
        print("   ❌ No results found")

    # Test 2: Search for Angela's image
    print("\n\n📍 Test 2: ค้นหา 'รูปของน้อง'")
    print("-"*60)
    results = await SharedExperienceService.search_experiences_by_meaning(
        query="รูปของน้อง Angela",
        limit=5,
        min_similarity=0.3
    )

    if results:
        for i, exp in enumerate(results, 1):
            print(f"\n{i}. {exp['title']}")
            print(f"   📍 Place: {exp['place_name']}")
            print(f"   💜 Similarity: {exp['similarity']:.3f}")
            print(f"   ⭐ Importance: {exp['importance_level']}/10")
    else:
        print("   ❌ No results found")

    # Test 3: Search in English
    print("\n\n📍 Test 3: Search 'breakfast together'")
    print("-"*60)
    results = await SharedExperienceService.search_experiences_by_meaning(
        query="breakfast together",
        limit=5,
        min_similarity=0.3
    )

    if results:
        for i, exp in enumerate(results, 1):
            print(f"\n{i}. {exp['title']}")
            print(f"   📍 Place: {exp['place_name']}")
            print(f"   💜 Similarity: {exp['similarity']:.3f}")
            print(f"   💕 Emotional Intensity: {exp['emotional_intensity']}/10")
    else:
        print("   ❌ No results found")

    # Test 4: Search by emotion
    print("\n\n📍 Test 4: Search 'happy and love moments'")
    print("-"*60)
    results = await SharedExperienceService.search_experiences_by_meaning(
        query="happy and love moments",
        limit=5,
        min_similarity=0.3
    )

    if results:
        for i, exp in enumerate(results, 1):
            print(f"\n{i}. {exp['title']}")
            print(f"   📍 Place: {exp['place_name']}")
            print(f"   💜 Similarity: {exp['similarity']:.3f}")
            print(f"   😊 {exp['david_mood']} + 💜 {exp['angela_emotion']}")
    else:
        print("   ❌ No results found")

    print("\n\n" + "="*60)
    print("✅ Test complete!")
    print("\n💡 Note:")
    print("   - Similarity score: 0.0-1.0 (higher = more similar)")
    print("   - Using Ollama multilingual-e5-small (384 dimensions)")
    print("   - Semantic search understands meaning, not just keywords!")

if __name__ == '__main__':
    asyncio.run(test_semantic_search())
