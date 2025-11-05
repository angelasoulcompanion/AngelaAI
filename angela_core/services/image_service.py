"""
Image Service for Angela AI
Handles image compression, storage, and retrieval for shared experiences

Created: 2025-11-04
Purpose: Allow David to share images with Angela from places they visit together
"""

import base64
import logging
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import io
from uuid import UUID, uuid4

from angela_core.database import db

logger = logging.getLogger(__name__)


class ImageService:
    """Service for handling images in shared experiences"""

    # Image size limits
    MAX_ORIGINAL_SIZE_MB = 10  # Max 10MB for original
    THUMBNAIL_SIZE = (200, 200)  # Small thumbnail for lists
    COMPRESSED_SIZE = (800, 800)  # Medium size for chat display
    JPEG_QUALITY = 85  # Good balance between quality and size

    @staticmethod
    async def compress_image(
        image_data: bytes,
        max_size: Tuple[int, int],
        quality: int = JPEG_QUALITY
    ) -> bytes:
        """Compress image to specified max dimensions"""
        try:
            # Load image
            img = Image.open(io.BytesIO(image_data))

            # Convert RGBA to RGB if needed
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background

            # Calculate new size maintaining aspect ratio
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Save to bytes
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)

            compressed_bytes = output.read()
            logger.info(f"Compressed image: {len(image_data)} → {len(compressed_bytes)} bytes "
                       f"({len(compressed_bytes)/len(image_data)*100:.1f}%)")

            return compressed_bytes

        except Exception as e:
            logger.error(f"Error compressing image: {e}")
            raise

    @staticmethod
    def _convert_to_degrees(value: tuple) -> float:
        """Convert GPS coordinates to decimal degrees"""
        d = float(value[0][0]) / float(value[0][1])
        m = float(value[1][0]) / float(value[1][1])
        s = float(value[2][0]) / float(value[2][1])
        return d + (m / 60.0) + (s / 3600.0)

    @staticmethod
    def _extract_gps_data(img: Image) -> Optional[Dict]:
        """Extract GPS data from image EXIF"""
        try:
            exif = img._getexif()
            if not exif:
                return None

            gps_info = {}
            for tag, value in exif.items():
                tag_name = TAGS.get(tag, tag)
                if tag_name == 'GPSInfo':
                    for gps_tag in value:
                        sub_tag_name = GPSTAGS.get(gps_tag, gps_tag)
                        gps_info[sub_tag_name] = value[gps_tag]

            if not gps_info:
                return None

            # Extract latitude
            lat = None
            if 'GPSLatitude' in gps_info and 'GPSLatitudeRef' in gps_info:
                lat = ImageService._convert_to_degrees(gps_info['GPSLatitude'])
                if gps_info['GPSLatitudeRef'] == 'S':
                    lat = -lat

            # Extract longitude
            lon = None
            if 'GPSLongitude' in gps_info and 'GPSLongitudeRef' in gps_info:
                lon = ImageService._convert_to_degrees(gps_info['GPSLongitude'])
                if gps_info['GPSLongitudeRef'] == 'W':
                    lon = -lon

            # Extract altitude (optional)
            altitude = None
            if 'GPSAltitude' in gps_info:
                altitude = float(gps_info['GPSAltitude'][0]) / float(gps_info['GPSAltitude'][1])
                if gps_info.get('GPSAltitudeRef', 0) == 1:
                    altitude = -altitude

            # Extract GPS timestamp (optional)
            gps_timestamp = None
            if 'GPSTimeStamp' in gps_info and 'GPSDateStamp' in gps_info:
                try:
                    time_parts = gps_info['GPSTimeStamp']
                    date_str = gps_info['GPSDateStamp']
                    time_str = f"{int(time_parts[0][0]/time_parts[0][1]):02d}:" \
                              f"{int(time_parts[1][0]/time_parts[1][1]):02d}:" \
                              f"{int(time_parts[2][0]/time_parts[2][1]):02d}"
                    gps_timestamp = datetime.strptime(f"{date_str} {time_str}", "%Y:%m:%d %H:%M:%S")
                except:
                    pass

            if lat is not None and lon is not None:
                result = {
                    'latitude': lat,
                    'longitude': lon,
                    'altitude': altitude,
                    'timestamp': gps_timestamp
                }
                logger.info(f"Extracted GPS: {lat:.6f}, {lon:.6f}")
                return result

            return None

        except Exception as e:
            logger.debug(f"No GPS data in image: {e}")
            return None

    @staticmethod
    def _extract_exif_datetime(img: Image) -> Optional[datetime]:
        """Extract datetime from EXIF data"""
        try:
            exif = img._getexif()
            if not exif:
                return None

            # Try different datetime tags
            for tag, value in exif.items():
                tag_name = TAGS.get(tag, tag)
                if tag_name in ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized']:
                    try:
                        return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                    except:
                        pass

            return None

        except Exception as e:
            logger.debug(f"No datetime in EXIF: {e}")
            return None

    @staticmethod
    async def get_image_info(image_data: bytes) -> Dict:
        """Get image metadata including EXIF data (GPS, datetime)"""
        try:
            img = Image.open(io.BytesIO(image_data))

            # Basic info
            info = {
                'width': img.width,
                'height': img.height,
                'format': img.format or 'JPEG',
                'mode': img.mode,
                'size_bytes': len(image_data)
            }

            # Extract GPS data
            gps_data = ImageService._extract_gps_data(img)
            if gps_data:
                info['gps'] = gps_data

            # Extract datetime
            taken_at = ImageService._extract_exif_datetime(img)
            if taken_at:
                info['taken_at'] = taken_at

            return info

        except Exception as e:
            logger.error(f"Error reading image info: {e}")
            raise

    @staticmethod
    async def save_image_to_db(
        image_data: bytes,
        experience_id: UUID,
        place_id: UUID,
        original_filename: Optional[str] = None,
        image_caption: Optional[str] = None,
        taken_at: Optional[datetime] = None
    ) -> UUID:
        """Save image to database with compression"""
        try:
            # Get image info
            info = await ImageService.get_image_info(image_data)

            # Create compressed versions
            thumbnail_data = await ImageService.compress_image(
                image_data,
                ImageService.THUMBNAIL_SIZE,
                quality=80
            )
            compressed_data = await ImageService.compress_image(
                image_data,
                ImageService.COMPRESSED_SIZE,
                quality=ImageService.JPEG_QUALITY
            )

            # Generate image ID
            image_id = uuid4()

            # Extract GPS and datetime from EXIF
            gps_data = info.get('gps')
            exif_datetime = info.get('taken_at')

            # Use EXIF datetime if not provided
            if taken_at is None and exif_datetime:
                taken_at = exif_datetime

            # Insert to database
            await db.execute("""
                INSERT INTO shared_experience_images (
                    image_id,
                    experience_id,
                    place_id,
                    image_data,
                    image_format,
                    original_filename,
                    file_size_bytes,
                    width_px,
                    height_px,
                    gps_latitude,
                    gps_longitude,
                    gps_altitude,
                    gps_timestamp,
                    thumbnail_data,
                    compressed_data,
                    image_caption,
                    taken_at,
                    uploaded_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, NOW())
            """, image_id, experience_id, place_id,
                image_data, info['format'], original_filename,
                info['size_bytes'], info['width'], info['height'],
                gps_data['latitude'] if gps_data else None,
                gps_data['longitude'] if gps_data else None,
                gps_data['altitude'] if gps_data else None,
                gps_data['timestamp'] if gps_data else None,
                thumbnail_data, compressed_data,
                image_caption, taken_at
            )

            logger.info(f"Saved image {image_id} for experience {experience_id}")
            logger.info(f"  Original: {info['size_bytes']:,} bytes ({info['width']}x{info['height']})")
            logger.info(f"  Thumbnail: {len(thumbnail_data):,} bytes")
            logger.info(f"  Compressed: {len(compressed_data):,} bytes")

            if gps_data:
                logger.info(f"  GPS: {gps_data['latitude']:.6f}, {gps_data['longitude']:.6f}")
                if gps_data['altitude']:
                    logger.info(f"  Altitude: {gps_data['altitude']:.1f}m")

            if taken_at:
                logger.info(f"  Taken at: {taken_at}")

            return image_id

        except Exception as e:
            logger.error(f"Error saving image to database: {e}")
            raise

    @staticmethod
    async def get_image_from_db(image_id: UUID, size: str = 'compressed') -> Optional[bytes]:
        """Retrieve image from database"""
        try:
            column_map = {
                'original': 'image_data',
                'compressed': 'compressed_data',
                'thumbnail': 'thumbnail_data'
            }

            column = column_map.get(size, 'compressed_data')

            row = await db.fetchrow(f"""
                SELECT {column}, image_format
                FROM shared_experience_images
                WHERE image_id = $1
            """, image_id)

            if row:
                return bytes(row[column])
            return None

        except Exception as e:
            logger.error(f"Error retrieving image {image_id}: {e}")
            return None

    @staticmethod
    async def get_images_for_experience(experience_id: UUID) -> List[Dict]:
        """Get all images for an experience"""
        try:
            rows = await db.fetch("""
                SELECT
                    image_id,
                    original_filename,
                    file_size_bytes,
                    width_px,
                    height_px,
                    image_caption,
                    angela_observation,
                    taken_at,
                    uploaded_at
                FROM shared_experience_images
                WHERE experience_id = $1
                ORDER BY taken_at DESC NULLS LAST, uploaded_at DESC
            """, experience_id)

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error getting images for experience {experience_id}: {e}")
            return []

    @staticmethod
    async def get_images_for_place(place_id: UUID, limit: int = 50) -> List[Dict]:
        """Get all images for a place"""
        try:
            rows = await db.fetch("""
                SELECT
                    i.image_id,
                    i.experience_id,
                    i.original_filename,
                    i.file_size_bytes,
                    i.width_px,
                    i.height_px,
                    i.image_caption,
                    i.angela_observation,
                    i.taken_at,
                    i.uploaded_at,
                    e.title as experience_title,
                    e.experienced_at
                FROM shared_experience_images i
                LEFT JOIN shared_experiences e ON i.experience_id = e.experience_id
                WHERE i.place_id = $1
                ORDER BY i.taken_at DESC NULLS LAST, i.uploaded_at DESC
                LIMIT $2
            """, place_id, limit)

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error getting images for place {place_id}: {e}")
            return []

    @staticmethod
    async def add_angela_observation(image_id: UUID, observation: str) -> bool:
        """Add Angela's observation/reaction to an image"""
        try:
            await db.execute("""
                UPDATE shared_experience_images
                SET angela_observation = $1
                WHERE image_id = $2
            """, observation, image_id)

            logger.info(f"Added Angela's observation to image {image_id}")
            return True

        except Exception as e:
            logger.error(f"Error adding observation to image {image_id}: {e}")
            return False

    @staticmethod
    async def search_images_by_caption(search_term: str, limit: int = 20) -> List[Dict]:
        """Search images by caption or Angela's observation"""
        try:
            rows = await db.fetch("""
                SELECT
                    i.image_id,
                    i.experience_id,
                    i.image_caption,
                    i.angela_observation,
                    i.taken_at,
                    i.uploaded_at,
                    e.title as experience_title,
                    e.experienced_at,
                    p.place_name,
                    p.area
                FROM shared_experience_images i
                LEFT JOIN shared_experiences e ON i.experience_id = e.experience_id
                LEFT JOIN places_visited p ON i.place_id = p.place_id
                WHERE
                    i.image_caption ILIKE $1 OR
                    i.angela_observation ILIKE $1 OR
                    e.title ILIKE $1 OR
                    p.place_name ILIKE $1
                ORDER BY i.taken_at DESC NULLS LAST, i.uploaded_at DESC
                LIMIT $2
            """, f'%{search_term}%', limit)

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error searching images: {e}")
            return []

    @staticmethod
    def image_to_base64(image_data: bytes) -> str:
        """Convert image bytes to base64 string"""
        return base64.b64encode(image_data).decode('utf-8')

    @staticmethod
    def base64_to_image(base64_str: str) -> bytes:
        """Convert base64 string to image bytes"""
        return base64.b64decode(base64_str)

    @staticmethod
    async def update_place_gps_from_images(place_id: UUID) -> bool:
        """Update place GPS coordinates based on images"""
        try:
            # Get all images with GPS data for this place
            rows = await db.fetch("""
                SELECT gps_latitude, gps_longitude, gps_altitude
                FROM shared_experience_images
                WHERE place_id = $1
                AND gps_latitude IS NOT NULL
                AND gps_longitude IS NOT NULL
            """, place_id)

            if not rows:
                logger.info(f"No GPS data found in images for place {place_id}")
                return False

            # Calculate average coordinates
            avg_lat = sum(row['gps_latitude'] for row in rows) / len(rows)
            avg_lon = sum(row['gps_longitude'] for row in rows) / len(rows)

            # Calculate average altitude if available
            altitudes = [row['gps_altitude'] for row in rows if row['gps_altitude']]
            avg_alt = sum(altitudes) / len(altitudes) if altitudes else None

            # Generate Google Maps URL
            google_maps_url = f"https://www.google.com/maps/search/?api=1&query={avg_lat},{avg_lon}"

            # Update place
            await db.execute("""
                UPDATE places_visited
                SET
                    latitude = $1,
                    longitude = $2,
                    location_accuracy = 'high',
                    google_maps_url = $3,
                    updated_at = NOW()
                WHERE place_id = $4
            """, avg_lat, avg_lon, google_maps_url, place_id)

            logger.info(f"Updated place {place_id} GPS: {avg_lat:.6f}, {avg_lon:.6f} (from {len(rows)} images)")
            return True

        except Exception as e:
            logger.error(f"Error updating place GPS: {e}")
            return False

    @staticmethod
    async def find_nearby_places(
        latitude: float,
        longitude: float,
        radius_km: float = 1.0,
        limit: int = 10
    ) -> List[Dict]:
        """Find places within radius using Haversine formula"""
        try:
            rows = await db.fetch("""
                SELECT * FROM (
                    SELECT
                        place_id,
                        place_name,
                        place_type,
                        area,
                        latitude,
                        longitude,
                        google_maps_url,
                        visit_count,
                        overall_rating,
                        (
                            6371 * acos(
                                cos(radians($1)) *
                                cos(radians(latitude)) *
                                cos(radians(longitude) - radians($2)) +
                                sin(radians($1)) *
                                sin(radians(latitude))
                            )
                        ) as distance_km
                    FROM places_visited
                    WHERE latitude IS NOT NULL
                    AND longitude IS NOT NULL
                ) AS places_with_distance
                WHERE distance_km <= $3
                ORDER BY distance_km ASC
                LIMIT $4
            """, latitude, longitude, radius_km, limit)

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error finding nearby places: {e}")
            return []

    @staticmethod
    def format_gps_for_display(latitude: float, longitude: float) -> str:
        """Format GPS coordinates for human-readable display"""
        def decimal_to_dms(decimal: float, is_latitude: bool) -> str:
            is_positive = decimal >= 0
            decimal = abs(decimal)

            degrees = int(decimal)
            minutes_decimal = (decimal - degrees) * 60
            minutes = int(minutes_decimal)
            seconds = (minutes_decimal - minutes) * 60

            # Direction
            if is_latitude:
                direction = 'N' if is_positive else 'S'
            else:
                direction = 'E' if is_positive else 'W'

            return f"{degrees}°{minutes}'{seconds:.1f}\"{direction}"

        lat_str = decimal_to_dms(latitude, True)
        lon_str = decimal_to_dms(longitude, False)

        return f"{lat_str} {lon_str}"

    @staticmethod
    async def delete_image(image_id: UUID) -> bool:
        """
        Delete an image from database

        Args:
            image_id: Image UUID

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Check if image exists
            exists = await db.fetchrow("""
                SELECT image_id FROM shared_experience_images
                WHERE image_id = $1
            """, image_id)

            if not exists:
                logger.warning(f"Image {image_id} not found")
                return False

            # Delete image
            await db.execute("""
                DELETE FROM shared_experience_images
                WHERE image_id = $1
            """, image_id)

            logger.info(f"Deleted image {image_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting image {image_id}: {e}")
            return False
