import json
import os
from dataclasses import dataclass

from pychron.paths import paths

PROFILE_STATE = "bootstrap_profiles.json"


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
    simple_ui_file: str
    edit_ui_defaults: str


@dataclass(frozen=True)
class ManagedRuntimeFile:
    label: str
    path: str
    default_text: str | None = None
    required: bool = True
    managed_by: str = "bootstrap"


def normalize_root(root):
    root = root or "~/Pychron"
    return os.path.normpath(os.path.expanduser(root))


def make_runtime_layout(root):
    root = normalize_root(root)
    setup_dir = os.path.join(root, "setupfiles")
    appdata_dir = os.path.join(root, ".appdata")
    return RuntimeLayout(
        root=root,
        setup_dir=setup_dir,
        scripts_dir=os.path.join(root, "scripts"),
        preferences_dir=os.path.join(root, "preferences"),
        data_dir=os.path.join(root, "data"),
        dvc_dir=os.path.join(root, "data", ".dvc"),
        repository_dir=os.path.join(root, "data", ".dvc", "repositories"),
        appdata_dir=appdata_dir,
        startup_tests=os.path.join(setup_dir, "startup_tests.yaml"),
        identifiers_file=os.path.join(appdata_dir, "identifiers.yaml"),
        task_extensions_file=os.path.join(appdata_dir, "task_extensions.yaml"),
        initialization_file=os.path.join(setup_dir, "initialization.xml"),
        simple_ui_file=os.path.join(appdata_dir, "simple_ui.yaml"),
        edit_ui_defaults=os.path.join(appdata_dir, "edit_ui.yaml"),
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


def base_runtime_directories(layout):
    return (
        ("setupfiles", layout.setup_dir),
        ("scripts", layout.scripts_dir),
        ("preferences", layout.preferences_dir),
        ("data", layout.data_dir),
        ("DVC root", layout.dvc_dir),
        ("repositories", layout.repository_dir),
        ("appdata", layout.appdata_dir),
    )


def managed_runtime_files(layout):
    from pychron.file_defaults import (
        DEFAULT_INITIALIZATION,
        DEFAULT_STARTUP_TESTS,
        EDIT_UI_DEFAULT,
        IDENTIFIERS_DEFAULT,
        SIMPLE_UI_DEFAULT,
        TASK_EXTENSION_DEFAULT,
    )

    return (
        ManagedRuntimeFile(
            "initialization.xml",
            layout.initialization_file,
            default_text=DEFAULT_INITIALIZATION,
        ),
        ManagedRuntimeFile(
            "startup_tests.yaml",
            layout.startup_tests,
            default_text=DEFAULT_STARTUP_TESTS,
        ),
        ManagedRuntimeFile(
            "identifiers.yaml",
            layout.identifiers_file,
            default_text=IDENTIFIERS_DEFAULT,
        ),
        ManagedRuntimeFile(
            "task_extensions.yaml",
            layout.task_extensions_file,
            default_text=TASK_EXTENSION_DEFAULT,
        ),
        ManagedRuntimeFile(
            "simple_ui.yaml",
            layout.simple_ui_file,
            default_text=SIMPLE_UI_DEFAULT,
            required=False,
        ),
        ManagedRuntimeFile(
            "edit_ui.yaml",
            layout.edit_ui_defaults,
            default_text=EDIT_UI_DEFAULT,
            required=False,
        ),
    )


def prepare_runtime_root(root, appname=None, write_defaults=True):
    root = normalize_root(root)
    layout = make_runtime_layout(root)

    if appname:
        from pychron.environment.util import set_application_home

        set_application_home(appname, root)

    paths.build(root)

    created = []
    if write_defaults:
        for spec in managed_runtime_files(layout):
            if spec.default_text is None or os.path.isfile(spec.path):
                continue

            parent = os.path.dirname(spec.path)
            if parent:
                os.makedirs(parent, exist_ok=True)

            with open(spec.path, "w") as wfile:
                wfile.write(spec.default_text)
            created.append(spec.path)

    return layout, created


def save_bootstrap_state(
    root,
    merged,
    bundles=None,
    source_profiles=None,
):
    layout = make_runtime_layout(root)
    payload = {
        "layout_version": 2,
        "root": layout.root,
        "bundles": list(bundles or ()),
        "requested": list(merged.requested),
        "resolved": list(merged.resolved),
        "source_profiles": list(source_profiles or ()),
        "managed_directories": list(merged.directories),
        "managed_files": [
            {
                "path": file_spec.path,
                "required": file_spec.required,
                "managed_by": "bootstrap" if file_spec.default_text is not None else "lab",
            }
            for file_spec in merged.required_files + merged.optional_files
        ],
    }
    os.makedirs(os.path.dirname(profile_state_path(layout.root)), exist_ok=True)
    with open(profile_state_path(layout.root), "w") as wfile:
        json.dump(payload, wfile, indent=2, sort_keys=True)
