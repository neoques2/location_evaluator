import math
import logging
from typing import Dict, Any, Optional

import requests

class OSRMClient:
    """Simple OSRM API client with offline fallback."""

    def __init__(self, base_url: str = "https://router.project-osrm.org", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

    def route(self, origin: Dict[str, float], destination: Dict[str, float], profile: str = "driving") -> Dict[str, Any]:
        """Calculate route between origin and destination using OSRM.

        Falls back to straight line distance if the request fails.
        """
        url = f"{self.base_url}/route/v1/{profile}/{origin['lon']},{origin['lat']};{destination['lon']},{destination['lat']}?overview=false"
        try:
            resp = requests.get(url, timeout=self.timeout)
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
