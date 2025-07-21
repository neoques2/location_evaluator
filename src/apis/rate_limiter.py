"""
Rate Limiting and API Error Handling
Handles rate limiting for API calls and implements retry logic with exponential backoff.
"""

import time
import json
import os
import logging
import requests
from typing import Callable, Any, Optional
from datetime import datetime, timedelta


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""

    pass


class QuotaExceededError(Exception):
    """Raised when API quota is exceeded."""

    pass


class RateLimiter:
    """
    Rate limiter to ensure API calls don't exceed specified limits.
    """

    def __init__(self, requests_per_second: int = 10):
        """
        Initialize rate limiter.

        Args:
            requests_per_second: Maximum requests per second allowed
        """
        self.requests_per_second = requests_per_second
        self.last_request_time = 0

    def wait_if_needed(self) -> None:
        """
        Wait if necessary to maintain rate limit.
        """
        time_since_last = time.time() - self.last_request_time
        min_interval = 1.0 / self.requests_per_second

        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)

        self.last_request_time = time.time()


class APIHandler:
    """
    Handles API calls with retry logic and error handling.
    """

    def __init__(self, retry_count: int = 3, backoff_factor: int = 2):
        """
        Initialize API handler.

        Args:
            retry_count: Number of retry attempts
            backoff_factor: Exponential backoff multiplier
        """
        self.retry_count = retry_count
        self.backoff_factor = backoff_factor
        self.logger = logging.getLogger(__name__)

    def call_with_retry(self, api_func: Callable) -> Any:
        """
        Call API function with retry logic.

        Args:
            api_func: Function to call (should be a lambda or callable with no args)

        Returns:
            Result of API function call

        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None

        for attempt in range(self.retry_count):
            try:
                return api_func()
            except requests.exceptions.HTTPError as e:
                last_exception = e
                if e.response.status_code == 429:  # Rate limit exceeded
                    if attempt == self.retry_count - 1:
                        raise RateLimitError(
                            f"Rate limit exceeded after {self.retry_count} attempts"
                        )
                    wait_time = self.backoff_factor**attempt
                    self.logger.warning(
                        f"Rate limit hit (attempt {attempt + 1}), retrying in {wait_time} seconds..."
                    )
                    time.sleep(wait_time)
                elif e.response.status_code == 403:  # Quota exceeded
                    raise QuotaExceededError("API quota exceeded")
                else:
                    if attempt == self.retry_count - 1:
                        raise
                    wait_time = self.backoff_factor**attempt
                    self.logger.warning(
                        f"HTTP error {e.response.status_code} (attempt {attempt + 1}), retrying in {wait_time} seconds..."
                    )
                    time.sleep(wait_time)
            except (
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
            ) as e:
                last_exception = e
                if attempt == self.retry_count - 1:
                    raise
                wait_time = self.backoff_factor**attempt
                self.logger.warning(
                    f"Network error (attempt {attempt + 1}), retrying in {wait_time} seconds..."
                )
                time.sleep(wait_time)
            except Exception as e:
                last_exception = e
                if attempt == self.retry_count - 1:
                    raise
                wait_time = self.backoff_factor**attempt
                self.logger.warning(
                    f"API call failed (attempt {attempt + 1}), retrying in {wait_time} seconds..."
                )
                time.sleep(wait_time)

        # This shouldn't be reached, but just in case
        raise (
            last_exception if last_exception else Exception("Unknown error in API call")
        )

    def get_fallback_data(self, *args, **kwargs) -> Optional[Any]:
        """
        Get fallback data when API calls fail.

        Args:
            *args: Arguments from original API call
            **kwargs: Keyword arguments from original API call

        Returns:
            Cached data if available, None otherwise
        """
        self.logger.info("Attempting to use fallback/cached data...")
        # TODO: Implement fallback logic based on cached data
        return None
