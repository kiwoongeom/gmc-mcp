"""Structured logging for gmc-mcp.

Stays on stdlib so we don't impose loguru/structlog on consumers. Uses a single
named logger 'gmc_mcp' so apps can configure it however they want."""

from __future__ import annotations

import logging
import os
import sys

LOGGER_NAME = "gmc_mcp"

_LEVELS = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}


def get_logger(name: str | None = None) -> logging.Logger:
    """Return the package logger or a sub-logger of it."""
    base = logging.getLogger(LOGGER_NAME)
    if not base.handlers:
        configure_default()
    if name and name != LOGGER_NAME:
        return base.getChild(name)
    return base


def configure_default() -> None:
    """Idempotent default handler configuration.

    Writes to stderr (so stdio MCP transport's stdout stays clean for JSON-RPC).
    Level is taken from GMC_LOG_LEVEL env var, defaulting to INFO.
    """
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return
    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    logger.addHandler(handler)
    level_name = os.environ.get("GMC_LOG_LEVEL", "INFO").upper()
    logger.setLevel(_LEVELS.get(level_name, logging.INFO))
    logger.propagate = False
