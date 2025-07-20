import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.utils.memory import log_memory_usage


def test_log_memory_usage():
    mem = log_memory_usage(None, "test")
    assert isinstance(mem, float)
    assert mem > 0
