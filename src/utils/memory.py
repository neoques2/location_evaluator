import os
import logging
from typing import Optional

import psutil


def log_memory_usage(logger: Optional[logging.Logger] = None, label: str = "") -> float:
    """Log current process memory usage in MB."""
    process = psutil.Process(os.getpid())
    mem_mb = process.memory_info().rss / (1024 * 1024)
    if logger:
        logger.debug(f"memory_usage_{label}: {mem_mb:.2f} MB")
    return mem_mb
