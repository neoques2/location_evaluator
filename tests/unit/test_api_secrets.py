import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.config_parser import ConfigParser


def _create_minimal_config(path):
    (path / "analysis.yaml").write_text(
        "analysis:\n  center_point: [0,0]\n  grid_size: 1\n  max_radius: 5\n"
    )
    dest_yaml = '''destinations:
  work:
    - address: "A"
      name: "Office"
      schedule:
        - days: "Mon"
          arrival_time: "09:00"
          departure_time: "17:00"'''
    (path / "destinations.yaml").write_text(dest_yaml)
    (path / "transportation.yaml").write_text(
        "transportation:\n  modes:\n    - driving\n"
    )
    (path / "api.yaml").write_text(
        "apis:\n  osrm:\n    base_url: http://localhost:5000\n    timeout: 30\n    requests_per_second: 10\n    cache: false\n    batch_size: 5\n  fbi_crime:\n    base_url: https://example.com/\n    timeout: 30\n"
    )
    (path / "weights.yaml").write_text(
        "weights:\n  travel_time: 0.5\n  travel_cost: 0.3\n  safety: 0.2\n"
    )
    (path / "output.yaml").write_text(
        "output:\n  output_format: json\n  cache_duration: 7\n"
    )


def test_api_secrets_file_sets_env(tmp_path, monkeypatch):
    _create_minimal_config(tmp_path)
    (tmp_path / "api_secrets.yaml").write_text("FBI_API_KEY: TESTKEY")
    monkeypatch.delenv("FBI_API_KEY", raising=False)
    parser = ConfigParser()
    cfg = parser.load_config(tmp_path)
    parser.validate_config(cfg)
    assert os.getenv("FBI_API_KEY") == "TESTKEY"
