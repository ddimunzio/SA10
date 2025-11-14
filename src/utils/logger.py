"""
Logging configuration for the Ham Radio Contest application.

This module provides a centralized logging setup that can be used
across the entire application.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class LoggerConfig:
    """Configuration for application logging."""

    # Default log format
    DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    # Log levels
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


def setup_logger(
    name: str = "ham_contest",
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    console: bool = True,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """
    Set up a logger with console and/or file handlers.

    Args:
        name: Logger name (typically __name__ or application name)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        console: Whether to output to console
        format_string: Custom format string for log messages

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logger("my_module", level=logging.DEBUG)
        >>> logger.info("Application started")
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove any existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatter
    if format_string is None:
        format_string = LoggerConfig.DEFAULT_FORMAT

    formatter = logging.Formatter(
        format_string,
        datefmt=LoggerConfig.DEFAULT_DATE_FORMAT
    )

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger or create a basic one.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def create_log_file_path(base_dir: Optional[Path] = None) -> Path:
    """
    Create a log file path with timestamp.

    Args:
        base_dir: Base directory for logs (defaults to ./logs)

    Returns:
        Path to log file with timestamp

    Example:
        >>> path = create_log_file_path()
        >>> print(path)
        logs/app_2024-11-13_15-30-45.log
    """
    if base_dir is None:
        base_dir = Path("logs")

    base_dir = Path(base_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"app_{timestamp}.log"

    return base_dir / log_filename


# Create a default application logger
def get_app_logger() -> logging.Logger:
    """
    Get the default application logger.

    Returns:
        Default application logger
    """
    logger = logging.getLogger("ham_contest")

    # Only configure if not already configured
    if not logger.handlers:
        setup_logger(
            name="ham_contest",
            level=logging.INFO,
            console=True
        )

    return logger


# Example usage in other modules:
# from src.utils.logger import get_logger
# logger = get_logger(__name__)
# logger.info("Module initialized")

