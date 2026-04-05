"""Code generation wizard for device driver boilerplate.

This module provides functionality to generate device driver code,
config files, and tests from a template system.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class DriverSpec:
    """Device driver specification.

    Attributes:
        class_name: Name of the driver class
        manufacturer: Device manufacturer
        model: Device model
        comm_type: Communication type (RS232, TCP, USB, etc.)
        description: Device description
        website: Manufacturer website
        docs_url: Documentation URL
        port: Default communication port (optional)
        baudrate: Default baudrate for serial (optional)
    """

    class_name: str
    manufacturer: str
    model: str
    comm_type: str
    description: str
    website: str = ""
    docs_url: str = ""
    port: str = ""
    baudrate: str = "9600"

    def is_serial(self) -> bool:
        """Check if driver uses serial communication."""
        return self.comm_type.upper() in ("RS232", "SERIAL")

    def is_tcp(self) -> bool:
        """Check if driver uses TCP communication."""
        return self.comm_type.upper() in ("TCP", "UDP", "ETHERNET")

    def is_usb(self) -> bool:
        """Check if driver uses USB communication."""
        return self.comm_type.upper() == "USB"


class DriverGenerator:
    """Generator for device driver boilerplate code."""

    @staticmethod
    def generate_driver_class(spec: DriverSpec) -> str:
        """Generate device driver class code.

        Args:
            spec: DriverSpec with driver details

        Returns:
            Python code for the driver class
        """
        metadata_fields = [
            f"    name: {spec.class_name}",
            f"    description: {spec.description}",
            f"    company: {spec.manufacturer}",
            f"    model: {spec.model}",
            f"    website: {spec.website}" if spec.website else "",
            f"    docs_url: {spec.docs_url}" if spec.docs_url else "",
            f"    default_comm_type: {spec.comm_type}",
        ]
        metadata_str = "\n".join(filter(None, metadata_fields))

        code = f'''"""Driver for {spec.manufacturer} {spec.model}.

Device: {spec.class_name}
Communication: {spec.comm_type}
"""

from pychron.hardware.core.core_device import CoreDevice


class {spec.class_name}(CoreDevice):
    """
    :::
{metadata_str}
    :::
    """

    def __init__(self, *args, **kwargs):
        super({spec.class_name}, self).__init__(*args, **kwargs)
        # Initialize device-specific attributes here

    def load_additional_args(self, config, det):
        """Load device-specific configuration.
        
        Args:
            config: Configuration object
            det: Device element tree
        """
        super({spec.class_name}, self).load_additional_args(config, det)
        # Load device-specific settings from config

    def initialize(self, initial_state=None, *args, **kwargs):
        """Initialize the device.
        
        Args:
            initial_state: Optional initial state
        """
        self.debug("Initializing {spec.class_name}")
        # Add initialization code here
        return True

    def shutdown(self):
        """Shutdown the device."""
        self.debug("Shutting down {spec.class_name}")
        # Add shutdown code here

    def _get_state(self, *args, **kwargs):
        """Get current device state.
        
        Returns:
            Device state
        """
        # Implement state retrieval
        return None
'''
        return code

    @staticmethod
    def generate_config_file(spec: DriverSpec, device_name: str) -> str:
        """Generate configuration file for device.

        Args:
            spec: DriverSpec with driver details
            device_name: Name for the device instance

        Returns:
            INI-format config file content
        """
        config = f"""[General]
name = {device_name}
device_class = {spec.class_name}

[Communications]
type = {spec.comm_type.lower()}
"""

        if spec.is_serial():
            config += f"""port = {spec.port or 'COM1'}
baudrate = {spec.baudrate}
"""
        elif spec.is_tcp():
            config += f"""host = localhost
port = {spec.port or '5000'}
kind = TCP
"""

        config += """
[Scan]
enabled = False
graph = False
record = False
auto_start = False
period = 1.0
"""
        return config

    @staticmethod
    def generate_test_class(spec: DriverSpec) -> str:
        """Generate unit tests for device driver.

        Args:
            spec: DriverSpec with driver details

        Returns:
            Python code for unit tests
        """
        test_code = f'''"""Unit tests for {spec.class_name} driver.

Tests for {spec.manufacturer} {spec.model} device driver.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock

from pychron.hardware.{spec.class_name.lower()} import {spec.class_name}


class Test{spec.class_name}(unittest.TestCase):
    """Test {spec.class_name} driver."""

    def setUp(self):
        """Set up test fixtures."""
        self.device = {spec.class_name}()

    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self.device, 'shutdown'):
            self.device.shutdown()

    def test_create_instance(self):
        """Test creating driver instance."""
        self.assertIsNotNone(self.device)

    def test_initialize(self):
        """Test device initialization."""
        result = self.device.initialize()
        self.assertTrue(result)

    def test_get_state(self):
        """Test getting device state."""
        state = self.device._get_state()
        # Add assertions for expected state

    @patch('pychron.hardware.core.core_device.CoreDevice._ask')
    def test_communication(self, mock_ask):
        """Test device communication."""
        mock_ask.return_value = "OK"
        # Add test code for communication


if __name__ == '__main__':
    unittest.main()
'''
        return test_code

    @staticmethod
    def generate_readme(spec: DriverSpec) -> str:
        """Generate README documentation for driver.

        Args:
            spec: DriverSpec with driver details

        Returns:
            Markdown README content
        """
        readme = f"""# {spec.class_name} Driver

Driver for {spec.manufacturer} {spec.model} device.

## Overview

- **Device**: {spec.class_name}
- **Manufacturer**: {spec.manufacturer}
- **Model**: {spec.model}
- **Communication**: {spec.comm_type}
- **Description**: {spec.description}

## Installation

1. Copy driver file to `pychron/hardware/`
2. Update device configuration file
3. Add device to hardware configuration

## Configuration

### Serial Configuration (RS232)
```ini
[Communications]
type = serial
port = COM1
baudrate = 9600
```

### TCP Configuration
```ini
[Communications]
type = tcp
host = localhost
port = 5000
kind = TCP
```

## Usage

```python
from pychron.hardware.{spec.class_name.lower()} import {spec.class_name}

device = {spec.class_name}()
device.initialize()

# Interact with device
state = device.get_state()

device.shutdown()
```

## References

"""
        if spec.website:
            readme += f"- [Website]({spec.website})\n"
        if spec.docs_url:
            readme += f"- [Documentation]({spec.docs_url})\n"

        readme += """
## Troubleshooting

- Check device connection
- Verify configuration settings
- Review hardware logs

## Support

For issues or questions, contact the development team.
"""
        return readme


class DriverWizard:
    """Interactive wizard for driver creation.

    Guides through step-by-step driver creation process.
    """

    def __init__(self) -> None:
        """Initialize wizard."""
        self.spec: Optional[DriverSpec] = None
        self.current_step = 0
        self.steps = [
            "basic_info",
            "communications",
            "metadata",
            "review",
        ]

    def get_current_step(self) -> str:
        """Get current step name."""
        if self.current_step < len(self.steps):
            return self.steps[self.current_step]
        return "complete"

    def get_step_progress(self) -> tuple:
        """Get wizard progress.

        Returns:
            Tuple of (current_step, total_steps)
        """
        return self.current_step + 1, len(self.steps)

    def step1_basic_info(
        self, class_name: str, manufacturer: str, model: str, comm_type: str, description: str
    ) -> bool:
        """Collect basic driver information.

        Args:
            class_name: Driver class name
            manufacturer: Device manufacturer
            model: Device model
            comm_type: Communication type
            description: Device description

        Returns:
            True if step completed successfully
        """
        try:
            if not all([class_name, manufacturer, model, comm_type, description]):
                logger.error("All fields required for step 1")
                return False

            self.spec = DriverSpec(
                class_name=class_name,
                manufacturer=manufacturer,
                model=model,
                comm_type=comm_type,
                description=description,
            )

            logger.info(f"Step 1 complete: {class_name}")
            self.current_step += 1
            return True

        except Exception as e:
            logger.error(f"Step 1 failed: {e}")
            return False

    def step2_communications(
        self, website: str = "", docs_url: str = "", port: str = "", baudrate: str = "9600"
    ) -> bool:
        """Configure communication details.

        Args:
            website: Manufacturer website
            docs_url: Documentation URL
            port: Default port
            baudrate: Default baudrate for serial

        Returns:
            True if step completed successfully
        """
        try:
            if not self.spec:
                logger.error("No spec initialized")
                return False

            self.spec.website = website or ""
            self.spec.docs_url = docs_url or ""
            self.spec.port = port or ""
            self.spec.baudrate = baudrate or "9600"

            logger.info("Step 2 complete: Communications configured")
            self.current_step += 1
            return True

        except Exception as e:
            logger.error(f"Step 2 failed: {e}")
            return False

    def step3_metadata(self) -> bool:
        """Add metadata (metadata already in spec).

        Returns:
            True if step completed successfully
        """
        try:
            if not self.spec:
                logger.error("No spec initialized")
                return False

            logger.info("Step 3 complete: Metadata configured")
            self.current_step += 1
            return True

        except Exception as e:
            logger.error(f"Step 3 failed: {e}")
            return False

    def step4_review(self) -> Dict[str, Any]:
        """Review and prepare for generation.

        Returns:
            Dict with review summary
        """
        if not self.spec:
            return {}

        return {
            "class_name": self.spec.class_name,
            "manufacturer": self.spec.manufacturer,
            "model": self.spec.model,
            "comm_type": self.spec.comm_type,
            "description": self.spec.description,
            "website": self.spec.website,
            "docs_url": self.spec.docs_url,
            "port": self.spec.port,
            "baudrate": self.spec.baudrate,
        }

    def generate_all(self, output_dir: Path) -> Dict[str, Path]:
        """Generate all driver files.

        Args:
            output_dir: Output directory for generated files

        Returns:
            Dict mapping file types to generated file paths
        """
        if not self.spec:
            raise ValueError("No specification set")

        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            generated_files = {}

            # Generate driver class
            driver_code = DriverGenerator.generate_driver_class(self.spec)
            driver_path = output_dir / f"{self.spec.class_name.lower()}.py"
            with open(driver_path, "w") as f:
                f.write(driver_code)
            generated_files["driver"] = driver_path

            # Generate config
            config_code = DriverGenerator.generate_config_file(self.spec, self.spec.class_name)
            config_path = output_dir / f"{self.spec.class_name.lower()}.cfg"
            with open(config_path, "w") as f:
                f.write(config_code)
            generated_files["config"] = config_path

            # Generate tests
            test_code = DriverGenerator.generate_test_class(self.spec)
            test_path = output_dir / f"test_{self.spec.class_name.lower()}.py"
            with open(test_path, "w") as f:
                f.write(test_code)
            generated_files["test"] = test_path

            # Generate README
            readme = DriverGenerator.generate_readme(self.spec)
            readme_path = output_dir / f"{self.spec.class_name.lower()}_README.md"
            with open(readme_path, "w") as f:
                f.write(readme)
            generated_files["readme"] = readme_path

            logger.info(f"Generated driver files in {output_dir}")
            self.current_step += 1

            return generated_files

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise

    def is_complete(self) -> bool:
        """Check if wizard is complete.

        Returns:
            True if all steps are completed
        """
        return self.current_step >= len(self.steps)

    def reset(self) -> None:
        """Reset wizard to initial state."""
        self.spec = None
        self.current_step = 0
        logger.info("Wizard reset to step 1")
