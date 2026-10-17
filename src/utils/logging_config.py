"""
Logging configuration for NexusMart Data Analytics Pipeline.
Provides standardized, structured logging to both console and log files.
"""

import logging
import sys
from pathlib import Path


def setup_logger(name: str = "nexusmart", log_file: Path | None = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configures and returns a logger instance with consistent formatting.
    Avoids duplicate handlers if called multiple times.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler if specified
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger
