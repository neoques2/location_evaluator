import math
import logging
from typing import Dict, Any, Optional

import requests
from .rate_limiter import RateLimiter, APIHandler

class OSRMClient:
    """Simple OSRM API client with offline fallback."""

    def __init__(self, base_url: str = "http://localhost:5000", timeout: int = 30,
                 requests_per_second: int = 10, api_handler: Optional[APIHandler] = None):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.rate_limiter = RateLimiter(requests_per_second=requests_per_second)
        self.api_handler = api_handler or APIHandler()
        self.logger = logging.getLogger(__name__)

    def route(self, origin: Dict[str, float], destination: Dict[str, float], profile: str = "driving") -> Dict[str, Any]:
        """Calculate route between origin and destination using OSRM.

        Falls back to straight line distance if the request fails.
        """
        url = f"{self.base_url}/route/v1/{profile}/{origin['lon']},{origin['lat']};{destination['lon']},{destination['lat']}?overview=false"
        try:
            self.rate_limiter.wait_if_needed()
            resp = self.api_handler.call_with_retry(lambda: requests.get(url, timeout=self.timeout))
            resp.raise_for_status()
            data = resp.json()
            if data.get('routes'):
                route = data['routes'][0]
                return {
                    'distance_miles': route['distance'] * 0.000621371,
                    'duration_seconds': route['duration'],
                    'status': 'OK'
                }
        except Exception as e:
            self.logger.warning(f"OSRM request failed: {e}; using fallback")

        distance = self._haversine(origin['lat'], origin['lon'], destination['lat'], destination['lon'])
        return {
            'distance_miles': distance,
            'duration_seconds': self._estimate_duration(distance),
            'status': 'ESTIMATED'
        }

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return 3959 * c  # miles

    def _estimate_duration(self, distance_miles: float) -> float:
        # simple estimate at 30 mph
        return (distance_miles / 30) * 3600
