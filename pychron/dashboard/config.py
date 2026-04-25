import os
from dataclasses import asdict, dataclass, field

from pychron.core.xml.xml_parser import XMLParser
from pychron.core.yaml import yload
from pychron.dashboard.constants import CRITICAL, WARNING
from pychron.core.helpers.strtools import to_bool


class DashboardConfigError(Exception):
    def __init__(self, issues):
        self.issues = tuple(issues)
        super(DashboardConfigError, self).__init__("\n".join(self.issues))


@dataclass(frozen=True)
class DashboardConditionalSpec:
    severity: int
    teststr: str
    nfail: int = 1
    script: str = ""
    emails: str = ""


@dataclass(frozen=True)
class DashboardValueSpec:
    name: str
    tag: str
    func_name: str
    period: object
    enabled: bool
    threshold: float
    units: str
    timeout: float
    record: bool
    bindname: str = ""
    conditionals: tuple[DashboardConditionalSpec, ...] = ()


@dataclass(frozen=True)
class DashboardDeviceSpec:
    name: str
    device: str
    enabled: bool
    values: tuple[DashboardValueSpec, ...] = ()


@dataclass(frozen=True)
class DashboardConfig:
    source_path: str
    port: int = 8100
    devices: tuple[DashboardDeviceSpec, ...] = ()

    def as_payload(self):
        return {
            "source_path": self.source_path,
            "port": self.port,
            "devices": [asdict(device) for device in self.devices],
        }


def _get_xml_value(elem, tag, default):
    ret = default
    found = elem.find(tag)
    if found is not None and found.text is not None:
        ret = found.text.strip()
    return ret


def _normalize_period(period, issues, label):
    if period == "on_change":
        return period

    try:
        value = float(period)
    except (TypeError, ValueError):
        issues.append("{} has invalid period '{}'".format(label, period))
        return 60

    if value <= 0:
        issues.append("{} has non-positive period '{}'".format(label, period))
        return 60

    return int(value) if int(value) == value else value


def _normalize_nfail(raw):
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 1


def _normalize_conditionals(entries, issues, value_label, script_validator=None):
    specs = []
    for severity, payload in entries:
        teststr = payload.get("teststr", "").strip()
        if not teststr:
            issues.append("{} has a conditional without a test string".format(value_label))
            continue

        script = (payload.get("script") or "").strip()
        if script and script_validator and not script_validator(script):
            issues.append(
                '{} references invalid script "{}"'.format(value_label, script)
            )
            continue

        specs.append(
            DashboardConditionalSpec(
                severity=severity,
                teststr=teststr,
                nfail=_normalize_nfail(payload.get("nfail", 1)),
                script=script,
                emails=(payload.get("emails") or "").strip(),
            )
        )
    return tuple(specs)


def _make_value_spec(device_name, payload, issues, script_validator=None):
    name = str(payload.get("name", "")).strip()
    label = "{} value".format(device_name)
    if not name:
        issues.append("{} is missing a name".format(label))
        return None

    tag = payload.get("tag") or "<{},{}>".format(device_name, name)
    tag = str(tag).strip()
    if not tag:
        issues.append("{} is missing a tag".format(label))
        return None

    func_name = str(payload.get("func_name") or payload.get("func") or "get").strip()
    if not func_name:
        issues.append("{} is missing a func name".format(label))
        return None

    period = _normalize_period(payload.get("period", 60), issues, "{}.{}".format(device_name, name))
    conditionals = _normalize_conditionals(
        payload.get("conditionals", ()),
        issues,
        "{}.{}".format(device_name, name),
        script_validator=script_validator,
    )

    try:
        threshold = float(payload.get("threshold", payload.get("change_threshold", 1e-20)))
    except (TypeError, ValueError):
        issues.append("{}.{} has invalid change threshold".format(device_name, name))
        threshold = 1e-20

    try:
        timeout = float(payload.get("timeout", 60))
    except (TypeError, ValueError):
        issues.append("{}.{} has invalid timeout".format(device_name, name))
        timeout = 60

    return DashboardValueSpec(
        name=name,
        tag=tag,
        func_name=func_name,
        period=period,
        enabled=to_bool(payload.get("enabled", False)),
        threshold=threshold,
        units=str(payload.get("units", "") or "").strip(),
        timeout=timeout,
        record=to_bool(payload.get("record", False)),
        bindname=str(payload.get("bindname") or payload.get("bind") or "").strip(),
        conditionals=conditionals,
    )


def _normalize_device_spec(payload, issues, script_validator=None):
    name = str(payload.get("name", "")).strip()
    if not name:
        issues.append("Dashboard device is missing a display name")
        return None

    hardware_name = str(payload.get("device", "")).strip()
    if not hardware_name:
        issues.append('Dashboard device "{}" is missing the internal device name'.format(name))
        return None

    values = []
    for value_payload in payload.get("values", ()):
        spec = _make_value_spec(
            name, value_payload, issues, script_validator=script_validator
        )
        if spec is not None:
            values.append(spec)

    if not values:
        issues.append('Dashboard device "{}" has no valid values'.format(name))

    return DashboardDeviceSpec(
        name=name,
        device=hardware_name,
        enabled=to_bool(payload.get("enabled", payload.get("use", True))),
        values=tuple(values),
    )


def _normalize_devices(device_payloads, issues, script_validator=None):
    devices = []
    tags = set()
    for device_payload in device_payloads:
        spec = _normalize_device_spec(
            device_payload, issues, script_validator=script_validator
        )
        if spec is None:
            continue

        for value in spec.values:
            if value.tag in tags:
                issues.append('Duplicate dashboard tag "{}"'.format(value.tag))
            else:
                tags.add(value.tag)
        devices.append(spec)
    return tuple(devices)


def _load_yaml_config(path, issues, script_validator=None):
    payload = yload(path, default=None)
    if payload is None:
        raise DashboardConfigError(
            ['Failed to load dashboard configuration from "{}"'.format(path)]
        )

    if isinstance(payload, dict):
        port = payload.get("port", 8100)
        device_payloads = payload.get("devices", ())
    elif isinstance(payload, list):
        port = 8100
        device_payloads = payload
    else:
        raise DashboardConfigError(
            ['Unsupported dashboard YAML structure in "{}"'.format(path)]
        )

    devices = _normalize_devices(
        device_payloads, issues, script_validator=script_validator
    )
    return DashboardConfig(source_path=path, port=int(port), devices=devices)


def _extract_xml_conditionals(value_elem):
    entries = []
    conditionals = value_elem.find("conditionals")
    if conditionals is None:
        return entries

    for tag, severity in (("warn", WARNING), ("critical", CRITICAL)):
        for elem in conditionals.findall(tag):
            payload = {
                "teststr": (elem.text or "").strip(),
                "nfail": _get_xml_value(elem, "nfail", 1),
                "script": _get_xml_value(elem, "script", ""),
                "emails": _get_xml_value(elem, "emails", ""),
            }
            entries.append((severity, payload))
    return entries


def _load_xml_config(path, issues, script_validator=None):
    parser = XMLParser(path)
    if parser._syntax_error:
        raise DashboardConfigError(
            ['{} has invalid XML: {}'.format(path, parser._syntax_error)]
        )

    port = 8100
    port_elements = parser.get_elements("port")
    if port_elements:
        try:
            port = int(port_elements[0].text.strip())
        except (AttributeError, TypeError, ValueError):
            issues.append('{} has invalid port "{}"'.format(path, port_elements[0].text))

    device_payloads = []
    for device_elem in parser.get_elements("device"):
        value_payloads = []
        for value_elem in device_elem.findall("value"):
            value_payloads.append(
                {
                    "name": (value_elem.text or "").strip(),
                    "func_name": _get_xml_value(value_elem, "func", "get"),
                    "period": _get_xml_value(value_elem, "period", 60),
                    "enabled": _get_xml_value(value_elem, "enabled", False),
                    "record": _get_xml_value(value_elem, "record", False),
                    "timeout": _get_xml_value(value_elem, "timeout", 60),
                    "change_threshold": _get_xml_value(
                        value_elem, "change_threshold", 1e-20
                    ),
                    "units": _get_xml_value(value_elem, "units", ""),
                    "bindname": _get_xml_value(value_elem, "bind", ""),
                    "conditionals": _extract_xml_conditionals(value_elem),
                }
            )

        device_payloads.append(
            {
                "name": (device_elem.text or "").strip(),
                "device": _get_xml_value(device_elem, "name", ""),
                "enabled": _get_xml_value(device_elem, "use", True),
                "values": value_payloads,
            }
        )

    devices = _normalize_devices(
        device_payloads, issues, script_validator=script_validator
    )
    return DashboardConfig(source_path=path, port=port, devices=devices)


def load_dashboard_config(root_dir, script_validator=None):
    setup_dir = os.path.join(root_dir, "setupfiles")
    yaml_path = os.path.join(setup_dir, "dashboard.yaml")
    xml_path = os.path.join(setup_dir, "dashboard.xml")
    issues = []

    if os.path.isfile(yaml_path):
        config = _load_yaml_config(
            yaml_path, issues, script_validator=script_validator
        )
    elif os.path.isfile(xml_path):
        config = _load_xml_config(
            xml_path, issues, script_validator=script_validator
        )
    else:
        raise DashboardConfigError(
            [
                'No dashboard configuration found. Expected "{}" or "{}"'.format(
                    yaml_path, xml_path
                )
            ]
        )

    if not config.devices:
        issues.append(
            'Dashboard configuration "{}" does not define any valid devices'.format(
                config.source_path
            )
        )

    if issues:
        raise DashboardConfigError(issues)

    return config
