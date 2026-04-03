import os
import tempfile
import unittest

try:
    from pychron.dashboard.config import DashboardConfigError, load_dashboard_config
except ModuleNotFoundError as exc:
    load_dashboard_config = None
    DashboardConfigError = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


XML_CONFIG = """<root>
  <port>8102</port>
  <device>Env
    <use>true</use>
    <name>environmental_monitor</name>
    <value>temperature
      <func>get_temperature</func>
      <period>10</period>
      <enabled>true</enabled>
      <units>C</units>
    </value>
  </device>
</root>
"""


YAML_CONFIG = """
port: 8102
devices:
  - name: Env
    enabled: true
    device: environmental_monitor
    values:
      - name: temperature
        func: get_temperature
        period: 10
        enabled: true
        units: C
"""


@unittest.skipIf(_IMPORT_ERROR is not None, str(_IMPORT_ERROR))
class DashboardConfigTestCase(unittest.TestCase):
    def test_xml_and_yaml_normalize_equally(self):
        with tempfile.TemporaryDirectory() as root:
            setup_dir = os.path.join(root, "setupfiles")
            os.makedirs(setup_dir)

            xml_path = os.path.join(setup_dir, "dashboard.xml")
            with open(xml_path, "w") as wfile:
                wfile.write(XML_CONFIG)
            xml_config = load_dashboard_config(root)

            os.remove(xml_path)
            with open(os.path.join(setup_dir, "dashboard.yaml"), "w") as wfile:
                wfile.write(YAML_CONFIG)
            yaml_config = load_dashboard_config(root)

            self.assertEqual(xml_config.port, yaml_config.port)
            self.assertEqual(xml_config.devices[0].name, yaml_config.devices[0].name)
            self.assertEqual(
                xml_config.devices[0].values[0].tag,
                yaml_config.devices[0].values[0].tag,
            )

    def test_duplicate_tags_raise_error(self):
        with tempfile.TemporaryDirectory() as root:
            setup_dir = os.path.join(root, "setupfiles")
            os.makedirs(setup_dir)
            with open(os.path.join(setup_dir, "dashboard.yaml"), "w") as wfile:
                wfile.write(
                    """
devices:
  - name: Env
    enabled: true
    device: environmental_monitor
    values:
      - name: temperature
        tag: <Env,temp>
        func: get_temperature
        period: 10
        enabled: true
      - name: humidity
        tag: <Env,temp>
        func: get_humidity
        period: 10
        enabled: true
"""
                )

            with self.assertRaises(DashboardConfigError):
                load_dashboard_config(root)


if __name__ == "__main__":
    unittest.main()
