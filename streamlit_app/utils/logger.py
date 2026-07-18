"""
Logging utility for the Streamlit app.

Mirrors the pattern in src/utils/logger.py used throughout the rest of
this project -- structured, timestamped, dual stdout+file output --
so the Streamlit layer follows the same coding standard as the data
engineering/ML layers rather than inventing a separate convention.
"""

import logging
import os
from datetime import datetime

from config import LOG_DIR, LOG_FILE


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError:
        # If the deployment environment's filesystem is read-only (common
        # on some free-tier hosting platforms), fall back to stdout-only
        # logging rather than crashing the whole app over a log file.
        logger.warning("Could not create log file -- falling back to stdout-only logging.")

    return logger
