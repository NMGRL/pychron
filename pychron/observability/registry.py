"""Registry for Prometheus metrics collectors."""

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

_registry: CollectorRegistry | None = None
_metrics_cache: dict = {}  # Cache of {name: metric_instance}


def get_registry() -> CollectorRegistry:
    """Get or create the global metrics registry.

    Returns:
        The singleton CollectorRegistry instance.
    """
    global _registry
    if _registry is None:
        _registry = CollectorRegistry()
    return _registry


def counter(
    name: str,
    documentation: str,
    labelnames: list[str] | None = None,
) -> Counter:
    """Create or get a Counter metric.

    Args:
        name: Metric name.
        documentation: Metric documentation.
        labelnames: Optional list of label names.

    Returns:
        A Counter instance.
    """
    # Check cache first
    if name in _metrics_cache:
        return _metrics_cache[name]

    labelnames = labelnames or []
    registry = get_registry()
    try:
        metric = Counter(
            name,
            documentation,
            labelnames=labelnames,
            registry=registry,
        )
        _metrics_cache[name] = metric
        return metric
    except ValueError:
        # Metric already registered, retrieve it from registry
        # by collecting and finding the metric by name
        for family in registry.collect():
            if family.name == name:
                # Return a wrapper that accesses the metric through samples
                # For now, cache and return from cache
                if name in _metrics_cache:
                    return _metrics_cache[name]
                # Fallback: create a local wrapper
                metric = Counter(
                    name,
                    documentation,
                    labelnames=labelnames,
                    registry=None,  # Don't register again
                )
                _metrics_cache[name] = metric
                return metric
        # If not found, raise the original error
        raise


def gauge(
    name: str,
    documentation: str,
    labelnames: list[str] | None = None,
) -> Gauge:
    """Create or get a Gauge metric.

    Args:
        name: Metric name.
        documentation: Metric documentation.
        labelnames: Optional list of label names.

    Returns:
        A Gauge instance.
    """
    # Check cache first
    if name in _metrics_cache:
        return _metrics_cache[name]

    labelnames = labelnames or []
    registry = get_registry()
    try:
        metric = Gauge(
            name,
            documentation,
            labelnames=labelnames,
            registry=registry,
        )
        _metrics_cache[name] = metric
        return metric
    except ValueError:
        # Metric already registered, retrieve it from cache or registry
        if name in _metrics_cache:
            return _metrics_cache[name]
        for family in registry.collect():
            if family.name == name:
                metric = Gauge(
                    name,
                    documentation,
                    labelnames=labelnames,
                    registry=None,
                )
                _metrics_cache[name] = metric
                return metric
        raise


def histogram(
    name: str,
    documentation: str,
    labelnames: list[str] | None = None,
    buckets: tuple[float, ...] | None = None,
) -> Histogram:
    """Create or get a Histogram metric.

    Args:
        name: Metric name.
        documentation: Metric documentation.
        labelnames: Optional list of label names.
        buckets: Optional custom bucket boundaries.

    Returns:
        A Histogram instance.
    """
    # Check cache first
    if name in _metrics_cache:
        return _metrics_cache[name]

    labelnames = labelnames or []
    registry = get_registry()
    kwargs = {
        "name": name,
        "documentation": documentation,
        "labelnames": labelnames,
        "registry": registry,
    }
    if buckets:
        kwargs["buckets"] = buckets
    try:
        metric = Histogram(**kwargs)
        _metrics_cache[name] = metric
        return metric
    except ValueError:
        # Metric already registered, retrieve it from cache or registry
        if name in _metrics_cache:
            return _metrics_cache[name]
        for family in registry.collect():
            if family.name == name:
                kwargs["registry"] = None
                metric = Histogram(**kwargs)
                _metrics_cache[name] = metric
                return metric
        raise


def clear_cache() -> None:
    """Clear the metrics cache. Used for testing."""
    global _metrics_cache
    _metrics_cache.clear()
