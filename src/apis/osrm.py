import math
import logging
from typing import Dict, Any, Optional, List

import requests
from .rate_limiter import RateLimiter, APIHandler
from .cache import get_cached_osrm_route, save_cached_osrm_route


class OSRMClient:
    """Simple OSRM API client with offline fallback."""

    def __init__(
        self,
        base_url: str = "http://localhost:5000",
        timeout: int = 30,
        requests_per_second: int = 10,
        api_handler: Optional[APIHandler] = None,
        use_cache: bool = True,
        cache_duration_days: int = 7,
        force_refresh: bool = False,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.rate_limiter = RateLimiter(requests_per_second=requests_per_second)
        self.api_handler = api_handler or APIHandler()
        self.use_cache = use_cache
        self.cache_duration_days = cache_duration_days
        self.force_refresh = force_refresh
        self.logger = logging.getLogger(__name__)

    def route(
        self,
        origin: Dict[str, float],
        destination: Dict[str, float],
        profile: str = "driving",
    ) -> Dict[str, Any]:
        """Calculate route between origin and destination using OSRM.

        Falls back to straight line distance if the request fails.
        """
        if self.use_cache and not self.force_refresh:
            cached = get_cached_osrm_route(
                origin["lat"],
                origin["lon"],
                destination["lat"],
                destination["lon"],
                profile,
            )
            if cached:
                return cached
        url = f"{self.base_url}/route/v1/{profile}/{origin['lon']},{origin['lat']};{destination['lon']},{destination['lat']}?overview=false"
        try:
            self.rate_limiter.wait_if_needed()
            resp = self.api_handler.call_with_retry(
                lambda: requests.get(url, timeout=self.timeout)
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("routes"):
                route = data["routes"][0]
                result = {
                    "distance_miles": route["distance"] * 0.000621371,
                    "duration_seconds": route["duration"],
                    "status": "OK",
                }
                if self.use_cache:
                    save_cached_osrm_route(
                        origin["lat"],
                        origin["lon"],
                        destination["lat"],
                        destination["lon"],
                        result,
                        profile=profile,
                        cache_duration_days=self.cache_duration_days,
                    )
                return result
        except Exception as e:
            self.logger.warning(f"OSRM request failed: {e}; using fallback")

        distance = self._haversine(
            origin["lat"], origin["lon"], destination["lat"], destination["lon"]
        )
        result = {
            "distance_miles": distance,
            "duration_seconds": self._estimate_duration(distance),
            "status": "ESTIMATED",
        }
        if self.use_cache:
            save_cached_osrm_route(
                origin["lat"],
                origin["lon"],
                destination["lat"],
                destination["lon"],
                result,
                profile=profile,
                cache_duration_days=self.cache_duration_days,
            )
        return result

    def route_batch(
        self,
        origins: List[Dict[str, float]],
        destinations: List[Dict[str, float]],
        profile: str = "driving",
    ) -> List[Dict[str, Any]]:
        """Calculate multiple routes using the OSRM /table API."""
        if len(origins) != len(destinations):
            raise ValueError("origins and destinations must have same length")

        import pandas as pd

        df = pd.DataFrame(
            {
                "o_lat": [o["lat"] for o in origins],
                "o_lon": [o["lon"] for o in origins],
                "d_lat": [d["lat"] for d in destinations],
                "d_lon": [d["lon"] for d in destinations],
                "idx": list(range(len(origins))),
            }
        )

        results: List[Optional[Dict[str, Any]]] = [None] * len(df)

        if self.use_cache and not self.force_refresh:
            df["cached"] = df.apply(
                lambda r: get_cached_osrm_route(
                    r.o_lat, r.o_lon, r.d_lat, r.d_lon, profile
                ),
                axis=1,
            )
            for _, row in df.dropna(subset=["cached"]).iterrows():
                results[int(row.idx)] = row.cached
            uncached = df[df["cached"].isna()].reset_index(drop=True)
        else:
            df["cached"] = None
            uncached = df

        if not uncached.empty:
            coord_parts = (
                uncached[["o_lon", "o_lat"]]
                .apply(lambda r: f"{r.o_lon},{r.o_lat}", axis=1)
                .tolist()
                + uncached[["d_lon", "d_lat"]]
                .apply(lambda r: f"{r.d_lon},{r.d_lat}", axis=1)
                .tolist()
            )
            coord_str = ";".join(coord_parts)
            sources = ";".join(str(i) for i in range(len(uncached)))
            dests = ";".join(str(len(uncached) + i) for i in range(len(uncached)))
            url = f"{self.base_url}/table/v1/{profile}/{coord_str}?sources={sources}&destinations={dests}&annotations=distance,duration"

            try:
                self.rate_limiter.wait_if_needed()
                resp = self.api_handler.call_with_retry(
                    lambda: requests.get(url, timeout=self.timeout)
                )
                resp.raise_for_status()
                data = resp.json()
                if "durations" in data and "distances" in data:
                    for i, row in uncached.iterrows():
                        dist = data["distances"][i][i]
                        dur = data["durations"][i][i]
                        result = {
                            "distance_miles": dist * 0.000621371,
                            "duration_seconds": dur,
                            "status": "OK",
                        }
                        idx = int(row.idx)
                        results[idx] = result
                        if self.use_cache:
                            save_cached_osrm_route(
                                row.o_lat,
                                row.o_lon,
                                row.d_lat,
                                row.d_lon,
                                result,
                                profile=profile,
                                cache_duration_days=self.cache_duration_days,
                            )
            except Exception as e:
                self.logger.warning(f"OSRM batch request failed: {e}; using fallback")
                for i, row in uncached.iterrows():
                    distance = self._haversine(
                        row.o_lat, row.o_lon, row.d_lat, row.d_lon
                    )
                    result = {
                        "distance_miles": distance,
                        "duration_seconds": self._estimate_duration(distance),
                        "status": "ESTIMATED",
                    }
                    idx = int(row.idx)
                    results[idx] = result
                    if self.use_cache:
                        save_cached_osrm_route(
                            row.o_lat,
                            row.o_lon,
                            row.d_lat,
                            row.d_lon,
                            result,
                            profile=profile,
                            cache_duration_days=self.cache_duration_days,
                        )

        return results

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))
        return 3959 * c  # miles

    def _estimate_duration(self, distance_miles: float) -> float:
        # simple estimate at 30 mph
        return (distance_miles / 30) * 3600
