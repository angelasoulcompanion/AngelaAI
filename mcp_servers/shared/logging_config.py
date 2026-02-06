"""
Unified logging configuration for Angela MCP servers.

All servers use stderr for logging (stdout is reserved for MCP protocol).
"""

import logging
import sys


def setup_logging(server_name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return a logger for an MCP server.

    Args:
        server_name: Name of the server (e.g., "angela-calendar")
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(server_name)

    # Avoid adding duplicate handlers if called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(
            logging.Formatter(
                f"[{server_name}] %(levelname)s %(message)s"
            )
        )
        logger.addHandler(handler)

    logger.setLevel(level)
    return logger
