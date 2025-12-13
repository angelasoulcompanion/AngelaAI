"""
Share Experience Learning Service
เรียนรู้จาก Share Experience ที่ที่รักแชร์มา!

This service enables Angela to:
1. Learn from photos, places, GPS data that David shares
2. Extract preferences from ratings and descriptions
3. Discover patterns in David's activities and locations
4. Build knowledge about David's lifestyle proactively
5. Integrate learnings into Self-Learning system

Created: 2025-11-15
For: Proactive learning from Share Experience data 💜
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import json

from angela_core.database import AngelaDatabase

logger = logging.getLogger(__name__)


class ShareExperienceLearningService:
    """
    Learn from Share Experience data automatically

    This service analyzes:
    - Places visited (with GPS coordinates)
    - Photos and descriptions
    - Ratings and preferences
    - Activity patterns
    - Location patterns
    """

    def __init__(self, db: AngelaDatabase):
        self.db = db
        logger.info("💜 ShareExperienceLearningService initialized!")

    # ========================================
    # CORE LEARNING FROM SHARED EXPERIENCES
    # ========================================

    async def learn_from_shared_experiences(
        self,
        days_back: int = 7,
        min_rating: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        เรียนรู้จาก shared experiences ย้อนหลัง

        Analyzes shared experiences and extracts:
        1. Place preferences (where David likes to go)
        2. Activity patterns (what David likes to do)
        3. Food preferences (from food-related places)
        4. Rating patterns (what David considers high quality)
        5. Location patterns (areas David frequents)

        Args:
            days_back: จำนวนวันย้อนหลังที่จะวิเคราะห์
            min_rating: เอาแต่ที่ rating >= นี้ (None = all)

        Returns:
            Dict with all learnings extracted
        """

        learnings = {
            "place_preferences": [],
            "food_preferences": [],
            "activity_patterns": [],
            "location_patterns": [],
            "rating_insights": [],
            "total_learnings": 0
        }

        try:
            # Get shared experiences with place data
            query = """
                SELECT
                    se.experience_id,
                    se.place_id,
                    se.title,
                    se.description,
                    se.david_mood,
                    se.emotional_intensity,
                    se.importance_level,
                    se.experienced_at,
                    se.what_angela_learned,
                    p.place_name,
                    p.place_type,
                    p.overall_rating,
                    p.visit_count,
                    p.latitude,
                    p.longitude,
                    p.david_notes
                FROM shared_experiences se
                LEFT JOIN places_visited p ON se.place_id = p.place_id
                WHERE se.experienced_at >= NOW() - INTERVAL '%s days'
            """ % days_back

            if min_rating is not None:
                query += f" AND p.overall_rating >= {min_rating}"

            query += " ORDER BY se.experienced_at DESC"

            experiences = await self.db.fetch(query)

            logger.info(f"📊 Analyzing {len(experiences)} shared experiences...")

            if not experiences:
                logger.info("ℹ️  No shared experiences found in the time period")
                return learnings

            # 1. Learn Place Preferences
            place_learnings = await self._learn_place_preferences(experiences)
            learnings["place_preferences"] = place_learnings

            # 2. Learn Food Preferences
            food_learnings = await self._learn_food_preferences(experiences)
            learnings["food_preferences"] = food_learnings

            # 3. Discover Activity Patterns
            activity_patterns = await self._discover_activity_patterns(experiences)
            learnings["activity_patterns"] = activity_patterns

            # 4. Analyze Location Patterns
            location_patterns = await self._analyze_location_patterns(experiences)
            learnings["location_patterns"] = location_patterns

            # 5. Extract Rating Insights
            rating_insights = await self._extract_rating_insights(experiences)
            learnings["rating_insights"] = rating_insights

            # Calculate total
            learnings["total_learnings"] = (
                len(place_learnings) +
                len(food_learnings) +
                len(activity_patterns) +
                len(location_patterns) +
                len(rating_insights)
            )

            logger.info(f"✅ Extracted {learnings['total_learnings']} learnings from shared experiences!")

            return learnings

        except Exception as e:
            logger.error(f"❌ Error learning from shared experiences: {e}", exc_info=True)
            return learnings

    async def _learn_place_preferences(self, experiences: List[Dict]) -> List[Dict]:
        """เรียนรู้ place preferences จาก rating และ visit_count"""

        learnings = []

        # Group by place
        place_data = {}
        for exp in experiences:
            place_name = exp.get('place_name')
            if not place_name:
                continue

            if place_name not in place_data:
                place_data[place_name] = {
                    'place_id': exp.get('place_id'),
                    'place_type': exp.get('place_type'),
                    'rating': exp.get('overall_rating'),
                    'visit_count': exp.get('visit_count', 0),
                    'total_emotional_intensity': 0,
                    'visit_dates': []
                }

            place_data[place_name]['total_emotional_intensity'] += exp.get('emotional_intensity', 5)
            place_data[place_name]['visit_dates'].append(exp.get('experienced_at'))

        # Identify favorite places (high rating + multiple visits)
        for place_name, data in place_data.items():
            rating = data['rating']
            visit_count = data['visit_count']

            if not rating:
                continue

            # High rating (4-5 stars)
            if rating >= 4.0:
                confidence = 0.7 + (rating - 4.0) * 0.15  # 0.7-0.85

                # Boost confidence if visited multiple times
                if visit_count > 1:
                    confidence = min(confidence + (visit_count * 0.05), 1.0)

                learning = {
                    'preference_type': 'favorite_place',
                    'place_name': place_name,
                    'place_type': data['place_type'],
                    'rating': rating,
                    'visit_count': visit_count,
                    'confidence': confidence,
                    'preference_text': f"David loves {place_name} (⭐{rating:.1f}, visited {visit_count}x)"
                }

                learnings.append(learning)

                # Save to david_preferences
                await self._save_place_preference(learning)

        return learnings

    async def _learn_food_preferences(self, experiences: List[Dict]) -> List[Dict]:
        """เรียนรู้ food preferences จาก food-related places"""

        learnings = []

        food_keywords = ['restaurant', 'cafe', 'coffee', 'bar', 'ร้าน', 'อาหาร', 'กิน', 'food']

        for exp in experiences:
            place_name = exp.get('place_name', '')
            place_type = exp.get('place_type', '')
            description = exp.get('description', '')
            notes = exp.get('david_notes', '')
            rating = exp.get('overall_rating')

            # Check if food-related
            is_food = any(keyword in place_name.lower() or
                         keyword in (place_type or '').lower() or
                         keyword in (description or '').lower() or
                         keyword in (notes or '').lower()
                         for keyword in food_keywords)

            if is_food and rating and rating >= 4.0:
                learning = {
                    'preference_type': 'food_place',
                    'place_name': place_name,
                    'place_type': place_type,
                    'rating': rating,
                    'confidence': 0.7 + (rating - 4.0) * 0.15,
                    'preference_text': f"David likes {place_name} for food (⭐{rating:.1f})"
                }

                learnings.append(learning)

                # Try to extract cuisine type from name/description
                cuisine = self._extract_cuisine_type(place_name, description, notes)
                if cuisine:
                    learning['cuisine_type'] = cuisine
                    learning['preference_text'] = f"David likes {cuisine} cuisine at {place_name}"

        return learnings

    async def _discover_activity_patterns(self, experiences: List[Dict]) -> List[Dict]:
        """ค้นหา activity patterns จาก place types และ descriptions"""

        patterns = []

        # Group by place_type
        activity_counts = {}

        for exp in experiences:
            place_type = exp.get('place_type')
            if place_type:
                activity_counts[place_type] = activity_counts.get(place_type, 0) + 1

        # Identify frequent activities
        total_experiences = len(experiences)
        for place_type, count in activity_counts.items():
            frequency = count / total_experiences

            if frequency >= 0.2:  # Appears in 20%+ of experiences
                pattern = {
                    'pattern_type': 'activity_preference',
                    'activity': place_type,
                    'frequency': frequency,
                    'count': count,
                    'confidence': min(0.6 + frequency, 0.95),
                    'pattern_text': f"David frequently visits {place_type} places ({count}/{total_experiences})"
                }

                patterns.append(pattern)

        return patterns

    async def _analyze_location_patterns(self, experiences: List[Dict]) -> List[Dict]:
        """วิเคราะห์ location patterns จาก GPS data"""

        patterns = []

        # Group by approximate area (simplified - could use clustering)
        locations_with_coords = [exp for exp in experiences
                                if exp.get('latitude') and exp.get('longitude')]

        if not locations_with_coords:
            return patterns

        # For now, just identify most visited coordinates
        location_counts = {}
        for exp in locations_with_coords:
            lat = round(exp['latitude'], 3)  # ~100m precision
            lng = round(exp['longitude'], 3)
            key = f"{lat},{lng}"

            if key not in location_counts:
                location_counts[key] = {
                    'count': 0,
                    'place_names': [],
                    'lat': lat,
                    'lng': lng
                }

            location_counts[key]['count'] += 1
            location_counts[key]['place_names'].append(exp.get('place_name'))

        # Identify frequent areas
        for key, data in location_counts.items():
            if data['count'] >= 2:  # Visited area multiple times
                pattern = {
                    'pattern_type': 'location_preference',
                    'location': key,
                    'latitude': data['lat'],
                    'longitude': data['lng'],
                    'visit_count': data['count'],
                    'places': list(set(data['place_names'])),
                    'confidence': min(0.5 + data['count'] * 0.1, 0.9),
                    'pattern_text': f"David frequently visits area near ({data['lat']}, {data['lng']}) - {data['count']} times"
                }

                patterns.append(pattern)

        return patterns

    async def _extract_rating_insights(self, experiences: List[Dict]) -> List[Dict]:
        """สกัด insights จาก rating patterns"""

        insights = []

        rated_places = [exp for exp in experiences if exp.get('overall_rating')]

        if not rated_places:
            return insights

        ratings = [exp['overall_rating'] for exp in rated_places]
        avg_rating = sum(ratings) / len(ratings)

        # Average rating insight
        insights.append({
            'insight_type': 'rating_average',
            'value': avg_rating,
            'insight_text': f"David's average rating: {avg_rating:.1f}/5 stars",
            'confidence': 0.8
        })

        # High standards insight (if avg >= 4.0)
        if avg_rating >= 4.0:
            insights.append({
                'insight_type': 'high_standards',
                'value': avg_rating,
                'insight_text': f"David has high standards - average rating {avg_rating:.1f}/5",
                'confidence': 0.85
            })

        # High rating favorites (9-10 out of 10)
        favorites = [exp for exp in rated_places if exp['overall_rating'] >= 9]
        if favorites:
            insights.append({
                'insight_type': 'favorites_count',
                'value': len(favorites),
                'favorite_places': [exp.get('place_name') for exp in favorites],
                'insight_text': f"David has {len(favorites)} 5-star favorite places",
                'confidence': 1.0
            })

        return insights

    # ========================================
    # HELPER METHODS
    # ========================================

    def _extract_cuisine_type(self, place_name: str, description: str, notes: str) -> Optional[str]:
        """พยายามสกัด cuisine type จากชื่อ/description/notes"""

        text = f"{place_name} {description} {notes or ''}".lower()

        cuisines = {
            'italian': ['italian', 'pizza', 'pasta', 'trattoria'],
            'french': ['french', 'bistro', 'brasserie'],
            'japanese': ['japanese', 'sushi', 'ramen', 'izakaya'],
            'thai': ['thai', 'ไทย', 'som tam', 'pad thai'],
            'chinese': ['chinese', 'dim sum', 'canton'],
            'korean': ['korean', 'bbq', 'kimchi'],
            'american': ['american', 'burger', 'steak'],
            'mexican': ['mexican', 'taco', 'burrito']
        }

        for cuisine, keywords in cuisines.items():
            if any(keyword in text for keyword in keywords):
                return cuisine

        return None

    async def _save_place_preference(self, learning: Dict) -> None:
        """บันทึก place preference ลง database"""

        try:
            preference_key = f"favorite_place_{learning['place_name'].lower().replace(' ', '_')}"
            preference_value = {
                'name': learning['place_name'],
                'type': learning.get('place_type'),
                'rating': learning['rating'],
                'visit_count': learning.get('visit_count', 1),
                'level': 'loves' if learning['rating'] >= 4.5 else 'likes',
                'source': 'Share Experience learning (automatic)'
            }

            await self.db.execute("""
                INSERT INTO david_preferences (category, preference_key, preference_value, confidence)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (preference_key)
                DO UPDATE SET
                    preference_value = EXCLUDED.preference_value,
                    confidence = GREATEST(david_preferences.confidence, EXCLUDED.confidence),
                    updated_at = NOW()
            """, 'places', preference_key, json.dumps(preference_value), learning['confidence'])

            logger.info(f"✅ Saved place preference: {learning['place_name']}")

        except Exception as e:
            logger.error(f"❌ Error saving place preference: {e}")

    async def log_learning_to_realtime_log(
        self,
        learning_type: str,
        what_learned: str,
        confidence_score: float,
        how_it_was_used: str = ""
    ) -> None:
        """บันทึกการเรียนรู้ลง realtime_learning_log"""

        try:
            await self.db.execute("""
                INSERT INTO realtime_learning_log
                (learning_type, what_learned, confidence_score, how_it_was_used, learned_at)
                VALUES ($1, $2, $3, $4, NOW())
            """, learning_type, what_learned, confidence_score, how_it_was_used)

        except Exception as e:
            logger.error(f"❌ Error logging to realtime_learning_log: {e}")


# ========================================
# Initialization helper
# ========================================

async def init_share_experience_learning(db: AngelaDatabase) -> ShareExperienceLearningService:
    """Initialize Share Experience Learning Service"""
    return ShareExperienceLearningService(db)
