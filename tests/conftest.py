import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_PATH = os.path.join(PROJECT_ROOT, 'src')
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

import pytest


@pytest.fixture(autouse=True)
def _patch_external_calls(monkeypatch):
    """Avoid real network calls during tests."""
    monkeypatch.setattr('src.config_parser.geocode_address', lambda addr, **k: {'lat': 0.0, 'lon': 0.0})
    monkeypatch.setattr('src.config_parser.check_network_connectivity', lambda url, timeout=5: True)
    monkeypatch.setenv('LE_SKIP_NETWORK', '1')
