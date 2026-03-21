import importlib
import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass

import typer

from pychron.cli_profiles import PROFILES, available_profile_names, merge_profiles
from pychron.install_support import (
    build_install_plan,
    export_config_bundle,
    import_config_bundle,
)
from pychron.paths import paths

DEFAULT_ROOT = "~/Pychron"
REQUIRED_PYTHON_PREFIX = "3.12"
CHECK_MARK = "OK"
WARN_MARK = "WARN"
FAIL_MARK = "FAIL"
PROFILE_STATE = "bootstrap_profiles.json"
SKIP_SOURCE_NAMES = {".DS_Store"}
SKIP_SOURCE_PREFIXES = ("~", "~~")
SKIP_SOURCE_SUFFIXES = (".bk", ".orig")

app = typer.Typer(
    help="Pychron installation and environment utilities.",
    no_args_is_help=True,
    add_completion=False,
)


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str


def _normalize_root(root):
    root = root or DEFAULT_ROOT
    return os.path.expanduser(root)


def _format_result(result):
    return "[{}] {}: {}".format(result.status, result.name, result.detail)


def _echo_results(results):
    for result in results:
        typer.echo(_format_result(result))


def _profile_state_path():
    return os.path.join(paths.appdata_dir, PROFILE_STATE)


def _normalize_profiles(profiles):
    return [profile for profile in (profiles or []) if profile]


def _load_saved_bootstrap_state():
    path = _profile_state_path()
    if not os.path.isfile(path):
        return {}

    try:
        with open(path, "r") as rfile:
            return json.load(rfile)
    except Exception:
        return {}


def _save_bootstrap_state(merged, source_profiles=None):
    path = _profile_state_path()
    payload = {
        "requested": list(merged.requested),
        "resolved": list(merged.resolved),
        "source_profiles": list(source_profiles or ()),
    }
    with open(path, "w") as wfile:
        json.dump(payload, wfile, indent=2, sort_keys=True)


def _required_module_checks():
    modules = (
        ("yaml", "PyYAML"),
        ("git", "GitPython"),
        ("numpy", "NumPy"),
        ("traits", "Traits"),
        ("traitsui", "TraitsUI"),
        ("pyface", "Pyface"),
        ("PyQt5", "PyQt5"),
        ("sqlalchemy", "SQLAlchemy"),
        ("requests", "Requests"),
        ("typer", "Typer"),
    )
    results = []
    for module_name, label in modules:
        try:
            importlib.import_module(module_name)
            results.append(CheckResult(label, CHECK_MARK, "import ok"))
        except Exception as exc:
            results.append(CheckResult(label, FAIL_MARK, str(exc)))
    return results


def _python_check():
    version = "{}.{}.{}".format(*sys.version_info[:3])
    status = CHECK_MARK if version.startswith(REQUIRED_PYTHON_PREFIX) else WARN_MARK
    detail = "running {}".format(version)
    if status != CHECK_MARK:
        detail = "{}; expected {}.*".format(detail, REQUIRED_PYTHON_PREFIX)
    return CheckResult("Python", status, detail)


def _git_check():
    git_path = shutil.which("git")
    if not git_path:
        return CheckResult("Git", FAIL_MARK, "git executable not found on PATH")

    try:
        proc = subprocess.run(
            [git_path, "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        detail = proc.stdout.strip() or proc.stderr.strip() or git_path
        return CheckResult("Git", CHECK_MARK, detail)
    except Exception as exc:
        return CheckResult("Git", FAIL_MARK, str(exc))


def _ensure_directory(path):
    os.makedirs(path, exist_ok=True)


def _write_file_if_missing(path, text):
    if os.path.isfile(path):
        return False

    parent = os.path.dirname(path)
    if parent:
        _ensure_directory(parent)

    with open(path, "w") as wfile:
        wfile.write(text or "")
    return True


def _should_skip_source_name(name):
    if name in SKIP_SOURCE_NAMES:
        return True
    if name.startswith(SKIP_SOURCE_PREFIXES):
        return True
    if name.endswith(SKIP_SOURCE_SUFFIXES):
        return True
    return False


def _copy_tree(source, destination, overwrite=False):
    copied = []
    if not source or not os.path.isdir(source):
        return copied

    for root, dirs, files in os.walk(source):
        dirs[:] = [d for d in dirs if not _should_skip_source_name(d)]
        rel = os.path.relpath(root, source)
        target_root = destination if rel == "." else os.path.join(destination, rel)
        _ensure_directory(target_root)

        for filename in files:
            if _should_skip_source_name(filename):
                continue
            src = os.path.join(root, filename)
            dst = os.path.join(target_root, filename)
            if overwrite or not os.path.exists(dst):
                shutil.copy2(src, dst)
                copied.append(dst)
    return copied


def _resolve_source_profile_root(base, profile_name, kind):
    if not base:
        return None

    base = os.path.expanduser(base)
    candidates = (
        os.path.join(base, profile_name, kind),
        os.path.join(base, profile_name),
        os.path.join(base, kind),
        base,
    )
    for candidate in candidates:
        if os.path.isdir(candidate):
            return candidate


def _apply_source_profiles(
    root,
    source_profiles=None,
    setupfiles_source=None,
    scripts_source=None,
    overwrite=False,
):
    copied = []
    root = _normalize_root(root)
    setup_target = os.path.join(root, "setupfiles")
    scripts_target = os.path.join(root, "scripts")

    for profile_name in source_profiles or ():
        setup_root = _resolve_source_profile_root(
            setupfiles_source, profile_name, "setupfiles"
        )
        scripts_root = _resolve_source_profile_root(
            scripts_source, profile_name, "scripts"
        )

        if setup_root:
            copied.extend(_copy_tree(setup_root, setup_target, overwrite=overwrite))
        if scripts_root:
            copied.extend(
                _copy_tree(scripts_root, scripts_target, overwrite=overwrite)
            )

    return copied


def _path_checks(root, profiles=None):
    results = []
    root = _normalize_root(root)
    paths.build(root)
    saved_state = _load_saved_bootstrap_state()
    merged = merge_profiles(profiles or saved_state.get("requested") or [])

    file_checks = (
        ("initialization.xml", os.path.join(paths.setup_dir, "initialization.xml")),
        ("startup_tests.yaml", paths.startup_tests),
        ("identifiers.yaml", paths.identifiers_file),
        ("task_extensions.yaml", paths.task_extensions_file),
    )
    dir_checks = (
        ("root", paths.root_dir),
        ("setupfiles", paths.setup_dir),
        ("scripts", paths.scripts_dir),
        ("preferences", paths.preferences_dir),
        ("data", paths.data_dir),
        ("DVC root", paths.dvc_dir),
        ("repositories", paths.repository_dataset_dir),
    )

    for label, directory in dir_checks:
        exists = os.path.isdir(directory)
        writable = os.access(directory, os.W_OK) if exists else False
        if exists and writable:
            status = CHECK_MARK
            detail = directory
        elif exists:
            status = WARN_MARK
            detail = "{} (not writable)".format(directory)
        else:
            status = FAIL_MARK
            detail = "{} (missing)".format(directory)
        results.append(CheckResult("Path {}".format(label), status, detail))

    for label, filename in file_checks:
        if os.path.isfile(filename):
            results.append(CheckResult("File {}".format(label), CHECK_MARK, filename))
        else:
            results.append(
                CheckResult(
                    "File {}".format(label),
                    WARN_MARK,
                    "{} (missing)".format(filename),
                )
            )

    if merged.resolved:
        results.append(
            CheckResult("Profiles", CHECK_MARK, ", ".join(merged.resolved))
        )
        for directory in merged.directories:
            full_path = os.path.join(paths.root_dir, directory)
            if os.path.isdir(full_path):
                status = CHECK_MARK
                detail = full_path
            else:
                status = FAIL_MARK
                detail = "{} (missing for selected profile)".format(full_path)
            results.append(
                CheckResult("Profile dir {}".format(directory), status, detail)
            )

        for file_spec in merged.required_files:
            full_path = os.path.join(paths.root_dir, file_spec.path)
            if os.path.isfile(full_path):
                status = CHECK_MARK
                detail = full_path
            else:
                status = FAIL_MARK
                detail = "{} (missing for selected profile)".format(full_path)
            results.append(
                CheckResult(
                    "Profile file {}".format(file_spec.path), status, detail
                )
            )

        for file_spec in merged.optional_files:
            full_path = os.path.join(paths.root_dir, file_spec.path)
            if os.path.isfile(full_path):
                status = CHECK_MARK
                detail = full_path
            else:
                status = WARN_MARK
                detail = "{} (recommended by selected profile)".format(full_path)
            results.append(
                CheckResult(
                    "Profile file {}".format(file_spec.path), status, detail
                )
            )

    if saved_state.get("source_profiles"):
        results.append(
            CheckResult(
                "Source profiles",
                CHECK_MARK,
                ", ".join(saved_state["source_profiles"]),
            )
        )

    return results


def _platform_check():
    detail = "{} {} ({})".format(
        platform.system(), platform.release(), platform.machine()
    )
    return CheckResult("Platform", CHECK_MARK, detail)


def _bootstrap(
    root,
    write_defaults=True,
    profiles=None,
    source_profiles=None,
    setupfiles_source=None,
    scripts_source=None,
    overwrite_source_files=False,
):
    root = _normalize_root(root)
    paths.build(root)
    if write_defaults:
        paths.write_defaults()

    merged = merge_profiles(profiles)
    for directory in merged.directories:
        _ensure_directory(os.path.join(paths.root_dir, directory))

    for file_spec in merged.required_files + merged.optional_files:
        if file_spec.default_text is not None:
            _write_file_if_missing(
                os.path.join(paths.root_dir, file_spec.path), file_spec.default_text
            )

    copied = _apply_source_profiles(
        root,
        source_profiles=source_profiles,
        setupfiles_source=setupfiles_source,
        scripts_source=scripts_source,
        overwrite=overwrite_source_files,
    )

    if merged.resolved or source_profiles:
        _save_bootstrap_state(merged, source_profiles=source_profiles)

    created = [
        paths.root_dir,
        paths.setup_dir,
        paths.scripts_dir,
        paths.preferences_dir,
        paths.data_dir,
        paths.dvc_dir,
        paths.repository_dataset_dir,
    ]
    created.extend(os.path.join(paths.root_dir, d) for d in merged.directories)
    created.extend(copied)
    return root, created, merged


def _doctor(root, profiles=None):
    results = [_platform_check(), _python_check(), _git_check()]
    results.extend(_required_module_checks())
    results.extend(_path_checks(root, profiles=profiles))
    return results


@app.command("profiles")
def profiles(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Show profile descriptions and included profiles.",
    ),
):
    for name in available_profile_names():
        if verbose:
            spec = PROFILES[name]
            details = spec.description
            if spec.includes:
                details = "{} includes={}".format(details, ",".join(spec.includes))
            typer.echo("{}: {}".format(name, details))
        else:
            typer.echo(name)


@app.command("install-plan")
def install_plan(
    root: str = typer.Option(
        DEFAULT_ROOT,
        "--root",
        help="Pychron data/config root to initialize.",
    ),
    profiles: list[str] = typer.Option(
        None,
        "--profile",
        help="Build an install plan for one or more profiles.",
    ),
):
    profiles = _normalize_profiles(profiles)
    plan = build_install_plan(profiles=profiles, root=root)
    typer.echo("Platform: {}".format(plan.platform_name))
    if plan.requested_profiles:
        typer.echo(
            "Requested profiles: {}".format(", ".join(plan.requested_profiles))
        )
        typer.echo("Resolved profiles: {}".format(", ".join(plan.resolved_profiles)))
    if plan.extras:
        typer.echo("Recommended extras: {}".format(", ".join(plan.extras)))

    typer.echo("")
    typer.echo("Commands")
    for command in plan.commands:
        typer.echo(" - {}".format(command))

    typer.echo("")
    typer.echo("Notes")
    for note in plan.notes:
        typer.echo(" - {}".format(note))


@app.command("bootstrap")
def bootstrap(
    root: str = typer.Option(
        DEFAULT_ROOT,
        "--root",
        help="Pychron data/config root to initialize.",
    ),
    write_defaults: bool = typer.Option(
        True,
        "--write-defaults/--no-write-defaults",
        help="Write default initialization and UI config files.",
    ),
    run_doctor: bool = typer.Option(
        True,
        "--doctor/--no-doctor",
        help="Run environment checks after bootstrapping.",
    ),
    profiles: list[str] = typer.Option(
        None,
        "--profile",
        help="Apply one or more composable bootstrap profiles.",
    ),
    source_profiles: list[str] = typer.Option(
        None,
        "--source-profile",
        help="Copy one or more site/instrument example bundles from external source trees.",
    ),
    setupfiles_source: str = typer.Option(
        None,
        "--setupfiles-source",
        help="External directory containing setupfiles example bundles.",
    ),
    scripts_source: str = typer.Option(
        None,
        "--scripts-source",
        help="External directory containing scripts example bundles.",
    ),
    overwrite_source_files: bool = typer.Option(
        False,
        "--overwrite-source-files/--no-overwrite-source-files",
        help="Allow external source bundles to overwrite existing files in the target root.",
    ),
):
    profiles = _normalize_profiles(profiles)
    source_profiles = _normalize_profiles(source_profiles)
    root, created, merged = _bootstrap(
        root,
        write_defaults=write_defaults,
        profiles=profiles,
        source_profiles=source_profiles,
        setupfiles_source=setupfiles_source,
        scripts_source=scripts_source,
        overwrite_source_files=overwrite_source_files,
    )
    typer.echo("Bootstrapped Pychron root: {}".format(root))
    for item in created:
        typer.echo(" - {}".format(item))

    if write_defaults:
        typer.echo("Default configuration files were written where missing.")

    if merged.resolved:
        typer.echo("Applied profiles: {}".format(", ".join(merged.resolved)))
    if source_profiles:
        typer.echo("Applied source bundles: {}".format(", ".join(source_profiles)))

    if run_doctor:
        typer.echo("")
        typer.echo("Doctor results")
        _echo_results(_doctor(root, profiles=profiles))


@app.command("doctor")
def doctor(
    root: str = typer.Option(
        DEFAULT_ROOT,
        "--root",
        help="Pychron data/config root to inspect.",
    ),
    profiles: list[str] = typer.Option(
        None,
        "--profile",
        help="Validate one or more composable profiles. If omitted, saved "
        "bootstrap profiles are used.",
    ),
):
    profiles = _normalize_profiles(profiles)
    results = _doctor(root, profiles=profiles)
    _echo_results(results)

    if any(result.status == FAIL_MARK for result in results):
        raise typer.Exit(code=1)


@app.command("export-config")
def export_config(
    root: str = typer.Option(
        DEFAULT_ROOT,
        "--root",
        help="Pychron data/config root to export.",
    ),
    output: str = typer.Option(
        ...,
        "--output",
        help="Zip archive path to write.",
    ),
    include_appdata: bool = typer.Option(
        False,
        "--include-appdata/--no-include-appdata",
        help="Include .appdata in the exported bundle.",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite/--no-overwrite",
        help="Overwrite an existing archive.",
    ),
):
    exported = export_config_bundle(
        root, output, include_appdata=include_appdata, overwrite=overwrite
    )
    typer.echo("Exported configuration bundle: {}".format(os.path.expanduser(output)))
    for item in exported:
        typer.echo(" - {}".format(item))


@app.command("import-config")
def import_config(
    root: str = typer.Option(
        DEFAULT_ROOT,
        "--root",
        help="Pychron data/config root to import into.",
    ),
    archive: str = typer.Option(
        ...,
        "--archive",
        help="Zip archive path to import.",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite/--no-overwrite",
        help="Allow imported files to overwrite existing files.",
    ),
):
    extracted, skipped = import_config_bundle(root, archive, overwrite=overwrite)
    typer.echo("Imported configuration bundle: {}".format(os.path.expanduser(archive)))
    typer.echo("Extracted {} files".format(len(extracted)))
    for item in extracted:
        typer.echo(" - {}".format(item))
    if skipped:
        typer.echo("Skipped {} files".format(len(skipped)))
        for item in skipped:
            typer.echo(" - {}".format(item))


def main():
    app()


def bootstrap_main():
    app(["bootstrap"])


def doctor_main():
    app(["doctor"])


if __name__ == "__main__":
    main()
