import os
import sys
from pathlib import Path
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.config_parser import ConfigParser, ConfigValidationError
def _create_config(tmp_path: Path):
    (tmp_path / 'analysis.yaml').write_text('analysis:\n  center_point: [0,0]\n  grid_size: 1\n  max_radius: 5\n')
    dest_yaml = '''destinations:
  work:
    - address: "1 Main St"
      name: "Office"
      schedule:
        - days: "Mon"
          arrival_time: "09:00"
          departure_time: "17:00"'''
    (tmp_path / 'destinations.yaml').write_text(dest_yaml)
    (tmp_path / 'transportation.yaml').write_text('transportation:\n  modes:\n    - driving\n')
    (tmp_path / 'api.yaml').write_text('apis:\n  osrm:\n    base_url: http://localhost:5000\n    timeout: 30\n    requests_per_second: 10\n    cache: false\n    batch_size: 5\n  fbi_crime:\n    base_url: https://example.com/\n    timeout: 30\n')
    (tmp_path / 'weights.yaml').write_text('weights:\n  travel_time: 0.5\n  travel_cost: 0.3\n  safety: 0.2\n')
    (tmp_path / 'output.yaml').write_text('output:\n  output_format: json\n  cache_duration: 7\n')


def test_geocoding_validation(monkeypatch, tmp_path):
    _create_config(tmp_path)

    monkeypatch.setattr('src.config_parser.geocode_address', lambda addr, **k: {'lat': 1.0, 'lon': 2.0})
    monkeypatch.setattr('src.config_parser.check_network_connectivity', lambda url, timeout=5: True)
    monkeypatch.setenv('LE_SKIP_NETWORK', '0')

    parser = ConfigParser()
    cfg = parser.load_config(tmp_path)
    parser.validate_config(cfg)
    assert cfg['destinations']['work'][0]['lat'] == 1.0


def test_geocoding_failure(monkeypatch, tmp_path):
    _create_config(tmp_path)

    monkeypatch.setattr('src.config_parser.geocode_address', lambda addr, **k: None)
    monkeypatch.setattr('src.config_parser.check_network_connectivity', lambda url, timeout=5: True)
    monkeypatch.setenv('LE_SKIP_NETWORK', '0')

    parser = ConfigParser()
    cfg = parser.load_config(tmp_path)
    with pytest.raises(ConfigValidationError):
        parser.validate_config(cfg)


def test_network_failure(monkeypatch, tmp_path):
    _create_config(tmp_path)

    monkeypatch.setattr('src.config_parser.geocode_address', lambda addr, **k: {'lat': 1.0, 'lon': 2.0})
    monkeypatch.setattr('src.config_parser.check_network_connectivity', lambda url, timeout=5: False)
    monkeypatch.setenv('LE_SKIP_NETWORK', '0')

    parser = ConfigParser()
    cfg = parser.load_config(tmp_path)
    with pytest.raises(ConfigValidationError):
        parser.validate_config(cfg)

