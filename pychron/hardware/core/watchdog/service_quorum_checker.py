"""Pre-experiment service health verification.

Verifies that required services are available before experiment execution.
Uses quorum strategies similar to device quorum checking but for services.
"""

from typing import Dict, List, Tuple, Optional
from enum import Enum


class ServiceQuorumStrategy(Enum):
    """Service quorum strategy."""

    ALL_REQUIRED = "all_required"  # All required services must be healthy
    ANY_REQUIRED = "any_required"  # At least one required service must be healthy
    OPTIONAL = "optional"  # Service not required


# Default service requirements per experiment phase
DEFAULT_SERVICE_REQUIREMENTS = {
    "pre_experiment": {
        "required_services": ["database"],  # Need DB for sample info
        "strategy": ServiceQuorumStrategy.ALL_REQUIRED,
    },
    "extraction": {
        "required_services": ["database"],  # Need DB to log extraction
        "strategy": ServiceQuorumStrategy.ALL_REQUIRED,
    },
    "measurement": {
        "required_services": ["database"],  # Need DB to log measurement
        "strategy": ServiceQuorumStrategy.ALL_REQUIRED,
    },
    "save": {
        "required_services": ["database", "dvc"],
        "strategy": ServiceQuorumStrategy.ANY_REQUIRED,  # Can save to either
    },
}


class ServiceQuorumChecker:
    """Verify service availability before experiment phases.

    Attributes:
        phase_requirements: Dict mapping phase name to {required_services, strategy}
    """

    def __init__(self, logger: Optional[any] = None):
        """Initialize service quorum checker.

        Args:
            logger: Optional logger object for debug output
        """
        # Copy defaults and allow customization
        self.phase_requirements = DEFAULT_SERVICE_REQUIREMENTS.copy()
        self._logger = logger

    def set_phase_requirements(
        self,
        phase_name: str,
        required_services: List[str],
        strategy: ServiceQuorumStrategy,
    ) -> None:
        """Set service requirements for a phase.

        Args:
            phase_name: Experiment phase (e.g., "extraction", "measurement")
            required_services: List of service names
            strategy: Quorum strategy (ALL_REQUIRED or ANY_REQUIRED)
        """
        self.phase_requirements[phase_name] = {
            "required_services": required_services,
            "strategy": strategy,
        }

    def verify_phase_quorum(
        self, phase_name: str, service_map: Dict[str, object]
    ) -> Tuple[bool, str]:
        """Verify service availability for a phase.

        Args:
            phase_name: Experiment phase name
            service_map: Dict mapping service name to service object with get_state() method

        Returns:
            (passed: bool, status_msg: str)
        """
        if phase_name not in self.phase_requirements:
            # No requirements defined, assume OK
            return True, f"{phase_name}: no requirements defined"

        req = self.phase_requirements[phase_name]
        required_services = req["required_services"]
        strategy = req["strategy"]

        if not required_services:
            return True, f"{phase_name}: no required services"

        # Check health of each required service
        healthy_services = []
        unhealthy_services = []

        for service_name in required_services:
            if service_name not in service_map:
                unhealthy_services.append(service_name)
                continue

            service = service_map[service_name]
            # Service objects should have get_state() method returning ServiceState
            is_healthy = True  # Default to healthy if no heartbeat
            try:
                if hasattr(service, "get_state") and callable(getattr(service, "get_state")):
                    from pychron.hardware.core.watchdog.service_heartbeat import ServiceState

                    state = service.get_state()
                    # Only process if state is actually a ServiceState enum
                    if isinstance(state, ServiceState):
                        is_healthy = state == ServiceState.HEALTHY
                    # else: keep default is_healthy = True
            except Exception:
                # If get_state fails, treat as healthy (best effort)
                is_healthy = True

            if is_healthy:
                healthy_services.append(service_name)
            else:
                unhealthy_services.append(service_name)

        # Apply strategy
        passed = False
        if strategy == ServiceQuorumStrategy.ALL_REQUIRED:
            passed = len(unhealthy_services) == 0
        elif strategy == ServiceQuorumStrategy.ANY_REQUIRED:
            passed = len(healthy_services) > 0

        return passed, self._build_status_message(
            phase_name, required_services, healthy_services, unhealthy_services, strategy
        )

    def get_phase_status(self, phase_name: str, service_map: Dict[str, object]) -> Dict[str, any]:
        """Get detailed status for a phase.

        Args:
            phase_name: Experiment phase name
            service_map: Dict mapping service name to service objects

        Returns:
            Dict with phase status details
        """
        passed, status_msg = self.verify_phase_quorum(phase_name, service_map)

        if phase_name not in self.phase_requirements:
            required = []
            strategy = None
        else:
            req = self.phase_requirements[phase_name]
            required = req["required_services"]
            strategy = req["strategy"].value

        return {
            "phase": phase_name,
            "passed": passed,
            "status_message": status_msg,
            "required_services": required,
            "strategy": strategy,
        }

    def log_service_status(self, service_map: Dict[str, object], logger_func=None) -> None:
        """Log service health status.

        Args:
            service_map: Dict mapping service name to service objects
            logger_func: Logger function (defaults to self._logger or print)
        """
        if logger_func is None:
            if self._logger and hasattr(self._logger, "debug"):
                logger_func = self._logger.debug
            else:
                logger_func = print

        logger_func("=" * 60)
        logger_func("SERVICE HEALTH STATUS")
        logger_func("=" * 60)

        for service_name, service in service_map.items():
            state = "UNKNOWN"
            stats = None

            try:
                if hasattr(service, "get_state"):
                    state = service.get_state().value
                if hasattr(service, "get_stats"):
                    stats = service.get_stats()
            except Exception as e:
                logger_func(f"  {service_name:<20} ERROR: {e}")
                continue

            is_required = False
            try:
                if hasattr(service, "is_required"):
                    is_required = service.is_required
            except Exception:
                pass

            req_str = "(required)" if is_required else "(optional)"
            logger_func(f"  {service_name:<20} {state:<15} {req_str}")

            if stats:
                logger_func(f"    Time in state: {stats.get('time_in_state', 'N/A'):.1f}s")
                if stats.get("avg_response_time"):
                    logger_func(f"    Avg response:  {stats['avg_response_time']:.3f}s")
                if stats.get("last_error"):
                    logger_func(f"    Last error:    {stats['last_error']}")

    def _build_status_message(
        self,
        phase_name: str,
        required: List[str],
        healthy: List[str],
        unhealthy: List[str],
        strategy: ServiceQuorumStrategy,
    ) -> str:
        """Build human-readable status message."""
        if strategy == ServiceQuorumStrategy.ALL_REQUIRED:
            if unhealthy:
                return (
                    f"{phase_name}: FAIL - required services unavailable: "
                    f"{', '.join(unhealthy)} (need all of {', '.join(required)})"
                )
            return f"{phase_name}: OK - all required services healthy ({', '.join(required)})"
        else:
            if not healthy:
                return (
                    f"{phase_name}: FAIL - no healthy services "
                    f"({', '.join(required)} all unavailable)"
                )
            return f"{phase_name}: OK - {len(healthy)} service(s) available ({', '.join(healthy)})"
