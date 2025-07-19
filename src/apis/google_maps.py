"""
Google Maps API Integration
Handles geocoding, distance matrix, and directions API calls with batch processing.
"""

import os
import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .rate_limiter import RateLimiter, APIHandler
from .cache import (
    get_cached_route, save_cached_route, get_cache_stats,
    get_cached_geocoding, save_cached_geocoding
)


@dataclass
class Destination:
    """Represents a destination with address and name."""
    address: str
    name: str


class GoogleMapsClient:
    """Google Maps API client with rate limiting and error handling."""
    
    def __init__(self, api_key: str, rate_limit: int = 10):
        """
        Initialize Google Maps client.
        
        Args:
            api_key: Google Maps API key
            rate_limit: Requests per second limit
        """
        self.api_key = api_key
        self.rate_limiter = RateLimiter(rate_limit)
        self.api_handler = APIHandler()
        self.logger = logging.getLogger(__name__)
        
        # Base URLs for different services
        self.geocoding_url = "https://maps.googleapis.com/maps/api/geocode/json"
        self.distance_matrix_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        
        # API limits for distance matrix
        self.max_origins_per_request = 25
        self.max_destinations_per_request = 25
        self.max_elements_per_request = 100
    
    def geocode_address(self, address: str) -> Optional[Dict[str, float]]:
        """
        Geocode a single address to lat/lon coordinates with caching.
        
        Args:
            address: Address string to geocode
            
        Returns:
            Dictionary with lat/lon coordinates, or None if failed
        """
        # Check cache first
        cached_result = get_cached_geocoding(address)
        if cached_result:
            self.logger.debug(f"Using cached geocoding for: {address}")
            return cached_result
        
        self.logger.debug(f"Geocoding address (not in cache): {address}")
        self.rate_limiter.wait_if_needed()
        
        params = {
            'address': address,
            'key': self.api_key
        }
        
        def make_request():
            response = requests.get(self.geocoding_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        
        try:
            data = self.api_handler.call_with_retry(make_request)
            
            if data['status'] == 'OK' and data['results']:
                location = data['results'][0]['geometry']['location']
                result = {
                    'lat': location['lat'],
                    'lon': location['lng'],
                    'formatted_address': data['results'][0]['formatted_address']
                }
                
                # Save to cache
                save_cached_geocoding(address, result)
                self.logger.debug(f"Cached geocoding result for: {address}")
                
                return result
            else:
                self.logger.warning(f"Geocoding failed for '{address}': {data.get('status', 'Unknown error')}")
                return None
                
        except Exception as e:
            self.logger.error(f"Geocoding error for '{address}': {e}")
            return None
    
    def geocode_batch(self, destinations: List[Destination]) -> List[Dict[str, Any]]:
        """
        Convert all destination addresses to coordinates.
        
        Args:
            destinations: List of destination objects with address and name
            
        Returns:
            List of geocoded destinations with lat/lon coordinates
        """
        geocoded_destinations = []
        
        self.logger.info(f"Geocoding {len(destinations)} destinations...")
        
        for i, dest in enumerate(destinations):
            self.logger.debug(f"Geocoding {i+1}/{len(destinations)}: {dest.address}")
            
            result = self.geocode_address(dest.address)
            
            if result:
                geocoded_dest = {
                    "address": dest.address,
                    "name": dest.name,
                    "lat": result['lat'],
                    "lon": result['lon'],
                    "formatted_address": result['formatted_address']
                }
                self.logger.debug(f"✅ Geocoded: {geocoded_dest['formatted_address']}")
            else:
                # Use a default location near the center for failed geocoding
                self.logger.warning(f"⚠️  Failed to geocode '{dest.address}', using default location")
                geocoded_dest = {
                    "address": dest.address,
                    "name": dest.name,
                    "lat": 40.7128,  # Default to NYC coordinates
                    "lon": -74.0060,
                    "formatted_address": f"{dest.address} (failed geocoding)",
                    "geocoding_failed": True
                }
            
            geocoded_destinations.append(geocoded_dest)
        
        successful_geocodes = len([d for d in geocoded_destinations if not d.get('geocoding_failed', False)])
        self.logger.info(f"Geocoding complete: {successful_geocodes}/{len(destinations)} successful")
        
        return geocoded_destinations
    
    def calculate_distance_matrix(self, origins: List[Dict], destinations: List[Dict], 
                                 mode: str = 'driving', departure_time: Optional[datetime] = None,
                                 traffic_model: str = 'best_guess') -> Dict[str, Any]:
        """
        Calculate distance matrix between origins and destinations with caching.
        
        Args:
            origins: List of origin coordinates [{'lat': float, 'lon': float}, ...]
            destinations: List of destination coordinates [{'lat': float, 'lon': float}, ...]
            mode: Transportation mode (driving, walking, transit, bicycling)
            departure_time: Departure time for traffic-aware routing
            traffic_model: Traffic model (best_guess, pessimistic, optimistic)
            
        Returns:
            Dictionary with distance matrix results
        """
        # Check cache for each origin-destination pair
        cached_routes = {}
        uncached_pairs = []
        
        # Prepare cache lookup parameters
        departure_time_str = departure_time.strftime("%H:%M") if departure_time else "anytime"
        day_str = departure_time.strftime("%a") if departure_time else "any"
        
        for i, origin in enumerate(origins):
            for j, dest in enumerate(destinations):
                # Try to get cached route
                dest_address = f"{dest['lat']:.4f},{dest['lon']:.4f}"
                cached_route = get_cached_route(
                    origin['lat'], origin['lon'], 
                    dest_address, departure_time_str, day_str
                )
                
                if cached_route:
                    cached_routes[(i, j)] = cached_route
                    self.logger.debug(f"Using cached route: ({origin['lat']:.4f},{origin['lon']:.4f}) -> {dest_address}")
                else:
                    uncached_pairs.append((i, j))
        
        # If all routes are cached, return cached results
        if not uncached_pairs:
            self.logger.info(f"All {len(origins)} × {len(destinations)} routes found in cache")
            return self._build_cached_distance_matrix(origins, destinations, cached_routes)
        
        self.logger.info(f"Cache hit: {len(cached_routes)}/{len(origins) * len(destinations)} routes. Need to fetch: {len(uncached_pairs)}")
        
        # Make API call for uncached routes
        self.rate_limiter.wait_if_needed()
        
        # Format origins and destinations for API
        origins_str = '|'.join([f"{o['lat']},{o['lon']}" for o in origins])
        destinations_str = '|'.join([f"{d['lat']},{d['lon']}" for d in destinations])
        
        params = {
            'origins': origins_str,
            'destinations': destinations_str,
            'mode': mode,
            'key': self.api_key,
            'units': 'imperial'  # Use miles
        }
        
        # Add traffic parameters for driving mode
        if mode == 'driving' and departure_time:
            params['departure_time'] = int(departure_time.timestamp())
            params['traffic_model'] = traffic_model
        
        def make_request():
            response = requests.get(self.distance_matrix_url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        
        try:
            data = self.api_handler.call_with_retry(make_request)
            
            if data['status'] == 'OK':
                result = self._process_distance_matrix_response_with_cache(
                    data, origins, destinations, cached_routes, departure_time_str, day_str
                )
                return result
            else:
                self.logger.warning(f"Distance matrix failed: {data.get('status', 'Unknown error')}")
                return self._create_fallback_distance_matrix(origins, destinations)
                
        except Exception as e:
            self.logger.error(f"Distance matrix error: {e}")
            return self._create_fallback_distance_matrix(origins, destinations)
    
    def _process_distance_matrix_response(self, data: Dict, origins: List[Dict], 
                                        destinations: List[Dict]) -> Dict[str, Any]:
        """Process API response into structured format."""
        results = {
            'status': 'OK',
            'origins': origins,
            'destinations': destinations,
            'routes': []
        }
        
        for i, row in enumerate(data['rows']):
            for j, element in enumerate(row['elements']):
                route = {
                    'origin_index': i,
                    'destination_index': j,
                    'origin': origins[i],
                    'destination': destinations[j],
                    'status': element['status']
                }
                
                if element['status'] == 'OK':
                    route.update({
                        'distance_miles': element['distance']['value'] * 0.000621371,  # meters to miles
                        'distance_text': element['distance']['text'],
                        'duration_seconds': element['duration']['value'],
                        'duration_text': element['duration']['text']
                    })
                    
                    # Add traffic duration if available
                    if 'duration_in_traffic' in element:
                        route.update({
                            'duration_in_traffic_seconds': element['duration_in_traffic']['value'],
                            'duration_in_traffic_text': element['duration_in_traffic']['text']
                        })
                else:
                    # Route failed, use fallback estimates
                    route.update(self._estimate_fallback_route(origins[i], destinations[j]))
                
                results['routes'].append(route)
        
        return results
    
    def _build_cached_distance_matrix(self, origins: List[Dict], destinations: List[Dict], 
                                    cached_routes: Dict) -> Dict[str, Any]:
        """Build distance matrix result from cached routes."""
        results = {
            'status': 'OK',
            'origins': origins,
            'destinations': destinations,
            'routes': []
        }
        
        for i, origin in enumerate(origins):
            for j, destination in enumerate(destinations):
                cached_data = cached_routes.get((i, j), {})
                route = {
                    'origin_index': i,
                    'destination_index': j,
                    'origin': origin,
                    'destination': destination,
                    'status': 'OK'
                }
                route.update(cached_data)
                results['routes'].append(route)
        
        return results
    
    def _process_distance_matrix_response_with_cache(self, data: Dict, origins: List[Dict], 
                                                   destinations: List[Dict], cached_routes: Dict,
                                                   departure_time_str: str, day_str: str) -> Dict[str, Any]:
        """Process API response and save new routes to cache."""
        results = {
            'status': 'OK',
            'origins': origins,
            'destinations': destinations,
            'routes': []
        }
        
        for i, row in enumerate(data['rows']):
            for j, element in enumerate(row['elements']):
                # Check if we have cached data for this route
                if (i, j) in cached_routes:
                    route = {
                        'origin_index': i,
                        'destination_index': j,
                        'origin': origins[i],
                        'destination': destinations[j],
                        'status': 'OK'
                    }
                    route.update(cached_routes[(i, j)])
                else:
                    # Process new API data
                    route = {
                        'origin_index': i,
                        'destination_index': j,
                        'origin': origins[i],
                        'destination': destinations[j],
                        'status': element['status']
                    }
                    
                    if element['status'] == 'OK':
                        route_data = {
                            'distance_miles': element['distance']['value'] * 0.000621371,  # meters to miles
                            'distance_text': element['distance']['text'],
                            'duration_seconds': element['duration']['value'],
                            'duration_text': element['duration']['text']
                        }
                        
                        # Add traffic duration if available
                        if 'duration_in_traffic' in element:
                            route_data.update({
                                'duration_in_traffic_seconds': element['duration_in_traffic']['value'],
                                'duration_in_traffic_text': element['duration_in_traffic']['text']
                            })
                        
                        route.update(route_data)
                        
                        # Save to cache
                        dest_address = f"{destinations[j]['lat']:.4f},{destinations[j]['lon']:.4f}"
                        save_cached_route(
                            origins[i]['lat'], origins[i]['lon'],
                            dest_address, departure_time_str, day_str,
                            route_data
                        )
                        self.logger.debug(f"Cached new route: ({origins[i]['lat']:.4f},{origins[i]['lon']:.4f}) -> {dest_address}")
                    else:
                        # Route failed, use fallback estimates
                        route.update(self._estimate_fallback_route(origins[i], destinations[j]))
                
                results['routes'].append(route)
        
        return results
    
    def _create_fallback_distance_matrix(self, origins: List[Dict], destinations: List[Dict]) -> Dict[str, Any]:
        """Create fallback distance matrix when API fails."""
        results = {
            'status': 'FALLBACK',
            'origins': origins,
            'destinations': destinations,
            'routes': []
        }
        
        for i, origin in enumerate(origins):
            for j, destination in enumerate(destinations):
                route = {
                    'origin_index': i,
                    'destination_index': j,
                    'origin': origin,
                    'destination': destination,
                    'status': 'ESTIMATED'
                }
                route.update(self._estimate_fallback_route(origin, destination))
                results['routes'].append(route)
        
        return results
    
    def _estimate_fallback_route(self, origin: Dict, destination: Dict) -> Dict[str, Any]:
        """Estimate route using straight-line distance."""
        import math
        
        # Haversine distance calculation
        lat1, lon1 = math.radians(origin['lat']), math.radians(origin['lon'])
        lat2, lon2 = math.radians(destination['lat']), math.radians(destination['lon'])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        straight_line_miles = 3959 * c  # Earth radius in miles
        
        # Estimate driving distance as 1.3x straight line (typical urban factor)
        estimated_distance = straight_line_miles * 1.3
        
        # Estimate time assuming 25 mph average speed in urban areas
        estimated_duration_hours = estimated_distance / 25
        estimated_duration_seconds = estimated_duration_hours * 3600
        
        return {
            'distance_miles': estimated_distance,
            'distance_text': f"{estimated_distance:.1f} mi (estimated)",
            'duration_seconds': estimated_duration_seconds,
            'duration_text': f"{int(estimated_duration_seconds // 60)} min (estimated)"
        }
    
    def batch_distance_calculations(self, grid_df, destinations: List[Dict], 
                                  mode: str = 'driving', departure_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Calculate distances from all grid points to destinations in efficient batches.
        
        Args:
            grid_df: Pandas DataFrame with grid points (must have 'lat', 'lon' columns)
            destinations: List of destination coordinates
            mode: Transportation mode
            departure_time: Departure time for traffic-aware routing
            
        Returns:
            Dictionary with all route calculations
        """
        import pandas as pd
        
        total_points = len(grid_df)
        total_destinations = len(destinations)
        
        self.logger.info(f"Calculating routes: {total_points:,} origins × {total_destinations} destinations = {total_points * total_destinations:,} routes")
        
        # Convert grid points to origins format
        origins = [{'lat': row['lat'], 'lon': row['lon'], 'point_id': row['point_id']} 
                  for _, row in grid_df.iterrows()]
        
        all_results = []
        
        # Batch processing to respect API limits
        batch_size = min(self.max_origins_per_request, 
                        self.max_elements_per_request // len(destinations))
        
        for i in range(0, len(origins), batch_size):
            batch_origins = origins[i:i + batch_size]
            
            self.logger.debug(f"Processing batch {i//batch_size + 1}: {len(batch_origins)} origins")
            
            # Calculate distance matrix for this batch
            result = self.calculate_distance_matrix(
                origins=batch_origins,
                destinations=destinations,
                mode=mode,
                departure_time=departure_time
            )
            
            all_results.append(result)
        
        # Combine all results
        combined_results = {
            'total_origins': total_points,
            'total_destinations': total_destinations,
            'total_routes': total_points * total_destinations,
            'batches': all_results,
            'mode': mode,
            'departure_time': departure_time.isoformat() if departure_time else None
        }
        
        self.logger.info(f"Batch calculations complete: {len(all_results)} batches")
        
        return combined_results


# Convenience functions for backward compatibility
def geocode_batch(destinations: List[Destination], api_key: str = None) -> List[Dict[str, Any]]:
    """
    Convenience function for batch geocoding.
    
    Args:
        destinations: List of destination objects
        api_key: Google Maps API key (if None, tries to get from environment)
        
    Returns:
        List of geocoded destinations
    """
    if api_key is None:
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not api_key:
            raise ValueError("Google Maps API key not provided and not found in environment")
    
    client = GoogleMapsClient(api_key)
    return client.geocode_batch(destinations)


def batch_distance_calculations(grid_points: List[Dict], destinations: List[Dict], schedules: List[Dict]) -> Dict[str, Any]:
    """
    Process grid points in batches of 25.
    For each batch, calculate distances to all destinations.
    
    Google Maps Distance Matrix API limits:
    - 25 origins OR 25 destinations per request
    - 100 elements per request (origins × destinations)
    - 100 requests per second
    
    Args:
        grid_points: List of grid points with lat/lon coordinates
        destinations: List of destination coordinates
        schedules: List of schedule items with departure times
        
    Returns:
        Dictionary containing calculated routes and distances
    """
    batch_size = 25
    results = {}
    
    for i in range(0, len(grid_points), batch_size):
        batch = grid_points[i:i + batch_size]
        
        # Calculate distances for all departure times
        for schedule_item in schedules:
            departure_time = schedule_item['departure_time']
            day_of_week = schedule_item['day']
            
            # Get traffic-aware travel times
            driving_results = distance_matrix_api_call(
                origins=batch,
                destinations=destinations,
                departure_time=get_next_datetime(departure_time, day_of_week),
                traffic_model='best_guess',
                mode='driving'
            )
            
            # Also get transit options if available
            transit_results = distance_matrix_api_call(
                origins=batch,
                destinations=destinations,
                departure_time=get_next_datetime(departure_time, day_of_week),
                mode='transit'
            )
            
            # Store results
            batch_key = f"batch_{i//batch_size}_{schedule_item['departure_time']}_{day_of_week}"
            results[batch_key] = {
                'driving': driving_results,
                'transit': transit_results
            }
    
    return results


def distance_matrix_api_call(origins: List[Dict], destinations: List[Dict], 
                           departure_time: datetime, traffic_model: str = 'best_guess', 
                           mode: str = 'driving') -> Dict[str, Any]:
    """
    Make actual Distance Matrix API call.
    
    Args:
        origins: List of origin coordinates
        destinations: List of destination coordinates
        departure_time: When to depart
        traffic_model: Traffic model to use
        mode: Transportation mode
        
    Returns:
        API response with distances and durations
    """
    # TODO: Implement actual Google Maps Distance Matrix API call
    # This is a placeholder structure
    return {
        'status': 'OK',
        'rows': [],
        'origin_addresses': [],
        'destination_addresses': []
    }


def get_next_datetime(time_str: str, day_of_week: str) -> datetime:
    """
    Convert time string and day to next occurrence datetime.
    
    Args:
        time_str: Time in HH:MM format
        day_of_week: Day of week (Mon, Tue, etc.)
        
    Returns:
        Next datetime occurrence
    """
    # TODO: Implement conversion logic
    # Parse time_str, find next occurrence of day_of_week
    # Return datetime object for API call
    return datetime.now()


def process_schedules(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert YAML schedule patterns into specific departure times.
    
    Args:
        config: Configuration dictionary with destinations and schedules
        
    Returns:
        List of schedule items with departure times and frequencies
    """
    schedules = []
    
    for dest_category in config['destinations']:
        for destination in config['destinations'][dest_category]:
            for schedule_item in destination['schedule']:
                if 'days' in schedule_item:
                    # Weekly patterns
                    days = parse_days(schedule_item['days'])  # "Mon-Fri" -> ["Mon", "Tue", ...]
                    for day in days:
                        schedules.append({
                            'destination': destination['address'],
                            'departure_time': schedule_item['arrival_time'],
                            'day': day,
                            'frequency': 'weekly'
                        })
                        
                elif 'pattern' in schedule_item:
                    # Monthly patterns
                    schedules.append({
                        'destination': destination['address'],
                        'departure_time': schedule_item['arrival_time'],
                        'pattern': schedule_item['pattern'],  # "first_monday"
                        'frequency': 'monthly'
                    })
    
    return schedules


def parse_days(days_str: str) -> List[str]:
    """
    Parse day string patterns into list of individual days.
    
    Args:
        days_str: String like "Mon-Fri", "Mon,Wed,Fri", etc.
        
    Returns:
        List of individual day strings
    """
    if '-' in days_str:
        # Range pattern like "Mon-Fri"
        start, end = days_str.split('-')
        day_map = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        start_idx = day_map.index(start)
        end_idx = day_map.index(end)
        return day_map[start_idx:end_idx + 1]
    elif ',' in days_str:
        # Comma-separated like "Mon,Wed,Fri"
        return [day.strip() for day in days_str.split(',')]
    else:
        # Single day
        return [days_str]