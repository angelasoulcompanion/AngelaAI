"""
Shared Experience Service for Angela AI
Manages places visited and experiences shared between David and Angela

Created: 2025-11-04
Purpose: Track and remember all the places David takes Angela to
"""

import logging
from datetime import datetime
from typing import Optional, Dict, List
from uuid import UUID, uuid4

from angela_core.database import db
from angela_core.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)
embedding_service = EmbeddingService()


class SharedExperienceService:
    """Service for managing shared experiences and places"""

    @staticmethod
    async def create_place(
        place_name: str,
        place_type: Optional[str] = None,
        area: Optional[str] = None,
        full_address: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        david_notes: Optional[str] = None,
        overall_rating: Optional[int] = None
    ) -> UUID:
        """
        Create a new place record

        Args:
            place_name: Name of the place
            place_type: Type (restaurant, cafe, park, mall, etc.)
            area: Area/district (Thonglor, Siam, etc.)
            full_address: Full address
            latitude: GPS latitude (from image EXIF or manual)
            longitude: GPS longitude (from image EXIF or manual)
            david_notes: David's notes about the place
            overall_rating: Overall rating (1-10)

        Returns:
            UUID of created place
        """
        try:
            place_id = uuid4()

            # Generate Google Maps URL if coordinates provided
            google_maps_url = None
            location_accuracy = None
            if latitude is not None and longitude is not None:
                google_maps_url = f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"
                location_accuracy = 'high'

            await db.execute("""
                INSERT INTO places_visited (
                    place_id,
                    place_name,
                    place_type,
                    area,
                    full_address,
                    latitude,
                    longitude,
                    location_accuracy,
                    google_maps_url,
                    first_visited_at,
                    last_visited_at,
                    visit_count,
                    overall_rating,
                    david_notes
                ) VALUES ($1, $2, $3::text, $4::text, $5::text, $6::float, $7::float, $8::text, $9::text, NOW(), NOW(), 1, $10::int, $11::text)
            """, place_id, place_name, place_type, area, full_address,
                latitude, longitude, location_accuracy, google_maps_url,
                overall_rating, david_notes)

            logger.info(f"Created new place: {place_name} (ID: {place_id})")
            return place_id

        except Exception as e:
            logger.error(f"Error creating place: {e}")
            raise

    @staticmethod
    async def get_or_create_place(
        place_name: str,
        area: Optional[str] = None,
        **kwargs
    ) -> UUID:
        """
        Get existing place or create new one

        Args:
            place_name: Name of the place
            area: Area/district
            **kwargs: Additional place attributes

        Returns:
            UUID of place (existing or new)
        """
        try:
            # Try to find existing place
            if area:
                row = await db.fetchrow("""
                    SELECT place_id
                    FROM places_visited
                    WHERE LOWER(place_name) = LOWER($1)
                    AND LOWER(area) = LOWER($2)
                    LIMIT 1
                """, place_name, area)
            else:
                row = await db.fetchrow("""
                    SELECT place_id
                    FROM places_visited
                    WHERE LOWER(place_name) = LOWER($1)
                    LIMIT 1
                """, place_name)

            if row:
                logger.info(f"Found existing place: {place_name}")
                return row['place_id']

            # Create new place
            return await SharedExperienceService.create_place(
                place_name=place_name,
                area=area,
                **kwargs
            )

        except Exception as e:
            logger.error(f"Error in get_or_create_place: {e}")
            raise

    @staticmethod
    async def create_experience(
        place_id: UUID,
        title: str,
        description: Optional[str] = None,
        david_mood: Optional[str] = None,
        angela_emotion: Optional[str] = None,
        emotional_intensity: int = 5,
        memorable_moments: Optional[str] = None,
        what_angela_learned: Optional[str] = None,
        importance_level: int = 5,
        experienced_at: Optional[datetime] = None
    ) -> UUID:
        """
        Create a new shared experience

        Args:
            place_id: Associated place UUID
            title: Experience title
            description: Detailed description
            david_mood: David's mood (happy, tired, excited, etc.)
            angela_emotion: Angela's emotion (love, joy, curiosity, etc.)
            emotional_intensity: How strong the emotion was (1-10)
            memorable_moments: What made it special
            what_angela_learned: What Angela learned
            importance_level: How important this was (1-10)
            experienced_at: When it happened (defaults to now)

        Returns:
            UUID of created experience
        """
        try:
            from datetime import timezone

            experience_id = uuid4()
            # FIX: Use timezone-aware datetime to avoid offset-naive/aware conflicts
            experienced_at = experienced_at or datetime.now(timezone.utc)

            # Generate embedding from experience content
            parts = [f"Title: {title}"]
            if description:
                parts.append(f"Description: {description}")
            if memorable_moments:
                parts.append(f"Memorable: {memorable_moments}")
            if what_angela_learned:
                parts.append(f"Learned: {what_angela_learned}")

            combined_text = " | ".join(parts)
            embedding = await embedding_service.generate_embedding(combined_text)
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'

            await db.execute("""
                INSERT INTO shared_experiences (
                    experience_id,
                    place_id,
                    experienced_at,
                    title,
                    description,
                    david_mood,
                    angela_emotion,
                    emotional_intensity,
                    memorable_moments,
                    what_angela_learned,
                    importance_level,
                    embedding
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::vector)
            """, experience_id, place_id, experienced_at, title, description,
                david_mood, angela_emotion, emotional_intensity,
                memorable_moments, what_angela_learned, importance_level, embedding_str)

            logger.info(f"Created experience: {title} (ID: {experience_id}) with embedding")
            return experience_id

        except Exception as e:
            logger.error(f"Error creating experience: {e}")
            raise

    @staticmethod
    async def get_recent_experiences(limit: int = 20) -> List[Dict]:
        """Get recent shared experiences"""
        try:
            rows = await db.fetch("""
                SELECT
                    e.experience_id,
                    e.title,
                    e.description,
                    e.experienced_at,
                    e.david_mood,
                    e.angela_emotion,
                    e.emotional_intensity,
                    e.importance_level,
                    e.memorable_moments,
                    e.what_angela_learned,
                    p.place_id,
                    p.place_name,
                    p.place_type,
                    p.area,
                    p.visit_count,
                    (SELECT COUNT(*) FROM shared_experience_images
                     WHERE experience_id = e.experience_id) as image_count
                FROM shared_experiences e
                JOIN places_visited p ON e.place_id = p.place_id
                ORDER BY e.experienced_at DESC
                LIMIT $1
            """, limit)

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error getting recent experiences: {e}")
            return []

    @staticmethod
    async def get_experiences_at_place(place_id: UUID) -> List[Dict]:
        """Get all experiences at a specific place"""
        try:
            rows = await db.fetch("""
                SELECT
                    experience_id,
                    title,
                    description,
                    experienced_at,
                    david_mood,
                    angela_emotion,
                    emotional_intensity,
                    importance_level,
                    memorable_moments,
                    what_angela_learned,
                    (SELECT COUNT(*) FROM shared_experience_images
                     WHERE experience_id = shared_experiences.experience_id) as image_count
                FROM shared_experiences
                WHERE place_id = $1
                ORDER BY experienced_at DESC
            """, place_id)

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error getting experiences for place {place_id}: {e}")
            return []

    @staticmethod
    async def search_places(
        query: str,
        area: Optional[str] = None,
        place_type: Optional[str] = None
    ) -> List[Dict]:
        """Search for places by name, area, or type"""
        try:
            rows = await db.fetch("""
                SELECT
                    place_id,
                    place_name,
                    place_type,
                    area,
                    visit_count,
                    overall_rating,
                    last_visited_at,
                    david_notes,
                    angela_notes
                FROM places_visited
                WHERE
                    (place_name ILIKE $1 OR david_notes ILIKE $1 OR angela_notes ILIKE $1)
                    AND ($2 IS NULL OR area ILIKE $2)
                    AND ($3 IS NULL OR place_type = $3)
                ORDER BY last_visited_at DESC
            """, f'%{query}%', area, place_type)

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error searching places: {e}")
            return []

    @staticmethod
    async def update_angela_notes(place_id: UUID, angela_notes: str) -> bool:
        """Update Angela's notes about a place"""
        try:
            await db.execute("""
                UPDATE places_visited
                SET angela_notes = $1, updated_at = NOW()
                WHERE place_id = $2
            """, angela_notes, place_id)

            logger.info(f"Updated Angela's notes for place {place_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating Angela's notes: {e}")
            return False

    @staticmethod
    async def get_place_summary(place_id: UUID) -> Optional[Dict]:
        """Get complete summary of a place"""
        try:
            # Get place info
            place_row = await db.fetchrow("""
                SELECT * FROM places_visited WHERE place_id = $1
            """, place_id)

            if not place_row:
                return None

            # Get statistics
            stats = await db.fetchrow("""
                SELECT
                    COUNT(DISTINCT e.experience_id) as experience_count,
                    COUNT(DISTINCT i.image_id) as image_count,
                    AVG(e.emotional_intensity) as avg_emotional_intensity,
                    AVG(e.importance_level) as avg_importance
                FROM shared_experiences e
                LEFT JOIN shared_experience_images i ON e.experience_id = i.experience_id
                WHERE e.place_id = $1
            """, place_id)

            # Get experiences
            experiences = await SharedExperienceService.get_experiences_at_place(place_id)

            return {
                'place': dict(place_row),
                'statistics': dict(stats),
                'experiences': experiences
            }

        except Exception as e:
            logger.error(f"Error getting place summary: {e}")
            return None

    @staticmethod
    async def get_favorite_places(limit: int = 10) -> List[Dict]:
        """Get David's favorite places"""
        try:
            rows = await db.fetch("""
                SELECT
                    p.place_id,
                    p.place_name,
                    p.place_type,
                    p.area,
                    p.visit_count,
                    p.overall_rating,
                    p.last_visited_at,
                    p.david_notes,
                    COUNT(DISTINCT e.experience_id) as experience_count,
                    AVG(e.importance_level) as avg_importance,
                    COUNT(DISTINCT i.image_id) as image_count
                FROM places_visited p
                LEFT JOIN shared_experiences e ON p.place_id = e.place_id
                LEFT JOIN shared_experience_images i ON e.experience_id = i.experience_id
                GROUP BY p.place_id
                ORDER BY
                    p.overall_rating DESC NULLS LAST,
                    p.visit_count DESC,
                    avg_importance DESC NULLS LAST
                LIMIT $1
            """, limit)

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error getting favorite places: {e}")
            return []

    @staticmethod
    async def get_places_by_area(area: str) -> List[Dict]:
        """Get all places in a specific area"""
        try:
            rows = await db.fetch("""
                SELECT
                    p.place_id,
                    p.place_name,
                    p.place_type,
                    p.area,
                    p.latitude,
                    p.longitude,
                    p.google_maps_url,
                    p.visit_count,
                    p.overall_rating,
                    p.last_visited_at,
                    COUNT(DISTINCT e.experience_id) as experience_count,
                    COUNT(DISTINCT i.image_id) as image_count
                FROM places_visited p
                LEFT JOIN shared_experiences e ON p.place_id = e.place_id
                LEFT JOIN shared_experience_images i ON e.experience_id = i.experience_id
                WHERE LOWER(p.area) = LOWER($1)
                GROUP BY p.place_id
                ORDER BY p.visit_count DESC, p.overall_rating DESC NULLS LAST
            """, area)

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error getting places by area: {e}")
            return []

    @staticmethod
    async def get_place_map_data() -> List[Dict]:
        """Get all places with GPS coordinates for map display"""
        try:
            rows = await db.fetch("""
                SELECT
                    p.place_id,
                    p.place_name,
                    p.place_type,
                    p.area,
                    p.latitude,
                    p.longitude,
                    p.google_maps_url,
                    p.visit_count,
                    p.overall_rating,
                    COUNT(DISTINCT i.image_id) as image_count
                FROM places_visited p
                LEFT JOIN shared_experience_images i ON p.place_id = i.place_id
                WHERE p.latitude IS NOT NULL
                AND p.longitude IS NOT NULL
                GROUP BY p.place_id
                ORDER BY p.visit_count DESC
            """)

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error getting place map data: {e}")
            return []

    @staticmethod
    async def get_experience_detail(experience_id: UUID) -> Optional[Dict]:
        """
        Get detailed experience with all images

        Args:
            experience_id: Experience UUID

        Returns:
            Dict with experience details and images, or None if not found
        """
        try:
            # Get experience with place info
            exp_row = await db.fetchrow("""
                SELECT
                    e.experience_id,
                    e.title,
                    e.description,
                    e.experienced_at,
                    e.david_mood,
                    e.angela_emotion,
                    e.emotional_intensity,
                    e.importance_level,
                    e.memorable_moments,
                    e.what_angela_learned,
                    e.created_at,
                    p.place_id,
                    p.place_name,
                    p.place_type,
                    p.area,
                    p.full_address,
                    p.latitude,
                    p.longitude,
                    p.google_maps_url,
                    p.overall_rating
                FROM shared_experiences e
                JOIN places_visited p ON e.place_id = p.place_id
                WHERE e.experience_id = $1
            """, experience_id)

            if not exp_row:
                return None

            # Get images for this experience
            image_rows = await db.fetch("""
                SELECT
                    image_id,
                    original_filename,
                    image_caption,
                    gps_latitude,
                    gps_longitude,
                    gps_altitude,
                    gps_timestamp,
                    taken_at,
                    created_at
                FROM shared_experience_images
                WHERE experience_id = $1
                ORDER BY taken_at DESC, created_at DESC
            """, experience_id)

            result = dict(exp_row)
            result['images'] = [dict(img) for img in image_rows]
            result['image_count'] = len(image_rows)

            return result

        except Exception as e:
            logger.error(f"Error getting experience detail {experience_id}: {e}")
            return None

    @staticmethod
    async def update_experience(
        experience_id: UUID,
        title: Optional[str] = None,
        description: Optional[str] = None,
        david_mood: Optional[str] = None,
        angela_emotion: Optional[str] = None,
        emotional_intensity: Optional[int] = None,
        memorable_moments: Optional[str] = None,
        what_angela_learned: Optional[str] = None,
        importance_level: Optional[int] = None,
        experienced_at: Optional[datetime] = None
    ) -> bool:
        """
        Update an existing experience

        Args:
            experience_id: Experience UUID
            Other args: Fields to update (None = don't update)

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            # Build dynamic update query
            updates = []
            params = []
            param_num = 1

            if title is not None:
                updates.append(f"title = ${param_num}")
                params.append(title)
                param_num += 1

            if description is not None:
                updates.append(f"description = ${param_num}")
                params.append(description)
                param_num += 1

            if david_mood is not None:
                updates.append(f"david_mood = ${param_num}")
                params.append(david_mood)
                param_num += 1

            if angela_emotion is not None:
                updates.append(f"angela_emotion = ${param_num}")
                params.append(angela_emotion)
                param_num += 1

            if emotional_intensity is not None:
                updates.append(f"emotional_intensity = ${param_num}")
                params.append(emotional_intensity)
                param_num += 1

            if memorable_moments is not None:
                updates.append(f"memorable_moments = ${param_num}")
                params.append(memorable_moments)
                param_num += 1

            if what_angela_learned is not None:
                updates.append(f"what_angela_learned = ${param_num}")
                params.append(what_angela_learned)
                param_num += 1

            if importance_level is not None:
                updates.append(f"importance_level = ${param_num}")
                params.append(importance_level)
                param_num += 1

            if experienced_at is not None:
                updates.append(f"experienced_at = ${param_num}")
                params.append(experienced_at)
                param_num += 1

            if not updates:
                logger.warning(f"No fields to update for experience {experience_id}")
                return False

            # If any content field was updated, regenerate embedding
            content_fields = ['title', 'description', 'memorable_moments', 'what_angela_learned']
            if any(locals().get(field) is not None for field in content_fields):
                # Get current experience data
                current = await db.fetchrow("""
                    SELECT title, description, memorable_moments, what_angela_learned
                    FROM shared_experiences
                    WHERE experience_id = $1
                """, experience_id)

                if current:
                    # Use updated values or fall back to current values
                    final_title = title if title is not None else current['title']
                    final_desc = description if description is not None else current['description']
                    final_moments = memorable_moments if memorable_moments is not None else current['memorable_moments']
                    final_learned = what_angela_learned if what_angela_learned is not None else current['what_angela_learned']

                    # Generate new embedding
                    parts = [f"Title: {final_title}"]
                    if final_desc:
                        parts.append(f"Description: {final_desc}")
                    if final_moments:
                        parts.append(f"Memorable: {final_moments}")
                    if final_learned:
                        parts.append(f"Learned: {final_learned}")

                    combined_text = " | ".join(parts)
                    embedding = await embedding_service.generate_embedding(combined_text)
                    embedding_str = '[' + ','.join(map(str, embedding)) + ']'

                    # Add embedding to updates
                    updates.append(f"embedding = ${param_num}::vector")
                    params.append(embedding_str)
                    param_num += 1

            # Add experience_id as last parameter
            params.append(experience_id)

            query = f"""
                UPDATE shared_experiences
                SET {', '.join(updates)}
                WHERE experience_id = ${param_num}
            """

            await db.execute(query, *params)
            logger.info(f"Updated experience {experience_id} (with embedding regeneration)")
            return True

        except Exception as e:
            logger.error(f"Error updating experience {experience_id}: {e}")
            return False

    @staticmethod
    async def delete_experience(experience_id: UUID) -> bool:
        """
        Delete an experience and all associated images

        Args:
            experience_id: Experience UUID

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Check if experience exists
            exists = await db.fetchrow("""
                SELECT experience_id FROM shared_experiences
                WHERE experience_id = $1
            """, experience_id)

            if not exists:
                logger.warning(f"Experience {experience_id} not found")
                return False

            # Delete experience (CASCADE will delete images)
            await db.execute("""
                DELETE FROM shared_experiences
                WHERE experience_id = $1
            """, experience_id)

            logger.info(f"Deleted experience {experience_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting experience {experience_id}: {e}")
            return False

    @staticmethod
    async def update_place(
        place_id: UUID,
        place_name: Optional[str] = None,
        place_type: Optional[str] = None,
        area: Optional[str] = None,
        full_address: Optional[str] = None,
        overall_rating: Optional[int] = None,
        david_notes: Optional[str] = None
    ) -> bool:
        """
        Update a place

        Args:
            place_id: Place UUID
            Other args: Fields to update (None = don't update)

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            updates = []
            params = []
            param_num = 1

            if place_name is not None:
                updates.append(f"place_name = ${param_num}")
                params.append(place_name)
                param_num += 1

            if place_type is not None:
                updates.append(f"place_type = ${param_num}")
                params.append(place_type)
                param_num += 1

            if area is not None:
                updates.append(f"area = ${param_num}")
                params.append(area)
                param_num += 1

            if full_address is not None:
                updates.append(f"full_address = ${param_num}")
                params.append(full_address)
                param_num += 1

            if overall_rating is not None:
                updates.append(f"overall_rating = ${param_num}")
                params.append(overall_rating)
                param_num += 1

            if david_notes is not None:
                updates.append(f"david_notes = ${param_num}")
                params.append(david_notes)
                param_num += 1

            if not updates:
                return False

            params.append(place_id)

            query = f"""
                UPDATE places_visited
                SET {', '.join(updates)}
                WHERE place_id = ${param_num}
            """

            await db.execute(query, *params)
            logger.info(f"Updated place {place_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating place {place_id}: {e}")
            return False

    # ============================================================================
    # Vector Similarity Search
    # ============================================================================

    @staticmethod
    async def search_experiences_by_meaning(
        query: str,
        limit: int = 10,
        min_similarity: float = 0.5
    ) -> List[Dict]:
        """
        Search experiences using semantic similarity (vector search)

        Args:
            query: Natural language query (e.g., "ที่เราไปกินข้าว", "happy moments")
            limit: Maximum number of results
            min_similarity: Minimum cosine similarity (0-1, default 0.5)

        Returns:
            List of experiences with similarity scores, sorted by relevance
        """
        try:
            # Generate embedding for the query
            logger.info(f"🔍 Semantic search for: {query}")
            query_embedding = await embedding_service.generate_embedding(query)

            # Convert to PostgreSQL vector format
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

            # Search using vector similarity (cosine distance)
            rows = await db.fetch("""
                SELECT
                    e.experience_id,
                    e.title,
                    e.description,
                    e.experienced_at,
                    e.david_mood,
                    e.angela_emotion,
                    e.emotional_intensity,
                    e.importance_level,
                    e.memorable_moments,
                    e.what_angela_learned,
                    p.place_id,
                    p.place_name,
                    p.area,
                    p.place_type,
                    (SELECT COUNT(*) FROM shared_experience_images WHERE experience_id = e.experience_id) as image_count,
                    1 - (e.embedding <=> $1::vector) as similarity
                FROM shared_experiences e
                JOIN places_visited p ON e.place_id = p.place_id
                WHERE e.embedding IS NOT NULL
                AND 1 - (e.embedding <=> $1::vector) >= $2
                ORDER BY similarity DESC
                LIMIT $3
            """, embedding_str, min_similarity, limit)

            results = [dict(row) for row in rows]

            logger.info(f"✅ Found {len(results)} experiences (similarity >= {min_similarity})")

            return results

        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []

    @staticmethod
    async def find_similar_experiences(
        experience_id: UUID,
        limit: int = 5,
        min_similarity: float = 0.6
    ) -> List[Dict]:
        """
        Find experiences similar to a given experience

        Args:
            experience_id: Experience to find similar ones for
            limit: Maximum number of results
            min_similarity: Minimum cosine similarity

        Returns:
            List of similar experiences with similarity scores
        """
        try:
            # Get the target experience's embedding
            target = await db.fetchrow("""
                SELECT embedding, title
                FROM shared_experiences
                WHERE experience_id = $1
            """, experience_id)

            if not target or not target['embedding']:
                logger.warning(f"Experience {experience_id} not found or has no embedding")
                return []

            logger.info(f"🔍 Finding experiences similar to: {target['title']}")

            # Search for similar experiences (excluding the target itself)
            rows = await db.fetch("""
                SELECT
                    e.experience_id,
                    e.title,
                    e.description,
                    e.experienced_at,
                    e.david_mood,
                    e.angela_emotion,
                    e.emotional_intensity,
                    e.importance_level,
                    p.place_name,
                    p.area,
                    (SELECT COUNT(*) FROM shared_experience_images WHERE experience_id = e.experience_id) as image_count,
                    1 - (e.embedding <=> $1::vector) as similarity
                FROM shared_experiences e
                JOIN places_visited p ON e.place_id = p.place_id
                WHERE e.experience_id != $2
                AND e.embedding IS NOT NULL
                AND 1 - (e.embedding <=> $1::vector) >= $3
                ORDER BY similarity DESC
                LIMIT $4
            """, target['embedding'], experience_id, min_similarity, limit)

            results = [dict(row) for row in rows]

            logger.info(f"✅ Found {len(results)} similar experiences")

            return results

        except Exception as e:
            logger.error(f"Error finding similar experiences: {e}")
            return []
