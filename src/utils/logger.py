"""
Centralized logging utility for the Customer Subscription & Churn
Intelligence Platform.

Every pipeline stage imports get_logger(__name__) rather than configuring
logging ad-hoc, so log formatting, levels, and destinations stay consistent
across ingestion, cleaning, feature engineering, and ETL modules.
"""

import logging
import os
from datetime import datetime

_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")


def get_logger(name: str, log_to_file: bool = True) -> logging.Logger:
    """
    Create (or retrieve) a configured logger.

    Parameters
    ----------
    name : str
        Typically __name__ of the calling module.
    log_to_file : bool
        If True, also write logs to logs/pipeline_<date>.log in addition
        to stdout.

    Returns
    -------
    logging.Logger
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        # Already configured (avoids duplicate handlers on repeated imports)
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_to_file:
        os.makedirs(_LOG_DIR, exist_ok=True)
        log_file = os.path.join(_LOG_DIR, f"pipeline_{datetime.now():%Y%m%d}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
