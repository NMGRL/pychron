import json
import os
from dataclasses import dataclass

from pychron.cli_profiles import merge_profiles
from pychron.starter_bundles import bundle_profiles, resolve_bundles

PROFILE_STATE = "bootstrap_profiles.json"


@dataclass(frozen=True)
class ValidationIssue:
    name: str
    status: str
    detail: str
    hint: str = ""


@dataclass(frozen=True)
class RuntimeLayout:
    root: str
    setup_dir: str
    scripts_dir: str
    preferences_dir: str
    data_dir: str
    dvc_dir: str
    repository_dir: str
    appdata_dir: str
    startup_tests: str
    identifiers_file: str
    task_extensions_file: str
    initialization_file: str


def normalize_root(root):
    root = root or "~/Pychron"
    return os.path.normpath(os.path.expanduser(root))


def make_runtime_layout(root):
    root = normalize_root(root)
    setup_dir = os.path.join(root, "setupfiles")
    scripts_dir = os.path.join(root, "scripts")
    appdata_dir = os.path.join(root, ".appdata")
    data_dir = os.path.join(root, "data")
    dvc_dir = os.path.join(data_dir, ".dvc")
    return RuntimeLayout(
        root=root,
        setup_dir=setup_dir,
        scripts_dir=scripts_dir,
        preferences_dir=os.path.join(root, "preferences"),
        data_dir=data_dir,
        dvc_dir=dvc_dir,
        repository_dir=os.path.join(dvc_dir, "repositories"),
        appdata_dir=appdata_dir,
        startup_tests=os.path.join(setup_dir, "startup_tests.yaml"),
        identifiers_file=os.path.join(appdata_dir, "identifiers.yaml"),
        task_extensions_file=os.path.join(appdata_dir, "task_extensions.yaml"),
        initialization_file=os.path.join(setup_dir, "initialization.xml"),
    )


def profile_state_path(root):
    return os.path.join(make_runtime_layout(root).appdata_dir, PROFILE_STATE)


def load_bootstrap_state(root):
    path = profile_state_path(root)
    if not os.path.isfile(path):
        return {}

    try:
        with open(path, "r") as rfile:
            return json.load(rfile)
    except Exception:
        return {}


def combine_profile_inputs(profiles=None, bundles=None, saved_state=None):
    bundle_names = tuple(bundles or saved_state.get("bundles") or ())
    profile_names = list(bundle_profiles(bundle_names))

    explicit_profiles = tuple(profiles or saved_state.get("requested") or ())
    for profile in explicit_profiles:
        if profile not in profile_names:
            profile_names.append(profile)

    return tuple(profile_names), bundle_names


def _bootstrap_hint(root, profiles=None, bundles=None):
    parts = ["pychron-bootstrap", "--root", root]
    for bundle in bundles or ():
        parts.extend(("--bundle", bundle))
    for profile in profiles or ():
        parts.extend(("--profile", profile))
    return "Run `{}` to initialize the expected layout.".format(" ".join(parts))


def validate_runtime_root(root, profiles=None, bundles=None):
    layout = make_runtime_layout(root)
    saved_state = load_bootstrap_state(root)
    requested_profiles, bundle_names = combine_profile_inputs(
        profiles=profiles, bundles=bundles, saved_state=saved_state
    )
    merged = merge_profiles(requested_profiles)
    bundle_specs = resolve_bundles(bundle_names)

    issues = []
    bootstrap_hint = _bootstrap_hint(
        layout.root, profiles=requested_profiles, bundles=bundle_names
    )

    if os.path.isdir(layout.root):
        issues.append(
            ValidationIssue("Path root", "OK", layout.root, ""))
    else:
        issues.append(
            ValidationIssue(
                "Path root",
                "FAIL",
                "{} (missing)".format(layout.root),
                bootstrap_hint,
            )
        )

    base_dirs = (
        ("setupfiles", layout.setup_dir),
        ("scripts", layout.scripts_dir),
        ("preferences", layout.preferences_dir),
        ("data", layout.data_dir),
        ("DVC root", layout.dvc_dir),
        ("repositories", layout.repository_dir),
        ("appdata", layout.appdata_dir),
    )
    for label, directory in base_dirs:
        if os.path.isdir(directory):
            issues.append(ValidationIssue("Path {}".format(label), "OK", directory))
        else:
            issues.append(
                ValidationIssue(
                    "Path {}".format(label),
                    "FAIL",
                    "{} (missing)".format(directory),
                    bootstrap_hint,
                )
            )

    file_checks = (
        ("initialization.xml", layout.initialization_file),
        ("startup_tests.yaml", layout.startup_tests),
        ("identifiers.yaml", layout.identifiers_file),
        ("task_extensions.yaml", layout.task_extensions_file),
    )
    for label, path in file_checks:
        if os.path.isfile(path):
            issues.append(ValidationIssue("File {}".format(label), "OK", path))
        else:
            issues.append(
                ValidationIssue(
                    "File {}".format(label),
                    "WARN",
                    "{} (missing)".format(path),
                    bootstrap_hint,
                )
            )

    if bundle_specs:
        detail = ", ".join(
            "{}@{}".format(bundle.name, bundle.version) for bundle in bundle_specs
        )
        issues.append(ValidationIssue("Bundles", "OK", detail))

    if merged.resolved:
        issues.append(
            ValidationIssue("Profiles", "OK", ", ".join(merged.resolved))
        )

    for directory in merged.directories:
        full_path = os.path.join(layout.root, directory)
        if os.path.isdir(full_path):
            issues.append(
                ValidationIssue("Profile dir {}".format(directory), "OK", full_path)
            )
        else:
            issues.append(
                ValidationIssue(
                    "Profile dir {}".format(directory),
                    "FAIL",
                    "{} (missing for selected profile)".format(full_path),
                    bootstrap_hint,
                )
            )

    for file_spec in merged.required_files:
        full_path = os.path.join(layout.root, file_spec.path)
        if os.path.isfile(full_path):
            issues.append(
                ValidationIssue("Profile file {}".format(file_spec.path), "OK", full_path)
            )
        else:
            issues.append(
                ValidationIssue(
                    "Profile file {}".format(file_spec.path),
                    "FAIL",
                    "{} (missing for selected profile)".format(full_path),
                    bootstrap_hint,
                )
            )

    for file_spec in merged.optional_files:
        full_path = os.path.join(layout.root, file_spec.path)
        if os.path.isfile(full_path):
            issues.append(
                ValidationIssue("Profile file {}".format(file_spec.path), "OK", full_path)
            )
        else:
            issues.append(
                ValidationIssue(
                    "Profile file {}".format(file_spec.path),
                    "WARN",
                    "{} (recommended by selected profile)".format(full_path),
                    "Import a site bundle or create this file when the workflow needs it.",
                )
            )

    if not saved_state and not bundle_specs and not merged.resolved:
        issues.append(
            ValidationIssue(
                "Bootstrap state",
                "WARN",
                "{} (missing)".format(profile_state_path(layout.root)),
                "Run `pychron-bootstrap` so the install records its selected profiles.",
            )
        )
    elif saved_state:
        details = []
        if saved_state.get("bundles"):
            details.append("bundles={}".format(",".join(saved_state["bundles"])))
        if saved_state.get("requested"):
            details.append("profiles={}".format(",".join(saved_state["requested"])))
        if saved_state.get("source_profiles"):
            details.append(
                "source_profiles={}".format(",".join(saved_state["source_profiles"]))
            )
        issues.append(
            ValidationIssue(
                "Bootstrap state",
                "OK",
                "; ".join(details) or profile_state_path(layout.root),
            )
        )

    return issues
