import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.apis.osrm import OSRMClient


def test_osrm_fallback():
    client = OSRMClient(base_url="http://invalid.local")
    origin = {'lat': 40.0, 'lon': -75.0}
    dest = {'lat': 40.1, 'lon': -75.1}
    result = client.route(origin, dest)
    assert result['distance_miles'] > 0
    assert result['duration_seconds'] > 0
    assert result['status'] in {'OK', 'ESTIMATED'}
