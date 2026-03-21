import json
import os
import platform
import zipfile
from dataclasses import dataclass
from datetime import datetime, UTC

from pychron.cli_profiles import merge_profiles

CONFIG_BUNDLE_VERSION = 1
CONFIG_BUNDLE_DIRS = ("setupfiles", "scripts", "preferences", "queue_conditionals")
OPTIONAL_CONFIG_BUNDLE_DIRS = (".appdata",)

PROFILE_EXTRA_MAP = {
    "extraction-line": ("hardware",),
    "laser-co2": ("laser",),
    "laser-diode": ("laser",),
    "spectrometer": ("hardware",),
    "spectrometer-ngx": ("spectrometer-ngx",),
}


@dataclass(frozen=True)
class InstallPlan:
    platform_name: str
    python_version: str
    requested_profiles: tuple[str, ...]
    resolved_profiles: tuple[str, ...]
    extras: tuple[str, ...]
    commands: tuple[str, ...]
    notes: tuple[str, ...]


def build_install_plan(profiles=None, root="~/Pychron", python_version="3.12"):
    merged = merge_profiles(profiles or ())
    extras = []
    seen = set()
    for profile in merged.resolved:
        for extra in PROFILE_EXTRA_MAP.get(profile, ()):
            if extra not in seen:
                seen.add(extra)
                extras.append(extra)

    sync_cmd = "uv sync"
    if extras:
        sync_cmd = "{} {}".format(
            sync_cmd, " ".join("--extra {}".format(extra) for extra in extras)
        )

    profile_args = " ".join(
        "--profile {}".format(profile) for profile in merged.requested
    )
    bootstrap_cmd = "pychron-bootstrap --root {}".format(root)
    if profile_args:
        bootstrap_cmd = "{} {}".format(bootstrap_cmd, profile_args)

    commands = (
        "uv venv --python {}".format(python_version),
        sync_cmd,
        bootstrap_cmd,
        "pychron-doctor --root {}".format(root),
    )

    system = platform.system()
    notes = [
        "Use Python {} for supported installs.".format(python_version),
        "Profile selection controls bootstrap layout; extras add optional "
        "comms/runtime dependencies.",
    ]
    if system == "Darwin":
        notes.append(
            "macOS installs should verify Qt platform plugin loading and app nap settings."
        )
    elif system == "Windows":
        notes.append(
            "Windows installs should verify serial permissions, path length, "
            "and antivirus exclusions."
        )
    elif system == "Linux":
        notes.append(
            "Linux installs should verify Qt/xcb libraries and serial device group membership."
        )

    return InstallPlan(
        platform_name=system,
        python_version=python_version,
        requested_profiles=merged.requested,
        resolved_profiles=merged.resolved,
        extras=tuple(extras),
        commands=commands,
        notes=tuple(notes),
    )


def _iter_bundle_paths(root, include_appdata=False):
    root = os.path.expanduser(root)
    rels = list(CONFIG_BUNDLE_DIRS)
    if include_appdata:
        rels.extend(OPTIONAL_CONFIG_BUNDLE_DIRS)

    for rel in rels:
        path = os.path.join(root, rel)
        if os.path.exists(path):
            yield rel, path


def export_config_bundle(root, output_path, include_appdata=False, overwrite=False):
    root = os.path.expanduser(root)
    output_path = os.path.expanduser(output_path)
    if os.path.exists(output_path) and not overwrite:
        raise FileExistsError(output_path)

    exported = []
    manifest = {
        "format_version": CONFIG_BUNDLE_VERSION,
        "created_at": datetime.now(UTC).isoformat(),
        "root": root,
        "included": [],
    }

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel, path in _iter_bundle_paths(root, include_appdata=include_appdata):
            manifest["included"].append(rel)
            if os.path.isfile(path):
                arcname = rel
                zf.write(path, arcname)
                exported.append(arcname)
                continue

            for current_root, dirs, files in os.walk(path):
                dirs.sort()
                files.sort()
                for filename in files:
                    src = os.path.join(current_root, filename)
                    arcname = os.path.relpath(src, root)
                    zf.write(src, arcname)
                    exported.append(arcname)

        zf.writestr("manifest.json", json.dumps(manifest, indent=2, sort_keys=True))

    return exported


def import_config_bundle(root, archive_path, overwrite=False):
    root = os.path.expanduser(root)
    archive_path = os.path.expanduser(archive_path)
    extracted = []
    skipped = []

    with zipfile.ZipFile(archive_path, "r") as zf:
        for member in zf.infolist():
            if member.filename.endswith("/") or member.filename == "manifest.json":
                continue

            destination = os.path.normpath(os.path.join(root, member.filename))
            if not destination.startswith(os.path.normpath(root)):
                skipped.append(member.filename)
                continue

            os.makedirs(os.path.dirname(destination), exist_ok=True)
            if os.path.exists(destination) and not overwrite:
                skipped.append(member.filename)
                continue

            with zf.open(member, "r") as rfile, open(destination, "wb") as wfile:
                wfile.write(rfile.read())
            extracted.append(member.filename)

    return extracted, skipped
