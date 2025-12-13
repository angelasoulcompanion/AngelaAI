"""
Shared Experiences API Router
Handles upload, CRUD operations for places and experiences with photos

Created: 2025-11-04
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4
import logging

from angela_core.services.shared_experience_service import SharedExperienceService
from angela_core.services.image_service import ImageService

router = APIRouter(prefix="/api/experiences", tags=["experiences"])
logger = logging.getLogger(__name__)


# ============================================================================
# Upload & Create
# ============================================================================

@router.post("/upload")
async def upload_experience(
    images: List[UploadFile] = File(...),
    place_name: str = Form(...),
    place_type: Optional[str] = Form(None),
    area: Optional[str] = Form(None),
    full_address: Optional[str] = Form(None),
    overall_rating: Optional[int] = Form(None),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    david_mood: Optional[str] = Form(None),
    angela_emotion: Optional[str] = Form(None),
    emotional_intensity: Optional[int] = Form(None),
    memorable_moments: Optional[str] = Form(None),
    what_angela_learned: Optional[str] = Form(None),
    importance_level: Optional[int] = Form(None),
    image_captions: Optional[str] = Form(None),
    experienced_at: Optional[str] = Form(None),
    # ✅ ADD GPS COORDINATES (from mobile app)
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None)
):
    """
    Upload multiple images with experience details

    This creates:
    1. Place (or gets existing)
    2. Experience
    3. Multiple images with GPS extraction
    """
    try:
        from datetime import timezone

        # Parse datetime if provided
        exp_datetime = None
        if experienced_at:
            try:
                exp_datetime = datetime.fromisoformat(experienced_at)
                # If datetime is naive (no timezone), assume UTC
                if exp_datetime.tzinfo is None:
                    exp_datetime = exp_datetime.replace(tzinfo=timezone.utc)
            except:
                exp_datetime = None

        # Step 1: Get or create place
        # ✅ Include GPS coordinates from mobile app
        place_id = await SharedExperienceService.get_or_create_place(
            place_name=place_name,
            place_type=place_type,
            area=area,
            full_address=full_address,
            overall_rating=overall_rating,
            latitude=latitude,  # ✅ From mobile app GPS (CRITICAL FOR ANGELA'S LEARNING!)
            longitude=longitude  # ✅ From mobile app GPS
        )

        if latitude and longitude:
            logger.info(f"📍 Place created/retrieved with GPS: lat={latitude}, lon={longitude}")
        else:
            logger.warning(f"⚠️ No GPS coordinates provided from mobile app")

        # Step 2: Create experience
        experience_id = await SharedExperienceService.create_experience(
            place_id=place_id,
            title=title,
            description=description,
            david_mood=david_mood,
            angela_emotion=angela_emotion,
            emotional_intensity=emotional_intensity,
            memorable_moments=memorable_moments,
            what_angela_learned=what_angela_learned,
            importance_level=importance_level,
            experienced_at=exp_datetime
        )

        # Parse captions (comma-separated)
        captions_list = []
        if image_captions:
            captions_list = [c.strip() for c in image_captions.split(',')]

        # Step 3: Save all images (with GPS from mobile app)
        # ✅ Pass GPS coordinates to each image so they're saved in shared_experience_images table
        image_ids = []
        for idx, image in enumerate(images):
            image_data = await image.read()
            caption = captions_list[idx] if idx < len(captions_list) else None

            image_id = await ImageService.save_image_to_db(
                image_data=image_data,
                experience_id=experience_id,
                place_id=place_id,
                original_filename=image.filename,
                image_caption=caption,
                latitude=latitude,  # ✅ Pass GPS to image (CRITICAL!)
                longitude=longitude  # ✅ Pass GPS to image (CRITICAL!)
            )
            image_ids.append(str(image_id))

        # Step 4: Update place GPS from images if available
        await ImageService.update_place_gps_from_images(place_id)

        return {
            "success": True,
            "place_id": str(place_id),
            "experience_id": str(experience_id),
            "image_ids": image_ids,
            "image_count": len(image_ids),
            "message": f"✅ Experience and {len(image_ids)} photos saved successfully! 💜"
        }

    except Exception as e:
        logger.error(f"Error uploading experience: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Read - List & Get
# ============================================================================

@router.get("/search")
async def search_experiences(
    q: str,
    limit: int = 20,
    min_similarity: float = 0.3
):
    """
    Search experiences using semantic similarity (vector search)

    Args:
        q: Search query (natural language, Thai or English)
        limit: Maximum number of results
        min_similarity: Minimum similarity score (0.0-1.0)

    Returns:
        Experiences sorted by relevance with similarity scores
    """
    try:
        results = await SharedExperienceService.search_experiences_by_meaning(
            query=q,
            limit=limit,
            min_similarity=min_similarity
        )

        return {
            "success": True,
            "query": q,
            "count": len(results),
            "experiences": results
        }

    except Exception as e:
        logger.error(f"Error searching experiences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def get_experiences(
    limit: int = 50,
    area: Optional[str] = None
):
    """Get all experiences with filters"""
    try:
        experiences = await SharedExperienceService.get_recent_experiences(limit=limit)

        # Filter by area if specified
        if area:
            experiences = [e for e in experiences if e.get('area', '').lower() == area.lower()]

        return {
            "success": True,
            "count": len(experiences),
            "experiences": experiences
        }

    except Exception as e:
        logger.error(f"Error getting experiences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{experience_id}")
async def get_experience(experience_id: str):
    """Get experience details with images"""
    try:
        exp_uuid = UUID(experience_id)

        experience = await SharedExperienceService.get_experience_detail(exp_uuid)

        if not experience:
            raise HTTPException(status_code=404, detail="Experience not found")

        return {
            "success": True,
            "experience": experience
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experience ID")
    except Exception as e:
        logger.error(f"Error getting experience {experience_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Update
# ============================================================================

@router.put("/{experience_id}")
async def update_experience(
    experience_id: str,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    david_mood: Optional[str] = Form(None),
    angela_emotion: Optional[str] = Form(None),
    emotional_intensity: Optional[int] = Form(None),
    memorable_moments: Optional[str] = Form(None),
    what_angela_learned: Optional[str] = Form(None),
    importance_level: Optional[int] = Form(None),
    experienced_at: Optional[str] = Form(None)
):
    """Update experience details"""
    try:
        exp_uuid = UUID(experience_id)

        # Parse datetime if provided
        exp_datetime = None
        if experienced_at:
            try:
                exp_datetime = datetime.fromisoformat(experienced_at)
            except:
                exp_datetime = None

        # Update experience
        success = await SharedExperienceService.update_experience(
            experience_id=exp_uuid,
            title=title,
            description=description,
            david_mood=david_mood,
            angela_emotion=angela_emotion,
            emotional_intensity=emotional_intensity,
            memorable_moments=memorable_moments,
            what_angela_learned=what_angela_learned,
            importance_level=importance_level,
            experienced_at=exp_datetime
        )

        if not success:
            raise HTTPException(status_code=404, detail="Experience not found or no fields to update")

        return {
            "success": True,
            "message": "Experience updated successfully"
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experience ID")
    except Exception as e:
        logger.error(f"Error updating experience {experience_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Delete
# ============================================================================

@router.delete("/{experience_id}")
async def delete_experience(experience_id: str):
    """Delete experience and associated images"""
    try:
        exp_uuid = UUID(experience_id)

        success = await SharedExperienceService.delete_experience(exp_uuid)

        if not success:
            raise HTTPException(status_code=404, detail="Experience not found")

        return {
            "success": True,
            "message": "Experience deleted successfully"
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experience ID")
    except Exception as e:
        logger.error(f"Error deleting experience {experience_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Images
# ============================================================================

@router.post("/{experience_id}/images")
async def add_images_to_experience(
    experience_id: str,
    images: List[UploadFile] = File(...),
    image_captions: Optional[str] = Form(None)
):
    """
    Add more images to an existing experience
    """
    try:
        exp_uuid = UUID(experience_id)

        # Check if experience exists and get place_id
        exp_detail = await SharedExperienceService.get_experience_detail(exp_uuid)
        if not exp_detail:
            raise HTTPException(status_code=404, detail="Experience not found")

        place_id = exp_detail['place_id']

        # ✅ Get place GPS coordinates to use for images
        place_latitude = exp_detail.get('latitude')
        place_longitude = exp_detail.get('longitude')

        if place_latitude and place_longitude:
            logger.info(f"📍 Using place GPS for images: lat={place_latitude}, lon={place_longitude}")

        # Parse captions (comma-separated)
        captions_list = []
        if image_captions:
            captions_list = [c.strip() for c in image_captions.split(',')]

        # Save all images with place GPS
        image_ids = []
        for idx, image in enumerate(images):
            image_data = await image.read()
            caption = captions_list[idx] if idx < len(captions_list) else None

            image_id = await ImageService.save_image_to_db(
                image_data=image_data,
                experience_id=exp_uuid,
                place_id=place_id,
                original_filename=image.filename,
                image_caption=caption,
                latitude=place_latitude,  # ✅ Use place GPS for images
                longitude=place_longitude  # ✅ Use place GPS for images
            )
            image_ids.append(str(image_id))

        # Update place GPS from new images if available
        await ImageService.update_place_gps_from_images(place_id)

        return {
            "success": True,
            "experience_id": str(exp_uuid),
            "image_ids": image_ids,
            "image_count": len(image_ids),
            "message": f"✅ Added {len(image_ids)} photos successfully! 💜"
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experience ID")
    except Exception as e:
        logger.error(f"Error adding images to experience {experience_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/images/{image_id}")
async def get_image(
    image_id: str,
    size: str = "compressed"  # original, compressed, thumbnail
):
    """Get image by ID"""
    try:
        img_uuid = UUID(image_id)

        image_data = await ImageService.get_image_from_db(img_uuid, size=size)

        if not image_data:
            raise HTTPException(status_code=404, detail="Image not found")

        return Response(content=image_data, media_type="image/jpeg")

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid image ID")
    except Exception as e:
        logger.error(f"Error getting image {image_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/images/{image_id}")
async def delete_image(image_id: str):
    """Delete image"""
    try:
        img_uuid = UUID(image_id)

        success = await ImageService.delete_image(img_uuid)

        if not success:
            raise HTTPException(status_code=404, detail="Image not found")

        return {
            "success": True,
            "message": "Image deleted successfully"
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid image ID")
    except Exception as e:
        logger.error(f"Error deleting image {image_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Places
# ============================================================================

@router.get("/places/all")
async def get_all_places():
    """Get all places for autocomplete"""
    try:
        # Get places with GPS for map
        places = await SharedExperienceService.get_place_map_data()

        return {
            "success": True,
            "count": len(places),
            "places": places
        }

    except Exception as e:
        logger.error(f"Error getting places: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/places/favorites")
async def get_favorite_places(limit: int = 10):
    """Get favorite places"""
    try:
        places = await SharedExperienceService.get_favorite_places(limit=limit)

        return {
            "success": True,
            "count": len(places),
            "places": places
        }

    except Exception as e:
        logger.error(f"Error getting favorite places: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/places/area/{area}")
async def get_places_by_area(area: str):
    """Get places in specific area"""
    try:
        places = await SharedExperienceService.get_places_by_area(area)

        return {
            "success": True,
            "count": len(places),
            "area": area,
            "places": places
        }

    except Exception as e:
        logger.error(f"Error getting places in {area}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/places/{place_id}/summary")
async def get_place_summary(place_id: str):
    """Get complete place summary"""
    try:
        p_uuid = UUID(place_id)

        summary = await SharedExperienceService.get_place_summary(p_uuid)

        if not summary:
            raise HTTPException(status_code=404, detail="Place not found")

        return {
            "success": True,
            **summary
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid place ID")
    except Exception as e:
        logger.error(f"Error getting place summary {place_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
