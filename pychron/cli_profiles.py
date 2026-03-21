import os
from dataclasses import dataclass, field

EXPERIMENT_DEFAULTS = """
columns:
  - Labnumber
  - Aliquot
  - Sample
  - Position
  - Extract
  - Units
  - Duration (s)
  - Cleanup (s)
  - Beam (mm)
  - Pattern
  - Extraction
  - Measurement
  - Conditionals
  - Comment
"""

FLUX_CONSTANTS_DEFAULT = """
# This is an example flux file. Add additional decay_constant and monitor_age pairs here
"FC MIN":
  lambda_ec: [5.80e-11, 0]
  lambda_b: [4.884e-10, 0]
  monitor_age: 28.201
"FC SJ":
  lambda_ec: [5.81e-11, 0]
  lambda_b: [4.962e-10, 0]
  monitor_age: 28.02
"""

RATIO_CHANGE_DETECTION = """
# - ratio: Ar40/Ar36
#   nanalyses: 5
#   threshold: 1
#   analysis_type: air
#   failure_count: 2
#   consecutive_failure: True
"""

PLACEHOLDER_SYSTEM_HEALTH = "# Add system health checks for this installation.\n"
PLACEHOLDER_VALID_PI_NAMES = "# Add valid PI names, one per line or as YAML entries.\n"
PLACEHOLDER_USERS = "# Add users for this installation.\n"


@dataclass(frozen=True)
class ProfileFile:
    path: str
    default_text: str | None = None
    required: bool = True


@dataclass(frozen=True)
class ProfileSpec:
    name: str
    description: str
    includes: tuple[str, ...] = ()
    directories: tuple[str, ...] = ()
    files: tuple[ProfileFile, ...] = ()


PROFILES = {
    "data-reduction": ProfileSpec(
        name="data-reduction",
        description="Pipeline/data-reduction workstation with reduction defaults.",
        directories=(
            "setupfiles/pipeline",
            "scripts/pipeline",
        ),
        files=(
            ProfileFile("setupfiles/flux_constants.yaml", FLUX_CONSTANTS_DEFAULT),
            ProfileFile("setupfiles/experiment_defaults.yaml", EXPERIMENT_DEFAULTS),
        ),
    ),
    "experiment": ProfileSpec(
        name="experiment",
        description="Automated experiment queue execution and script authoring.",
        directories=(
            "setupfiles/blocks",
            "setupfiles/monitors",
            "setupfiles/pipeline",
            "setupfiles/incremental_heat_templates",
            "scripts/conditionals",
            "scripts/extraction",
            "scripts/measurement",
            "scripts/pipeline",
            "scripts/post_equilibration",
            "scripts/post_measurement",
            "scripts/procedures",
            "scripts/spectrometer",
            "scripts/backup",
            "scripts/syn_extraction",
            "scripts/truncation",
            "scripts/measurement/fits",
            "scripts/measurement/hops",
        ),
        files=(
            ProfileFile("setupfiles/experiment_defaults.yaml", EXPERIMENT_DEFAULTS),
            ProfileFile(
                "setupfiles/ratio_change_detection.yaml",
                RATIO_CHANGE_DETECTION,
                required=False,
            ),
        ),
    ),
    "extraction-line": ProfileSpec(
        name="extraction-line",
        description="Extraction line control and monitor configuration.",
        directories=(
            "setupfiles/blocks",
            "setupfiles/canvas2D",
            "setupfiles/devices",
            "setupfiles/extractionline",
            "setupfiles/monitors",
            "setupfiles/patterns",
            "setupfiles/tray_maps",
        ),
    ),
    "laser-co2": ProfileSpec(
        name="laser-co2",
        description="CO2 laser workstation layout derived from common consulting setups.",
        directories=(
            "setupfiles/bakeout_configurations",
            "setupfiles/canvas2D",
            "setupfiles/canvas3D",
            "setupfiles/formatting",
            "setupfiles/heating_schedules",
            "setupfiles/jogs",
            "setupfiles/patterns",
            "setupfiles/tray_maps",
            "setupfiles/irradiation_tray_maps",
        ),
        files=(
            ProfileFile(
                "setupfiles/pid_degasser.yaml",
                "# CO2 PID degasser settings.\n",
                required=False,
            ),
        ),
    ),
    "laser-diode": ProfileSpec(
        name="laser-diode",
        description="Diode laser workstation layout derived from common consulting setups.",
        directories=(
            "setupfiles/bakeout_configurations",
            "setupfiles/canvas2D",
            "setupfiles/formatting",
            "setupfiles/heating_schedules",
            "setupfiles/jogs",
            "setupfiles/patterns",
            "setupfiles/tray_maps",
            "setupfiles/irradiation_tray_maps",
        ),
        files=(
            ProfileFile(
                "setupfiles/pid_degasser.yaml",
                "# Diode PID degasser settings.\n",
                required=False,
            ),
        ),
    ),
    "spectrometer": ProfileSpec(
        name="spectrometer",
        description="Mass spectrometer defaults shared by Argus/Helix/NGX style setups.",
        directories=(
            "setupfiles/monitors",
            "setupfiles/spectrometer",
        ),
        files=(
            ProfileFile("setupfiles/flux_constants.yaml", FLUX_CONSTANTS_DEFAULT),
            ProfileFile(
                "setupfiles/ratio_change_detection.yaml",
                RATIO_CHANGE_DETECTION,
                required=False,
            ),
            ProfileFile(
                "setupfiles/system_health.yaml",
                PLACEHOLDER_SYSTEM_HEALTH,
                required=False,
            ),
            ProfileFile(
                "setupfiles/valid_pi_names.yaml",
                PLACEHOLDER_VALID_PI_NAMES,
                required=False,
            ),
            ProfileFile("setupfiles/users.yaml", PLACEHOLDER_USERS, required=False),
        ),
    ),
    "spectrometer-ngx": ProfileSpec(
        name="spectrometer-ngx",
        description="NGX-specific spectrometer support files and actuator/controller stubs.",
        includes=("spectrometer",),
        files=(
            ProfileFile(
                "setupfiles/NGXGPActuator.cfg",
                "[Communicator]\nkind = ethernet\n",
                required=False,
            ),
            ProfileFile(
                "setupfiles/spectrometer_microcontroller.cfg",
                "[Communicator]\nkind = ethernet\n",
                required=False,
            ),
            ProfileFile(
                "setupfiles/switch_controller.cfg",
                "[Communicator]\nkind = ethernet\n",
                required=False,
            ),
        ),
    ),
    "chromium": ProfileSpec(
        name="chromium",
        description="Chromium laser client/stage profile.",
        directories=(
            "setupfiles/canvas2D",
            "setupfiles/devices",
            "setupfiles/patterns",
            "setupfiles/tray_maps",
        ),
    ),
    "ngx": ProfileSpec(
        name="ngx",
        description="Alias for spectrometer-ngx.",
        includes=("spectrometer-ngx",),
    ),
    "co2": ProfileSpec(
        name="co2",
        description="Alias for laser-co2.",
        includes=("laser-co2",),
    ),
    "diode": ProfileSpec(
        name="diode",
        description="Alias for laser-diode.",
        includes=("laser-diode",),
    ),
    "chromiumco2": ProfileSpec(
        name="chromiumco2",
        description="Composite Chromium + CO2 laser + experiment workstation profile.",
        includes=("experiment", "extraction-line", "chromium", "laser-co2"),
    ),
    "chromiumdiode": ProfileSpec(
        name="chromiumdiode",
        description="Composite Chromium + diode laser + experiment workstation profile.",
        includes=("experiment", "extraction-line", "chromium", "laser-diode"),
    ),
}


def available_profile_names():
    return tuple(sorted(PROFILES))


def normalize_profile_name(name):
    return name.strip().lower()


def _resolve_profile(name, seen, ordered):
    normalized = normalize_profile_name(name)
    if normalized in seen:
        return

    try:
        spec = PROFILES[normalized]
    except KeyError as exc:
        raise KeyError('Unknown profile "{}"'.format(name)) from exc

    seen.add(normalized)
    for include in spec.includes:
        _resolve_profile(include, seen, ordered)
    ordered.append(spec)


def resolve_profiles(names):
    seen = set()
    ordered = []
    for name in names or ():
        _resolve_profile(name, seen, ordered)
    return ordered


@dataclass
class MergedProfile:
    requested: tuple[str, ...] = ()
    resolved: tuple[str, ...] = ()
    directories: tuple[str, ...] = ()
    required_files: tuple[ProfileFile, ...] = ()
    optional_files: tuple[ProfileFile, ...] = ()
    descriptions: dict[str, str] = field(default_factory=dict)


def merge_profiles(names):
    resolved_specs = resolve_profiles(names)
    directories = []
    required_files = []
    optional_files = []
    seen_dirs = set()
    seen_required = set()
    seen_optional = set()

    for spec in resolved_specs:
        for directory in spec.directories:
            key = os.path.normpath(directory)
            if key not in seen_dirs:
                seen_dirs.add(key)
                directories.append(directory)

        for file_spec in spec.files:
            key = os.path.normpath(file_spec.path)
            if file_spec.required:
                if key not in seen_required:
                    seen_required.add(key)
                    required_files.append(file_spec)
            elif key not in seen_optional:
                seen_optional.add(key)
                optional_files.append(file_spec)

    return MergedProfile(
        requested=tuple(normalize_profile_name(name) for name in names or ()),
        resolved=tuple(spec.name for spec in resolved_specs),
        directories=tuple(directories),
        required_files=tuple(required_files),
        optional_files=tuple(optional_files),
        descriptions={spec.name: spec.description for spec in resolved_specs},
    )
