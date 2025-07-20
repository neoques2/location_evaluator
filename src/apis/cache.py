"""
Caching System for Route Data
Handles local caching of route calculations to minimize API usage.
"""

import os
import json
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd

OSRM_CACHE_FILE = os.path.join("data", "osrm_cache.csv")


def _load_osrm_cache() -> pd.DataFrame:
    if os.path.exists(OSRM_CACHE_FILE):
        return pd.read_csv(OSRM_CACHE_FILE, parse_dates=["expires"])
    return pd.DataFrame(
        columns=[
            "origin_lat",
            "origin_lon",
            "dest_lat",
            "dest_lon",
            "profile",
            "distance_miles",
            "duration_seconds",
            "status",
            "expires",
        ]
    )


def _save_osrm_cache(df: pd.DataFrame) -> None:
    os.makedirs(os.path.dirname(OSRM_CACHE_FILE) or ".", exist_ok=True)
    df.to_csv(OSRM_CACHE_FILE, index=False)


def get_cached_geocoding(address: str) -> Optional[Dict[str, Any]]:
    """
    Check if geocoding data exists in cache.
    Return cached data if not expired (30 days for geocoding).
    
    Args:
        address: Address to geocode
        
    Returns:
        Cached geocoding data if available and not expired, None otherwise
    """
    cache_key = f"geocoding_{address}"
    cache_file = get_geocoding_cache_file_path(cache_key)
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                if not is_expired(data['cache_info']['expires']):
                    return data['geocoding_data']
        except (json.JSONDecodeError, KeyError):
            # Invalid cache file, remove it
            os.remove(cache_file)
    
    return None


def save_cached_geocoding(address: str, geocoding_data: Dict[str, Any],
                         cache_duration_days: int = 30) -> None:
    """
    Save geocoding data to cache.
    
    Args:
        address: Address that was geocoded
        geocoding_data: Geocoding result to cache
        cache_duration_days: How long to cache data (default 30 days for geocoding)
    """
    cache_key = f"geocoding_{address}"
    cache_file = get_geocoding_cache_file_path(cache_key)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    
    # Prepare cache data
    cache_data = {
        'cache_info': {
            'created': datetime.now().isoformat(),
            'expires': (datetime.now() + timedelta(days=cache_duration_days)).isoformat(),
            'address': address,
            'cache_type': 'geocoding'
        },
        'geocoding_data': geocoding_data
    }
    
    # Save to file
    with open(cache_file, 'w') as f:
        json.dump(cache_data, f, indent=2)


def get_cached_crime_data(lat: float, lon: float, radius_miles: float) -> Optional[Dict[str, Any]]:
    """Retrieve cached crime statistics for a location if available."""
    cache_key = f"crime_{lat:.4f}_{lon:.4f}_{radius_miles:.2f}"
    cache_file = get_crime_cache_file_path(cache_key)

    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                if not is_expired(data['cache_info']['expires']):
                    return data['crime_data']
        except (json.JSONDecodeError, KeyError):
            os.remove(cache_file)

    return None


def save_cached_crime_data(lat: float, lon: float, radius_miles: float,
                           crime_data: Dict[str, Any], cache_duration_days: int = 7) -> None:
    """Save crime statistics to cache."""
    cache_key = f"crime_{lat:.4f}_{lon:.4f}_{radius_miles:.2f}"
    cache_file = get_crime_cache_file_path(cache_key)
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)

    cache_data = {
        'cache_info': {
            'created': datetime.now().isoformat(),
            'expires': (datetime.now() + timedelta(days=cache_duration_days)).isoformat(),
            'grid_point': {'lat': lat, 'lon': lon},
            'radius_miles': radius_miles,
            'cache_type': 'crime'
        },
        'crime_data': crime_data,
    }

    with open(cache_file, 'w') as f:
        json.dump(cache_data, f, indent=2)


def get_crime_cache_file_path(cache_key: str) -> str:
    """Generate file path for cached crime statistics."""
    cache_dir = os.path.join('data', 'crime_cache')
    stable_hash = hashlib.md5(cache_key.encode()).hexdigest()
    return os.path.join(cache_dir, f"{stable_hash}.json")


def get_geocoding_cache_file_path(cache_key: str) -> str:
    """
    Generate cache file path for geocoding data.
    
    Args:
        cache_key: Unique cache key for geocoding
        
    Returns:
        Full path to geocoding cache file
    """
    cache_dir = os.path.join("data", "geocoding_cache")
    # Use stable hash function
    stable_hash = hashlib.md5(cache_key.encode()).hexdigest()
    cache_file = os.path.join(cache_dir, f"{stable_hash}.json")
    return cache_file


def get_cached_route(origin_lat: float, origin_lon: float, destination_address: str, 
                    departure_time: str, day: str) -> Optional[Dict[str, Any]]:
    """
    Check if route data exists in cache.
    Return cached data if not expired (7 days default).
    
    Args:
        origin_lat: Origin latitude
        origin_lon: Origin longitude
        destination_address: Destination address
        departure_time: Departure time string
        day: Day of week
        
    Returns:
        Cached route data if available and not expired, None otherwise
    """
    cache_key = f"{origin_lat:.4f}_{origin_lon:.4f}_{destination_address}_{departure_time}_{day}"
    cache_file = get_cache_file_path(origin_lat, origin_lon, cache_key)
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                if not is_expired(data['cache_info']['expires']):
                    return data['route_data']
        except (json.JSONDecodeError, KeyError):
            # Invalid cache file, remove it
            os.remove(cache_file)
    
    return None


def save_cached_route(origin_lat: float, origin_lon: float, destination_address: str,
                     departure_time: str, day: str, route_data: Dict[str, Any],
                     cache_duration_days: int = 7) -> None:
    """
    Save route data to cache.
    
    Args:
        origin_lat: Origin latitude
        origin_lon: Origin longitude
        destination_address: Destination address
        departure_time: Departure time string
        day: Day of week
        route_data: Route data to cache
        cache_duration_days: How long to cache data (default 7 days)
    """
    cache_key = f"{origin_lat:.4f}_{origin_lon:.4f}_{destination_address}_{departure_time}_{day}"
    cache_file = get_cache_file_path(origin_lat, origin_lon, cache_key)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    
    # Prepare cache data
    cache_data = {
        'cache_info': {
            'created': datetime.now().isoformat(),
            'expires': (datetime.now() + timedelta(days=cache_duration_days)).isoformat(),
            'grid_point': {
                'lat': origin_lat,
                'lon': origin_lon
            },
            'destination': destination_address,
            'departure_time': departure_time,
            'day': day
        },
        'route_data': route_data
    }
    
    # Save to file
    with open(cache_file, 'w') as f:
        json.dump(cache_data, f, indent=2)


def get_cached_osrm_route(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    profile: str = "driving",
) -> Optional[Dict[str, Any]]:
    """Retrieve cached OSRM route by coordinate pair if available."""
    df = _load_osrm_cache()
    if df.empty:
        return None
    mask = (
        (df.origin_lat == origin_lat)
        & (df.origin_lon == origin_lon)
        & (df.dest_lat == dest_lat)
        & (df.dest_lon == dest_lon)
        & (df.profile == profile)
    )
    row = df.loc[mask]
    if not row.empty and row.iloc[0]["expires"] > datetime.now():
        r = row.iloc[0]
        return {
            "distance_miles": float(r.distance_miles),
            "duration_seconds": float(r.duration_seconds),
            "status": r.status,
        }
    return None


def save_cached_osrm_route(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    route_data: Dict[str, Any],
    profile: str = "driving",
    cache_duration_days: int = 7,
) -> None:
    """Save OSRM route to cache."""
    df = _load_osrm_cache()
    expires = datetime.now() + timedelta(days=cache_duration_days)
    mask = (
        (df.origin_lat == origin_lat)
        & (df.origin_lon == origin_lon)
        & (df.dest_lat == dest_lat)
        & (df.dest_lon == dest_lon)
        & (df.profile == profile)
    )
    df = df.loc[~mask]
    new_row = pd.DataFrame(
        [
            {
                "origin_lat": origin_lat,
                "origin_lon": origin_lon,
                "dest_lat": dest_lat,
                "dest_lon": dest_lon,
                "profile": profile,
                "distance_miles": route_data.get("distance_miles", 0.0),
                "duration_seconds": route_data.get("duration_seconds", 0.0),
                "status": route_data.get("status", "OK"),
                "expires": expires,
            }
        ]
    )
    df = pd.concat([df, new_row], ignore_index=True)
    _save_osrm_cache(df)


def get_cache_file_path(lat: float, lon: float, cache_key: str) -> str:
    """
    Generate cache file path based on coordinates.
    
    Cache structure:
    data/grid_cache/
    ├── 40.71/                    # lat truncated to 2 decimals
    │   ├── -74.00/              # lon truncated to 2 decimals
    │   │   ├── route_cache_1.json
    │   │   └── route_cache_2.json
    
    Args:
        lat: Latitude
        lon: Longitude
        cache_key: Unique cache key
        
    Returns:
        Full path to cache file
    """
    lat_dir = f"{lat:.2f}"
    lon_dir = f"{lon:.2f}"
    
    cache_dir = os.path.join("data", "grid_cache", lat_dir, lon_dir)
    # Use stable hash function
    stable_hash = hashlib.md5(cache_key.encode()).hexdigest()
    cache_file = os.path.join(cache_dir, f"{stable_hash}.json")
    
    return cache_file


def is_expired(expires_str: str) -> bool:
    """
    Check if cache entry is expired.
    
    Args:
        expires_str: ISO format expiration datetime string
        
    Returns:
        True if expired, False otherwise
    """
    try:
        expires = datetime.fromisoformat(expires_str)
        return datetime.now() > expires
    except ValueError:
        # Invalid datetime format, consider expired
        return True


def clear_expired_cache() -> int:
    """
    Clear all expired cache entries.
    
    Returns:
        Number of cache files removed
    """
    cache_root = os.path.join("data", "grid_cache")
    if not os.path.exists(cache_root):
        return 0
    
    removed_count = 0
    
    for root, dirs, files in os.walk(cache_root):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        if is_expired(data['cache_info']['expires']):
                            os.remove(file_path)
                            removed_count += 1
                except (json.JSONDecodeError, KeyError, OSError):
                    # Invalid or corrupted file, remove it
                    try:
                        os.remove(file_path)
                        removed_count += 1
                    except OSError:
                        pass
    
    return removed_count


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.
    
    Returns:
        Dictionary with cache statistics
    """
    cache_root = os.path.join("data", "grid_cache")
    if not os.path.exists(cache_root):
        return {
            'total_files': 0,
            'total_size_mb': 0,
            'expired_files': 0,
            'valid_files': 0
        }
    
    total_files = 0
    total_size = 0
    expired_files = 0
    valid_files = 0
    
    for root, dirs, files in os.walk(cache_root):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                try:
                    total_files += 1
                    total_size += os.path.getsize(file_path)
                    
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        if is_expired(data['cache_info']['expires']):
                            expired_files += 1
                        else:
                            valid_files += 1
                except (json.JSONDecodeError, KeyError, OSError):
                    expired_files += 1
    
    return {
        'total_files': total_files,
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'expired_files': expired_files,
        'valid_files': valid_files
    }