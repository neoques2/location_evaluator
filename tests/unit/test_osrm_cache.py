import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.apis.cache import save_cached_osrm_route, get_cached_osrm_route


def test_osrm_cache_roundtrip(tmp_path):
    cwd = os.getcwd()
    os.chdir(tmp_path)
    route = {"distance_miles": 2.0, "duration_seconds": 120, "status": "OK"}
    save_cached_osrm_route(1.0, 2.0, 3.0, 4.0, route, cache_duration_days=1)
    res = get_cached_osrm_route(1.0, 2.0, 3.0, 4.0)
    assert res == route
    os.chdir(cwd)


def test_osrm_cache_expired(tmp_path):
    cwd = os.getcwd()
    os.chdir(tmp_path)
    route = {"distance_miles": 1.0, "duration_seconds": 60, "status": "OK"}
    save_cached_osrm_route(5.0, 6.0, 7.0, 8.0, route, cache_duration_days=-1)
    res = get_cached_osrm_route(5.0, 6.0, 7.0, 8.0)
    assert res is None
    os.chdir(cwd)
