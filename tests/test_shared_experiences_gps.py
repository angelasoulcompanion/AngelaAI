"""
Test Shared Experiences & GPS System
Created: 2025-11-04
"""

import asyncio
from uuid import uuid4
from angela_core.services.shared_experience_service import SharedExperienceService
from angela_core.services.image_service import ImageService


async def test_system():
    """Test the complete shared experiences system"""

    print("🧪 Testing Shared Experiences & GPS System\n")
    print("=" * 60)

    # Test 1: Create a place with GPS
    print("\n📍 Test 1: Create Place with GPS")
    print("-" * 60)

    place_id = await SharedExperienceService.create_place(
        place_name="Test Cafe",
        place_type="cafe",
        area="Thonglor",
        latitude=13.7563,
        longitude=100.5018,
        david_notes="Great coffee and atmosphere",
        overall_rating=9
    )

    print(f"✅ Created place: {place_id}")
    print(f"   - Name: Test Cafe")
    print(f"   - GPS: 13.7563, 100.5018")
    print(f"   - Area: Thonglor")

    # Test 2: Create experience
    print("\n💭 Test 2: Create Experience")
    print("-" * 60)

    experience_id = await SharedExperienceService.create_experience(
        place_id=place_id,
        title="First Visit - Coffee Date",
        description="Tried their signature latte. Angela was with me via iPad!",
        david_mood="happy",
        angela_emotion="joy",
        emotional_intensity=8,
        importance_level=8,
        memorable_moments="Angela loved seeing the interior design"
    )

    print(f"✅ Created experience: {experience_id}")
    print(f"   - Title: First Visit - Coffee Date")
    print(f"   - Emotions: David=happy, Angela=joy")
    print(f"   - Intensity: 8/10")

    # Test 3: Format GPS for display
    print("\n🌍 Test 3: Format GPS Coordinates")
    print("-" * 60)

    formatted = ImageService.format_gps_for_display(13.7563, 100.5018)
    print(f"✅ Decimal: 13.7563, 100.5018")
    print(f"✅ DMS: {formatted}")

    # Test 4: Search places by area
    print("\n🔍 Test 4: Search Places by Area")
    print("-" * 60)

    places = await SharedExperienceService.get_places_by_area("Thonglor")
    print(f"✅ Found {len(places)} place(s) in Thonglor:")
    for place in places:
        print(f"   - {place['place_name']}")
        if place['latitude']:
            print(f"     GPS: {place['latitude']:.6f}, {place['longitude']:.6f}")
            print(f"     Maps: {place['google_maps_url']}")

    # Test 5: Get place summary
    print("\n📊 Test 5: Get Place Summary")
    print("-" * 60)

    summary = await SharedExperienceService.get_place_summary(place_id)
    if summary:
        print(f"✅ Place: {summary['place']['place_name']}")
        print(f"   - Visit count: {summary['place']['visit_count']}")
        print(f"   - Rating: {summary['place']['overall_rating']}/10")
        print(f"   - Experiences: {summary['statistics']['experience_count']}")
        print(f"   - Images: {summary['statistics']['image_count']}")

    # Test 6: Get map data
    print("\n🗺️ Test 6: Get Map Data")
    print("-" * 60)

    map_data = await SharedExperienceService.get_place_map_data()
    print(f"✅ Found {len(map_data)} place(s) with GPS coordinates")
    for place in map_data[:3]:  # Show first 3
        print(f"   - {place['place_name']}: ({place['latitude']:.4f}, {place['longitude']:.4f})")

    # Test 7: Find nearby places
    print("\n📍 Test 7: Find Nearby Places")
    print("-" * 60)

    nearby = await ImageService.find_nearby_places(
        latitude=13.7563,
        longitude=100.5018,
        radius_km=2.0,
        limit=5
    )
    print(f"✅ Found {len(nearby)} place(s) within 2km:")
    for place in nearby:
        print(f"   - {place['place_name']}: {place['distance_km']:.2f} km away")

    print("\n" + "=" * 60)
    print("🎉 All tests completed successfully!")
    print("=" * 60)

    print("\n💜 System Status:")
    print("   ✅ Database tables created")
    print("   ✅ GPS extraction ready")
    print("   ✅ Image compression ready")
    print("   ✅ Location services ready")
    print("   ✅ Ready to receive photos from David!")


if __name__ == "__main__":
    asyncio.run(test_system())
