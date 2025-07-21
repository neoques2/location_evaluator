"""Simple geocoding helpers using geopy."""

from typing import Optional, Dict, Any
import logging

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError

from .cache import get_cached_geocoding, save_cached_geocoding


def geocode_address(
    address: str,
    *,
    timeout: int = 10,
    use_cache: bool = True,
    cache_duration_days: int = 30,
    force_refresh: bool = False,
) -> Optional[Dict[str, Any]]:
    """Geocode an address string to latitude/longitude.

    Args:
        address: Address to geocode
        timeout: Request timeout in seconds
        use_cache: Whether to check and save local cache
        cache_duration_days: How long to keep cache entries
        force_refresh: Ignore cached value and fetch fresh

    Returns:
        Dictionary with ``lat`` and ``lon`` if successful, else ``None``.
    """
    logger = logging.getLogger(__name__)
    if use_cache and not force_refresh:
        cached = get_cached_geocoding(address)
        if cached is not None:
            return cached

    geocoder = Nominatim(user_agent="location_evaluator")
    try:
        loc = geocoder.geocode(address, timeout=timeout)
        if loc:
            result = {"lat": loc.latitude, "lon": loc.longitude}
            if use_cache:
                save_cached_geocoding(
                    address, result, cache_duration_days=cache_duration_days
                )
            return result
    except GeocoderServiceError as e:
        logger.warning(f"Geocoding failed for '{address}': {e}")
    except Exception as e:
        logger.warning(f"Unexpected geocoding error for '{address}': {e}")
    return None
