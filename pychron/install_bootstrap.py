import json
import os
import shutil

from pychron.cli_profiles import merge_profiles
from pychron.install_validation import profile_state_path
from pychron.paths import paths
from pychron.starter_bundles import resolve_bundles

DEFAULT_ROOT = "~/Pychron"
SKIP_SOURCE_NAMES = {".DS_Store"}
SKIP_SOURCE_PREFIXES = ("~", "~~")
SKIP_SOURCE_SUFFIXES = (".bk", ".orig")


def normalize_root(root):
    root = root or DEFAULT_ROOT
    return os.path.expanduser(root)


def ensure_directory(path):
    os.makedirs(path, exist_ok=True)


def write_file_if_missing(path, text):
    if os.path.isfile(path):
        return False

    parent = os.path.dirname(path)
    if parent:
        ensure_directory(parent)

    with open(path, "w") as wfile:
        wfile.write(text or "")
    return True


def save_bootstrap_state(root, merged, bundles=None, source_profiles=None):
    path = profile_state_path(root)
    ensure_directory(os.path.dirname(path))
    payload = {
        "bundles": list(bundles or ()),
        "requested": list(merged.requested),
        "resolved": list(merged.resolved),
        "source_profiles": list(source_profiles or ()),
    }
    with open(path, "w") as wfile:
        json.dump(payload, wfile, indent=2, sort_keys=True)


def should_skip_source_name(name):
    if name in SKIP_SOURCE_NAMES:
        return True
    if name.startswith(SKIP_SOURCE_PREFIXES):
        return True
    if name.endswith(SKIP_SOURCE_SUFFIXES):
        return True
    return False


def copy_tree(source, destination, overwrite=False):
    copied = []
    if not source or not os.path.isdir(source):
        return copied

    for root, dirs, files in os.walk(source):
        dirs[:] = [d for d in dirs if not should_skip_source_name(d)]
        rel = os.path.relpath(root, source)
        target_root = destination if rel == "." else os.path.join(destination, rel)
        ensure_directory(target_root)

        for filename in files:
            if should_skip_source_name(filename):
                continue
            src = os.path.join(root, filename)
            dst = os.path.join(target_root, filename)
            if overwrite or not os.path.exists(dst):
                shutil.copy2(src, dst)
                copied.append(dst)
    return copied


def resolve_source_profile_root(base, profile_name, kind):
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


def apply_source_profiles(
    root,
    source_profiles=None,
    setupfiles_source=None,
    scripts_source=None,
    overwrite=False,
):
    copied = []
    root = normalize_root(root)
    setup_target = os.path.join(root, "setupfiles")
    scripts_target = os.path.join(root, "scripts")

    for profile_name in source_profiles or ():
        setup_root = resolve_source_profile_root(
            setupfiles_source, profile_name, "setupfiles"
        )
        scripts_root = resolve_source_profile_root(
            scripts_source, profile_name, "scripts"
        )

        if setup_root:
            copied.extend(copy_tree(setup_root, setup_target, overwrite=overwrite))
        if scripts_root:
            copied.extend(copy_tree(scripts_root, scripts_target, overwrite=overwrite))

    return copied


def bootstrap_runtime_root(
    root,
    write_defaults=True,
    profiles=None,
    bundles=None,
    source_profiles=None,
    setupfiles_source=None,
    scripts_source=None,
    overwrite_source_files=False,
):
    root = normalize_root(root)
    paths.build(root)
    if write_defaults:
        paths.write_defaults()

    profile_names = []
    for bundle in resolve_bundles(bundles or ()):
        for profile in bundle.profiles:
            if profile not in profile_names:
                profile_names.append(profile)
    for profile in profiles or ():
        if profile not in profile_names:
            profile_names.append(profile)

    merged = merge_profiles(profile_names)
    for directory in merged.directories:
        ensure_directory(os.path.join(paths.root_dir, directory))

    for file_spec in merged.required_files + merged.optional_files:
        if file_spec.default_text is not None:
            write_file_if_missing(
                os.path.join(paths.root_dir, file_spec.path), file_spec.default_text
            )

    copied = apply_source_profiles(
        root,
        source_profiles=source_profiles,
        setupfiles_source=setupfiles_source,
        scripts_source=scripts_source,
        overwrite=overwrite_source_files,
    )

    if merged.resolved or bundles or source_profiles:
        save_bootstrap_state(
            root,
            merged,
            bundles=bundles,
            source_profiles=source_profiles,
        )

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
