"""Network connectivity helper functions."""

from typing import Optional
import logging
import requests


def check_network_connectivity(url: str, timeout: int = 5) -> bool:
    """Return True if ``url`` is reachable."""
    logger = logging.getLogger(__name__)
    try:
        requests.head(url, timeout=timeout)
        return True
    except Exception as e:
        logger.warning(f"Network connectivity check failed for {url}: {e}")
        return False

