#!/usr/bin/env python3
"""
Angela Logging Configuration
Centralized logging setup for all Angela services
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime


# Log directory
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Log levels
LOG_LEVEL = logging.INFO
LOG_LEVEL_CONSOLE = logging.INFO
LOG_LEVEL_FILE = logging.DEBUG

# Log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    name: str = "angela",
    level: int = LOG_LEVEL,
    log_to_file: bool = True,
    log_to_console: bool = True,
    log_file: str = None
) -> logging.Logger:
    """
    Setup centralized logging for Angela services

    Args:
        name: Logger name (usually __name__)
        level: Logging level
        log_to_file: Whether to log to file
        log_to_console: Whether to log to console
        log_file: Custom log file name (optional)

    Returns:
        Configured logger instance

    Usage:
        from angela_core.logging_config import setup_logging
        logger = setup_logging(__name__)
    """
    # Create logger
    logger = logging.getLogger(name)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False

    # Create formatter
    formatter = logging.Formatter(
        fmt=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT
    )

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(LOG_LEVEL_CONSOLE)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if log_to_file:
        if log_file is None:
            # Default log file based on logger name
            log_file = f"{name.replace('.', '_')}.log"

        log_path = LOG_DIR / log_file

        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(LOG_LEVEL_FILE)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def setup_service_logging(service_name: str) -> logging.Logger:
    """
    Setup logging for an Angela service with standard configuration

    Args:
        service_name: Name of the service (e.g., 'memory', 'embedding', 'daemon')

    Returns:
        Configured logger

    Usage:
        logger = setup_service_logging('memory_service')
    """
    log_file = f"angela_{service_name}.log"
    return setup_logging(
        name=f"angela.{service_name}",
        log_file=log_file
    )


def get_logger(name: str = None) -> logging.Logger:
    """
    Get or create a logger with Angela's standard configuration

    Args:
        name: Logger name (defaults to 'angela')

    Returns:
        Logger instance
    """
    name = name or "angela"
    logger = logging.getLogger(name)

    # Setup if not already configured
    if not logger.handlers:
        return setup_logging(name)

    return logger


# Predefined service loggers
def get_memory_logger() -> logging.Logger:
    """Get logger for memory service"""
    return setup_service_logging("memory")


def get_embedding_logger() -> logging.Logger:
    """Get logger for embedding service"""
    return setup_service_logging("embedding")


def get_consciousness_logger() -> logging.Logger:
    """Get logger for consciousness systems"""
    return setup_service_logging("consciousness")


def get_daemon_logger() -> logging.Logger:
    """Get logger for daemon"""
    return setup_service_logging("daemon")


def get_api_logger() -> logging.Logger:
    """Get logger for API services"""
    return setup_service_logging("api")


# Configure root Angela logger
root_logger = setup_logging("angela", log_file="angela.log")


# Silence noisy libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("asyncpg").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
