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

    data = crime_data.get_crime_data(40.0, -75.0, radius_miles=0.5, use_cache=False)
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


def test_get_crime_data_uses_cache(monkeypatch, tmp_path):
    os.chdir(tmp_path)
    calls = {'count': 0}

    def fake_get(url, params=None, timeout=10):
        calls['count'] += 1
        return DummyResp({'incidents': []})

    monkeypatch.setattr(crime_data.requests, 'get', fake_get)

    result1 = crime_data.get_crime_data(40.0, -75.0, radius_miles=0.5, cache_duration_days=1)
    assert calls['count'] == 1

    result2 = crime_data.get_crime_data(40.0, -75.0, radius_miles=0.5, cache_duration_days=1)
    assert calls['count'] == 1  # no additional call
    assert result1 == result2


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

    def fake_get_crime_data(lat, lon, radius_miles=0.5, **kwargs):
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


def test_calculate_safety_score_increases_with_crime():
    low = crime_data.calculate_safety_score(1, 0, 0, 1000.0)
    high = crime_data.calculate_safety_score(5, 3, 2, 1000.0)
    assert 0 <= low <= 1
    assert 0 <= high <= 1
    assert high > low


def test_calculate_safety_score_uses_weights():
    default = crime_data.calculate_safety_score(1, 1, 1, 1000.0)
    weighted = crime_data.calculate_safety_score(
        1,
        1,
        1,
        1000.0,
        weights={'violent': 4.0, 'property': 2.0, 'other': 1.0},
    )
    assert weighted > default


def test_get_bounding_box_produces_reasonable_offsets():
    bbox = crime_data.get_bounding_box(40.0, -75.0, 1.0)
    assert bbox['north'] > 40.0
    assert bbox['south'] < 40.0
    assert bbox['east'] > -75.0
    assert bbox['west'] < -75.0
    assert bbox['east'] - bbox['west'] > 0
    assert bbox['north'] - bbox['south'] > 0
