import os
import json
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pytest

from src.apis import crime_data
from src.apis import cache as cache_utils
from src.analyzer import LocationAnalyzer

class DummyResp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_get_crime_data_makes_request(monkeypatch):
    called = {}

    def fake_get(url, params=None, timeout=10):
        called['url'] = url
        called['params'] = params
        return DummyResp({'incidents': [
            {'crime_type': 'violent'},
            {'crime_type': 'property'},
            {'crime_type': 'other'},
        ]})

    monkeypatch.setattr(crime_data.requests, 'get', fake_get)

    data = crime_data.get_crime_data(40.0, -75.0, radius_miles=0.5)
    assert called['url'].startswith('https://')
    assert data['incident_count'] == 3
    assert data['violent_crimes'] == 1
    assert data['property_crimes'] == 1
    assert data['other_crimes'] == 1


def test_crime_cache_helpers(tmp_path):
    # point cache directory to tmp
    os.chdir(tmp_path)
    sample = {'crime_score': 0.1}
    cache_utils.save_cached_crime_data(40.0, -75.0, 0.5, sample, cache_duration_days=1)
    loaded = cache_utils.get_cached_crime_data(40.0, -75.0, 0.5)
    assert loaded == sample


def test_analyzer_uses_crime_api(monkeypatch):
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

    called = {'count': 0}

    def fake_get_crime_data(lat, lon, radius_miles=0.5):
        called['count'] += 1
        return {
            'crime_score': 0.2,
            'incident_count': 1,
            'violent_crimes': 1,
            'property_crimes': 0,
            'other_crimes': 0,
            'safety_grade': 'A',
        }

    monkeypatch.setattr(crime_data, 'get_crime_data', fake_get_crime_data)

    results = analyzer._analyze_locations({})
    assert len(results) == 1
    assert results[0].safety_analysis.crime_score == 0.2
    assert called['count'] == 1
