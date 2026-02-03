"""Shared experiences endpoints."""
from fastapi import APIRouter, Depends, Query

from db import get_conn, get_pool

router = APIRouter(prefix="/api/experiences", tags=["experiences"])


@router.get("/shared")
async def get_shared_experiences(limit: int = Query(50, ge=1, le=200), conn=Depends(get_conn)):
    """Fetch shared experiences"""
    rows = await conn.fetch("""
        SELECT se.experience_id::text, se.place_id::text, pv.place_name, se.experienced_at,
               se.title, se.description, se.david_mood, se.angela_emotion, se.emotional_intensity,
               se.memorable_moments, se.what_angela_learned, se.importance_level, se.created_at
        FROM shared_experiences se
        LEFT JOIN places_visited pv ON se.place_id = pv.place_id
        ORDER BY se.experienced_at DESC
        LIMIT $1
    """, limit)
    return [dict(r) for r in rows]


@router.get("/images/{experience_id}")
async def get_experience_images(experience_id: str, conn=Depends(get_conn)):
    """Fetch images for a specific experience"""
    rows = await conn.fetch("""
        SELECT image_id::text, experience_id::text, place_id::text,
               image_format, original_filename, file_size_bytes,
               width_px, height_px, gps_latitude, gps_longitude, gps_altitude,
               gps_timestamp, image_caption, angela_observation, taken_at,
               uploaded_at, created_at
        FROM shared_experience_images
        WHERE experience_id = $1
        ORDER BY taken_at DESC NULLS LAST, created_at DESC
    """, experience_id)
    return [dict(r) for r in rows]
