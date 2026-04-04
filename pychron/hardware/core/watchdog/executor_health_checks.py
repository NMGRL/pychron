"""Device quorum verification for experiment phase execution.

Provides pre-phase health checks to ensure critical devices are available
before starting extraction, measurement, save, and other phases.
"""

from typing import Dict, List, Optional, Any

from pychron.hardware.core.watchdog import HeartbeatState


class DeviceQuorumChecker:
    """Verify device health quorum before phase execution.

    Supports two strategies:
    - all_healthy: All required devices must be HEALTHY
    - any_healthy: At least one required device must be HEALTHY
    """

    # Default quorum requirements per phase
    DEFAULT_PHASE_REQUIREMENTS = {
        "extraction": {
            "required_devices": ["MS", "EL", "pump"],
            "strategy": "all_healthy",
        },
        "measurement": {
            "required_devices": ["detector", "spectrometer"],
            "strategy": "all_healthy",
        },
        "save": {
            "required_devices": ["database"],
            "strategy": "any_healthy",
        },
    }

    def __init__(self, phase_requirements: Optional[Dict[str, Dict[str, Any]]] = None):
        """Initialize quorum checker.

        Args:
            phase_requirements: Dict mapping phase names to requirements:
                {
                    "extraction": {
                        "required_devices": ["MS", "EL"],
                        "strategy": "all_healthy"  # or "any_healthy"
                    },
                    ...
                }
                If None, uses DEFAULT_PHASE_REQUIREMENTS.
        """
        self.phase_requirements = phase_requirements or self.DEFAULT_PHASE_REQUIREMENTS

    def verify_phase_quorum(self, phase_name: str, device_map: Dict[str, Any]) -> tuple[bool, str]:
        """Verify device quorum for a phase.

        Args:
            phase_name: Name of phase (e.g., "extraction", "measurement")
            device_map: Dict mapping device names to device objects with
                        get_device_health() method

        Returns:
            Tuple of (passed: bool, status_message: str)
            - passed=True if quorum met
            - status_message describes devices and their states
        """
        if phase_name not in self.phase_requirements:
            # Phase not configured, allow it
            return True, f"No quorum requirements for phase: {phase_name}"

        phase_config = self.phase_requirements[phase_name]
        required_devices = phase_config.get("required_devices", [])
        strategy = phase_config.get("strategy", "all_healthy")

        if not required_devices:
            return True, f"No devices required for phase: {phase_name}"

        # Check each required device
        device_statuses = {}
        healthy_count = 0

        for device_name in required_devices:
            if device_name not in device_map:
                device_statuses[device_name] = "NOT_FOUND"
                continue

            device = device_map[device_name]
            health_state = self._get_device_health(device)

            if health_state is None:
                # Device without heartbeat - treat as healthy
                device_statuses[device_name] = "HEALTHY"
                healthy_count += 1
            elif health_state == HeartbeatState.HEALTHY:
                device_statuses[device_name] = "HEALTHY"
                healthy_count += 1
            elif health_state == HeartbeatState.DEGRADED:
                device_statuses[device_name] = "DEGRADED"
            elif health_state == HeartbeatState.UNAVAILABLE:
                device_statuses[device_name] = "UNAVAILABLE"
            elif health_state == HeartbeatState.RECOVERING:
                device_statuses[device_name] = "RECOVERING"
            else:
                device_statuses[device_name] = str(health_state)

        # Evaluate strategy
        if strategy == "all_healthy":
            passed = healthy_count == len(required_devices)
        elif strategy == "any_healthy":
            passed = healthy_count > 0
        else:
            # Unknown strategy, fail safe
            passed = False

        # Build status message
        status_lines = [f"Phase '{phase_name}' ({strategy}):"]
        for device_name, state in device_statuses.items():
            status_lines.append(f"  {device_name}: {state}")
        status_message = "\n".join(status_lines)

        return passed, status_message

    def get_phase_status(self, phase_name: str, device_map: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed phase status.

        Args:
            phase_name: Name of phase
            device_map: Dict mapping device names to device objects

        Returns:
            Dict with keys:
            - phase_name
            - strategy
            - required_devices
            - device_statuses (dict of device_name -> state)
            - healthy_count
            - total_count
            - passed (bool)
        """
        phase_config = self.phase_requirements.get(
            phase_name, {"required_devices": [], "strategy": "all_healthy"}
        )
        required_devices = phase_config.get("required_devices", [])
        strategy = phase_config.get("strategy", "all_healthy")

        device_statuses = {}
        healthy_count = 0

        for device_name in required_devices:
            if device_name not in device_map:
                device_statuses[device_name] = "NOT_FOUND"
                continue

            device = device_map[device_name]
            health_state = self._get_device_health(device)

            if health_state is None:
                # Device without heartbeat - treat as healthy
                state_value = "healthy"
                healthy_count += 1
            else:
                state_value = health_state.value
                if health_state == HeartbeatState.HEALTHY:
                    healthy_count += 1

            device_statuses[device_name] = state_value

        # Determine if passed
        if strategy == "all_healthy":
            passed = healthy_count == len(required_devices)
        elif strategy == "any_healthy":
            passed = healthy_count > 0
        else:
            passed = False

        return {
            "phase_name": phase_name,
            "strategy": strategy,
            "required_devices": required_devices,
            "device_statuses": device_statuses,
            "healthy_count": healthy_count,
            "total_count": len(required_devices),
            "passed": passed,
        }

    def _get_device_health(self, device: Any) -> Optional[HeartbeatState]:
        """Get device health state.

        Handles both:
        - Devices with get_device_health() method (heartbeat-enabled)
        - Devices without it (returns None, defaults to healthy)

        Args:
            device: Device object

        Returns:
            HeartbeatState or None if device doesn't support heartbeat
        """
        if hasattr(device, "get_device_health"):
            return device.get_device_health()
        return None


def log_device_status(device_map: Dict[str, Any], logger=None) -> str:
    """Generate human-readable device status report.

    Args:
        device_map: Dict mapping device names to device objects
        logger: Optional logger to write status to (logs at INFO level)

    Returns:
        Human-readable status string
    """
    status_lines = ["Device Health Status:"]

    for device_name, device in device_map.items():
        if hasattr(device, "get_device_health"):
            health = device.get_device_health()
            if health:
                state_str = health.value
                status_lines.append(f"  {device_name}: {state_str.upper()}")
            else:
                status_lines.append(f"  {device_name}: NO_HEARTBEAT")
        else:
            status_lines.append(f"  {device_name}: NO_HEARTBEAT")

    status_text = "\n".join(status_lines)

    if logger:
        logger.info(status_text)

    return status_text
