import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.apis import cache


def test_cache_clear_and_stats(tmp_path):
    cwd = os.getcwd()
    os.chdir(tmp_path)
    route = {"distance_miles": 1.0, "duration_seconds": 60, "status": "OK"}
    cache.save_cached_route(
        40.0, -75.0, "A", "09:00", "Mon", route, cache_duration_days=1
    )
    cache.save_cached_route(
        40.0, -75.0, "B", "10:00", "Tue", route, cache_duration_days=-1
    )

    stats = cache.get_cache_stats()
    assert stats["total_files"] == 2
    removed = cache.clear_expired_cache()
    assert removed == 1
    stats = cache.get_cache_stats()
    assert stats["total_files"] == 1
    os.chdir(cwd)
