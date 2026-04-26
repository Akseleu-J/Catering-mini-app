"""
config/logging_setup.py
Structured logging configuration.
"""

import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """Configure application-wide structured logging."""
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt, datefmt))

    # File handler for persistent logs
    file_handler = logging.FileHandler("bot.log", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(fmt, datefmt))

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)
    root.addHandler(file_handler)

    # Suppress noisy libs
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get named logger."""
    return logging.getLogger(name)
