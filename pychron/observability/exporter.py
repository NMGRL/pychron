"""HTTP exporter for Prometheus metrics."""

import logging
from typing import Any

from prometheus_client import start_http_server

from .config import MetricsConfig
from .metrics import get_config, is_enabled
from .registry import get_registry

logger = logging.getLogger(__name__)

_exporter_started = False


def start_exporter() -> bool:
    """Start the Prometheus HTTP metrics exporter.

    Starts an HTTP server serving Prometheus metrics on the configured
    host and port. Safe to call multiple times (idempotent).

    Returns:
        True if exporter was started or was already running.
        False if startup failed (and was logged).
    """
    global _exporter_started

    if not is_enabled():
        return True  # Enabled check passed (it's disabled, which is fine)

    if _exporter_started:
        return True  # Already running

    config = get_config()
    registry = get_registry()

    try:
        start_http_server(
            port=config.port,
            addr=config.host,
            registry=registry,
        )
        _exporter_started = True
        logger.info(f"Prometheus metrics exporter started on {config.host}:{config.port}/metrics")
        return True
    except Exception as e:
        logger.warning(
            f"Failed to start Prometheus metrics exporter on " f"{config.host}:{config.port}: {e}"
        )
        return False


def is_exporter_started() -> bool:
    """Check if the exporter has been started.

    Returns:
        True if exporter was successfully started.
    """
    return _exporter_started
