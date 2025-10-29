#!/usr/bin/env python3
"""
Location Service - Angela's Location Awareness System
ระบบให้ Angela รู้ว่า David อยู่ที่ไหนในโลก

Features:
- Detect location from IP address
- Get city, country, coordinates
- Auto-detect timezone from location
- Track location changes
- Privacy-focused (only when needed)
"""

import httpx
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


class LocationService:
    """Angela's Location Service - Know where David is"""

    def __init__(self):
        """Initialize location service"""
        self._current_location: Optional[Dict[str, Any]] = None
        self._last_update: Optional[datetime] = None
        self._cache_duration = timedelta(hours=1)  # Cache for 1 hour
        logger.info("📍 Location Service initialized")

    async def get_current_location(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get current location based on IP address

        Args:
            force_refresh: Force refresh even if cache is valid

        Returns:
            Dictionary with location information
        """
        # Check cache
        if not force_refresh and self._is_cache_valid():
            logger.debug("📍 Using cached location")
            return self._current_location

        # Fetch new location
        try:
            logger.info("📍 Fetching current location from IP...")

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("https://ipapi.co/json/")

                if response.status_code == 200:
                    data = response.json()

                    # Parse and structure location data
                    location = {
                        # Basic info
                        "ip": data.get("ip"),
                        "version": data.get("version"),

                        # Location
                        "city": data.get("city"),
                        "region": data.get("region"),
                        "region_code": data.get("region_code"),
                        "country": data.get("country_name"),
                        "country_code": data.get("country_code"),
                        "country_code_iso3": data.get("country_code_iso3"),
                        "continent_code": data.get("continent_code"),

                        # Coordinates
                        "latitude": data.get("latitude"),
                        "longitude": data.get("longitude"),

                        # Postal
                        "postal": data.get("postal"),

                        # Time
                        "timezone": data.get("timezone"),
                        "utc_offset": data.get("utc_offset"),

                        # Currency & Language
                        "currency": data.get("currency"),
                        "currency_name": data.get("currency_name"),
                        "languages": data.get("languages"),

                        # ISP
                        "org": data.get("org"),
                        "asn": data.get("asn"),

                        # Metadata
                        "last_updated": datetime.now(),
                        "source": "ipapi.co"
                    }

                    # Update cache
                    self._current_location = location
                    self._last_update = datetime.now()

                    logger.info(f"📍 Location updated: {location['city']}, {location['country']}")
                    return location
                else:
                    logger.error(f"❌ Failed to get location: HTTP {response.status_code}")
                    return self._get_fallback_location()

        except Exception as e:
            logger.error(f"❌ Error getting location: {e}")
            return self._get_fallback_location()

    def _is_cache_valid(self) -> bool:
        """Check if cached location is still valid"""
        if self._current_location is None or self._last_update is None:
            return False

        age = datetime.now() - self._last_update
        return age < self._cache_duration

    def _get_fallback_location(self) -> Dict[str, Any]:
        """Get fallback location if detection fails"""
        if self._current_location:
            # Return cached location if available
            logger.warning("⚠️ Using cached location as fallback")
            return self._current_location

        # Default to Bangkok, Thailand
        logger.warning("⚠️ Using default location (Bangkok, Thailand)")
        return {
            "city": "Bangkok",
            "region": "Bangkok",
            "country": "Thailand",
            "country_code": "TH",
            "latitude": 13.7563,
            "longitude": 100.5018,
            "timezone": "Asia/Bangkok",
            "utc_offset": "+0700",
            "last_updated": datetime.now(),
            "source": "fallback"
        }

    # ========== Convenience Methods ==========

    async def get_city(self) -> str:
        """Get current city name"""
        location = await self.get_current_location()
        return location.get("city", "Unknown")

    async def get_country(self) -> str:
        """Get current country name"""
        location = await self.get_current_location()
        return location.get("country", "Unknown")

    async def get_timezone(self) -> str:
        """Get current timezone"""
        location = await self.get_current_location()
        return location.get("timezone", "Asia/Bangkok")

    async def get_coordinates(self) -> tuple:
        """Get current coordinates (latitude, longitude)"""
        location = await self.get_current_location()
        lat = location.get("latitude", 0.0)
        lon = location.get("longitude", 0.0)
        return (lat, lon)

    async def get_location_string(self, language: str = "th") -> str:
        """
        Get human-readable location string

        Args:
            language: 'th' or 'en'

        Returns:
            Location string like "บางบัวทอง, นนทบุรี, ไทย"
        """
        location = await self.get_current_location()

        city = location.get("city", "")
        region = location.get("region", "")
        country = location.get("country", "")

        if language == "th":
            # For Thai locations, use Thai names
            if country == "Thailand":
                return f"{city}, {region}, ไทย"
            else:
                return f"{city}, {region}, {country}"
        else:
            return f"{city}, {region}, {country}"

    async def get_full_location_info(self) -> Dict[str, Any]:
        """
        Get comprehensive location information with formatted strings

        Returns:
            Dictionary with all location info plus formatted strings
        """
        location = await self.get_current_location()

        # Add formatted strings
        location_str_th = await self.get_location_string("th")
        location_str_en = await self.get_location_string("en")

        return {
            **location,
            "location_string_th": location_str_th,
            "location_string_en": location_str_en,
            "coordinates_string": f"{location.get('latitude', 0)}, {location.get('longitude', 0)}"
        }

    async def has_location_changed(self, threshold_km: float = 10.0) -> bool:
        """
        Check if location has changed significantly

        Args:
            threshold_km: Minimum distance in km to consider as change

        Returns:
            True if location changed significantly
        """
        if self._current_location is None:
            return True

        old_location = self._current_location.copy()
        new_location = await self.get_current_location(force_refresh=True)

        # Calculate distance between old and new coordinates
        old_coords = (old_location.get("latitude", 0), old_location.get("longitude", 0))
        new_coords = (new_location.get("latitude", 0), new_location.get("longitude", 0))

        distance = self._calculate_distance(old_coords, new_coords)

        return distance >= threshold_km

    def _calculate_distance(self, coord1: tuple, coord2: tuple) -> float:
        """
        Calculate distance between two coordinates using Haversine formula

        Args:
            coord1: (lat, lon) tuple
            coord2: (lat, lon) tuple

        Returns:
            Distance in kilometers
        """
        from math import radians, cos, sin, asin, sqrt

        lat1, lon1 = coord1
        lat2, lon2 = coord2

        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))

        # Earth radius in kilometers
        r = 6371

        return c * r


# ========== Global Location Instance ==========

# Create global location instance for easy access
location = LocationService()

logger.info("📍 Location Service module loaded. Global 'location' instance available.")
