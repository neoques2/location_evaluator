import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.analyzer import LocationAnalyzer


def test_analyze_locations_with_duplicate_destinations():
    cfg = {
        'analysis': {
            'grid_size': 0.1,
            'max_radius': 0.1,
            'center_point': [0.0, 0.0],
        },
        'destinations': {},
        'transportation': {},
        'weights': {},
        'output': {},
    }

    analyzer = LocationAnalyzer(cfg)
    analyzer._setup_analysis_grid()

    analyzer.schedules = [
        {
            'destination': '123 Main St',
            'destination_name': 'A',
            'category': 'cat1',
            'departure_time': '09:00',
            'day': 'Mon',
            'frequency': 'weekly',
            'annual_occurrences': 52,
        },
        {
            'destination': '123 Main St',
            'destination_name': 'A2',
            'category': 'cat2',
            'departure_time': '10:00',
            'day': 'Tue',
            'frequency': 'weekly',
            'annual_occurrences': 52,
        },
    ]

    route_data = {
        'routes': {
            0: {
                '123 Main St': {
                    'status': 'OK',
                    'duration_seconds': 600,
                    'distance_miles': 1.0,
                }
            }
        }
    }

    results = analyzer._analyze_locations(route_data)
    assert results[0].travel_analysis.destinations

