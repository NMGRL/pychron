"""Configuration for observability/metrics export."""


class MetricsConfig:
    """Configuration for Prometheus metrics export.

    Attributes:
        enabled: Whether metrics collection is enabled.
        host: Host to bind the metrics HTTP server to.
        port: Port to bind the metrics HTTP server to.
        namespace: Prometheus metric namespace prefix.
    """

    def __init__(
        self,
        enabled: bool = False,
        host: str = "127.0.0.1",
        port: int = 9109,
        namespace: str = "pychron",
    ) -> None:
        """Initialize metrics configuration.

        Args:
            enabled: Whether metrics collection is enabled.
            host: Host to bind to (default: 127.0.0.1).
            port: Port to bind to (default: 9109).
            namespace: Metric namespace prefix (default: pychron).
        """
        self.enabled = enabled
        self.host = host
        self.port = port
        self.namespace = namespace
