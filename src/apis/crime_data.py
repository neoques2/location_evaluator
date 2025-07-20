"""
FBI UCR Crime Data Integration
Handles FBI Crime Data Explorer API calls and crime statistics processing.

Data Sources:
- FBI Crime Data Explorer API: https://api.usa.gov/crime/fbi/cde/
- National Incident-Based Reporting System (NIBRS)
- Uniform Crime Reporting (UCR) Summary Data

Backup Crime Data Sources:
If FBI API is unavailable:
1. Local Police Department APIs (city-specific)
2. SpotCrime API (commercial)
3. CrimeReports.com (web scraping as last resort)
"""

import os
import requests
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from .cache import get_cached_crime_data, save_cached_crime_data


@dataclass
class CrimeStats:
    """Crime statistics for a location."""
    crime_score: float      # 0-1 scale, lower is safer
    incident_count: int     # total incidents in area
    violent_crimes: int     # count of violent crimes
    property_crimes: int    # count of property crimes
    other_crimes: int       # count of other crimes
    safety_grade: str       # A+ to F scale


def get_crime_data(
    lat: float,
    lon: float,
    radius_miles: float = 0.5,
    *,
    weights: Optional[Dict[str, float]] = None,
    density_scale: float = 1000.0,
    score_scale: float = 10.0,
    use_cache: bool = True,
    cache_duration_days: int = 7,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """
    Get crime statistics for area around location.
    
    Args:
        lat: Latitude of location
        lon: Longitude of location
        radius_miles: Radius around location to search (default 0.5 miles)
        weights: Optional weighting for crime types
        density_scale: Population density normalization factor
        score_scale: Divisor for final score scaling
        
    Returns:
        Dictionary containing crime statistics and safety score
    """
    if use_cache and not force_refresh:
        cached = get_cached_crime_data(lat, lon, radius_miles)
        if cached is not None:
            if cached.get('crime_data') is not None and cached.get('crime_data').get('crime_score') != 0.0:
                print(cached.get('crime_data'))
            return cached

    # Convert to bounding box
    bbox = get_bounding_box(lat, lon, radius_miles)
    
    # Query FBI API for recent crime data
    crime_data = fbi_api_get_incidents(
        bbox=bbox,
        start_date='2023-01-01',
        end_date='2024-01-01'
    )
    
    # Calculate crime score
    violent_crimes = count_by_type(crime_data, 'violent')
    property_crimes = count_by_type(crime_data, 'property')
    other_crimes = count_by_type(crime_data, 'other')
    
    # Normalize by population density
    population_density = get_population_density(lat, lon)
    
    safety_score = calculate_safety_score(
        violent_crimes,
        property_crimes,
        other_crimes,
        population_density,
        weights=weights,
        density_scale=density_scale,
        score_scale=score_scale,
    )
    
    result = {
        'crime_score': safety_score,
        'incident_count': len(crime_data),
        'violent_crimes': violent_crimes,
        'property_crimes': property_crimes,
        'other_crimes': other_crimes,
        'safety_grade': score_to_grade(safety_score)
    }

    if use_cache:
        save_cached_crime_data(lat, lon, radius_miles, result,
                               cache_duration_days=cache_duration_days)

    return result


def get_bounding_box(lat: float, lon: float, radius_miles: float) -> Dict[str, float]:
    """
    Convert lat/lon and radius to bounding box coordinates.
    
    Args:
        lat: Center latitude
        lon: Center longitude
        radius_miles: Radius in miles
        
    Returns:
        Dictionary with north, south, east, west bounds
    """
    # Approximate conversion: 1 degree latitude ≈ 69 miles
    # Longitude varies by latitude: 1 degree longitude ≈ 69 * cos(latitude) miles
    
    lat_offset = radius_miles / 69.0
    lon_offset = radius_miles / (69.0 * abs(lat))
    
    return {
        'north': lat + lat_offset,
        'south': lat - lat_offset,
        'east': lon + lon_offset,
        'west': lon - lon_offset
    }


def fbi_api_get_incidents(bbox: Dict[str, float], start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Query FBI Crime Data Explorer API for incidents in bounding box.
    
    Args:
        bbox: Bounding box coordinates
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        List of crime incidents
    """
    base_url = "https://api.usa.gov/crime/fbi/cde"

    params = {
        'bbox': f"{bbox['west']},{bbox['south']},{bbox['east']},{bbox['north']}",
        'start_date': start_date,
        'end_date': end_date,
    }

    api_key = os.getenv('FBI_API_KEY')
    if api_key:
        params['api_key'] = api_key

    url = f"{base_url}/offense/reports"

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return data
        if 'results' in data:
            return data['results']
        if 'incidents' in data:
            return data['incidents']
    except Exception:
        pass

    return []


def count_by_type(crime_data: List[Dict[str, Any]], crime_type: str) -> int:
    """
    Count crimes by type from crime data.
    
    Args:
        crime_data: List of crime incidents
        crime_type: Type to count ('violent', 'property', 'other')
        
    Returns:
        Count of crimes of specified type
    """
    return sum(1 for incident in crime_data if incident.get('crime_type') == crime_type)


def get_population_density(lat: float, lon: float) -> float:
    """
    Get population density for normalization of crime statistics.
    
    Args:
        lat: Latitude
        lon: Longitude
        
    Returns:
        Population density (people per square mile)
    """
    # TODO: Implement population density lookup
    # Could use Census API or other demographic data source
    return 1000.0  # Placeholder


def calculate_safety_score(
    violent_crimes: int,
    property_crimes: int,
        other_crimes: int,
        population_density: float,
        *,
        weights: Optional[Dict[str, float]] = None,
        density_scale: float = 1000.0,
        score_scale: float = 10.0,
    ) -> float:
    """
    Calculate normalized safety score from crime statistics.
    
    Args:
        violent_crimes: Count of violent crimes
        property_crimes: Count of property crimes
        other_crimes: Count of other crimes
        population_density: Population density for normalization
        weights: Optional weighting for crime types
        density_scale: Normalization factor for population density
        score_scale: Divisor for final score scaling
        
    Returns:
        Safety score (0-1 scale, lower is safer)
    """
    # Weight violent crimes more heavily than property crimes
    w = weights or {'violent': 2.0, 'property': 1.0, 'other': 0.5}
    weighted_crimes = (
        violent_crimes * w.get('violent', 2.0)
        + property_crimes * w.get('property', 1.0)
        + other_crimes * w.get('other', 0.5)
    )
    
    # Normalize by population density
    normalized_crimes = weighted_crimes / max(population_density / density_scale, 1)
    
    # Convert to 0-1 scale (this is a simplified approach)
    # In practice, you'd want to calibrate this against regional averages
    safety_score = min(normalized_crimes / score_scale, 1.0)
    
    return safety_score


def score_to_grade(score: float) -> str:
    """
    Convert safety score to letter grade.
    
    Args:
        score: Safety score (0-1 scale, lower is safer)
        
    Returns:
        Letter grade (A+ to F)
    """
    if score <= 0.1:
        return "A+"
    elif score <= 0.2:
        return "A"
    elif score <= 0.3:
        return "A-"
    elif score <= 0.4:
        return "B+"
    elif score <= 0.5:
        return "B"
    elif score <= 0.6:
        return "B-"
    elif score <= 0.7:
        return "C+"
    elif score <= 0.8:
        return "C"
    elif score <= 0.9:
        return "C-"
    else:
        return "F"
