import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.analyzer import LocationAnalyzer
from src.core.grid_generator import AnalysisGrid
from src.config_parser import ConfigParser
from src.apis.cache import save_cached_route
from src.apis.osrm import OSRMClient
from src.apis.rate_limiter import APIHandler


def load_config():
    parser = ConfigParser()
    config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config'))
    cfg = parser.load_config(config_dir)
    parser.validate_config(cfg)
    return cfg


def test_cached_route_used(tmp_path):
    cfg = load_config()
    analyzer = LocationAnalyzer(cfg)
    analyzer.grid = AnalysisGrid(40.0, -75.0, radius_miles=0.1, grid_size_miles=0.1)
    analyzer.schedules = [{
        'destination': 'Test Dest',
        'lat': 40.1,
        'lon': -75.1,
        'departure_time': '09:00',
        'day': 'Mon',
        'category': 'work',
        'frequency': 'weekly',
        'annual_occurrences': 52
    }]
    point = analyzer.grid.grid_df.iloc[0]
    route = {'distance_miles': 1.0, 'duration_seconds': 100, 'status': 'OK'}
    save_cached_route(point['lat'], point['lon'], 'Test Dest', '09:00', 'Mon', route)
    result = analyzer._calculate_routes()
    assert result['cache_hits'] == 1
    assert result['total_api_calls'] == 0


def test_rate_limiter_delay():
    client = OSRMClient(base_url="http://invalid.local", requests_per_second=2, api_handler=APIHandler(retry_count=1))
    origin = {'lat': 40.0, 'lon': -75.0}
    dest = {'lat': 40.1, 'lon': -75.1}
    start = time.time()
    client.route(origin, dest)
    client.route(origin, dest)
    elapsed = time.time() - start
    assert elapsed >= 0.5
