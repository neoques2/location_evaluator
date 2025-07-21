import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.apis.osrm import OSRMClient


def test_osrm_fallback():
    client = OSRMClient(base_url="http://invalid.local")
    origin = {"lat": 40.0, "lon": -75.0}
    dest = {"lat": 40.1, "lon": -75.1}
    result = client.route(origin, dest)
    assert result["distance_miles"] > 0
    assert result["duration_seconds"] > 0
    assert result["status"] in {"OK", "ESTIMATED"}


def test_osrm_local_route():
    """Query local OSRM server for a known route."""
    client = OSRMClient(base_url="http://localhost:5000")
    origin = {"lat": 32.7555, "lon": -97.3308}  # Downtown Fort Worth
    dest = {"lat": 32.7767, "lon": -96.7970}  # Downtown Dallas
    result = client.route(origin, dest)
    if result["status"] != "OK":
        pytest.skip("Local OSRM server not available")
    assert 20 * 60 <= result["duration_seconds"] <= 90 * 60
    assert 25 <= result["distance_miles"] <= 40


def test_osrm_batch_fallback():
    client = OSRMClient(base_url="http://invalid.local")
    origins = [
        {"lat": 40.0, "lon": -75.0},
        {"lat": 40.1, "lon": -75.2},
    ]
    dests = [
        {"lat": 40.1, "lon": -75.1},
        {"lat": 40.2, "lon": -75.3},
    ]
    results = client.route_batch(origins, dests)
    assert len(results) == 2
    for res in results:
        assert res["distance_miles"] > 0
        assert res["duration_seconds"] > 0
        assert res["status"] in {"OK", "ESTIMATED"}


def test_osrm_batch_local_route():
    client = OSRMClient(base_url="http://localhost:5000")
    origins = [
        {"lat": 32.7555, "lon": -97.3308},
        {"lat": 32.7555, "lon": -97.3308},
    ]
    dests = [
        {"lat": 32.7767, "lon": -96.7970},
        {"lat": 32.7555, "lon": -97.3308},
    ]
    results = client.route_batch(origins, dests)
    if any(r["status"] != "OK" for r in results):
        pytest.skip("Local OSRM server not available")
    assert len(results) == 2
    assert all(r["duration_seconds"] > 0 for r in results)
