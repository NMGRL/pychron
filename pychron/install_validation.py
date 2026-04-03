import os
from dataclasses import dataclass

from pychron.cli_profiles import merge_profiles
from pychron.install_runtime import (
    base_runtime_directories,
    load_bootstrap_state,
    make_runtime_layout,
    managed_runtime_files,
    normalize_root,
    profile_state_path,
)
from pychron.starter_bundles import bundle_profiles, resolve_bundles


@dataclass(frozen=True)
class ValidationIssue:
    name: str
    status: str
    detail: str
    hint: str = ""
    category: str = ""
    managed_by: str = "bootstrap"


@dataclass(frozen=True)
class RuntimeValidationReport:
    root: str
    issues: tuple[ValidationIssue, ...]

    @property
    def blocking_issues(self):
        return tuple(issue for issue in self.issues if issue.status == "FAIL")

    @property
    def recommended_issues(self):
        return tuple(issue for issue in self.issues if issue.status == "WARN")

    @property
    def info_issues(self):
        return tuple(issue for issue in self.issues if issue.status == "OK")

    @property
    def should_prompt_first_run(self):
        return bool(
            [
                issue
                for issue in self.blocking_issues
                if issue.category
                in ("root", "base_dir", "base_file", "profile_dir", "profile_file")
            ]
        )

    def summary_lines(self, limit=5):
        if not self.blocking_issues:
            return ()

        lines = [
            "Pychron setup is incomplete. {} blocking issue(s) found.".format(
                len(self.blocking_issues)
            )
        ]
        for issue in self.blocking_issues[:limit]:
            lines.append("- {}: {}".format(issue.name, issue.detail))
        lines.append("Run `pychron-doctor --root {}` for a full report.".format(self.root))
        return tuple(lines)


def combine_profile_inputs(profiles=None, bundles=None, saved_state=None):
    saved_state = saved_state or {}
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
    return "Run `{}` to initialize or repair this runtime.".format(" ".join(parts))


def _managed_file_hint(spec, bootstrap_hint):
    if spec.default_text is not None:
        return bootstrap_hint

    if spec.required:
        return "This file is required for the selected workflow and must be supplied by the lab."

    return "Create this file when the workflow needs it."


def _profile_file_managed_by(file_spec):
    return "bootstrap" if file_spec.default_text is not None else "lab"


def build_runtime_validation_report(root, profiles=None, bundles=None):
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
        issues.append(ValidationIssue("Path root", "OK", layout.root, category="root"))
    else:
        issues.append(
            ValidationIssue(
                "Path root",
                "FAIL",
                "{} (missing)".format(layout.root),
                bootstrap_hint,
                category="root",
            )
        )

    for label, directory in base_runtime_directories(layout):
        if os.path.isdir(directory):
            issues.append(
                ValidationIssue(
                    "Path {}".format(label),
                    "OK",
                    directory,
                    category="base_dir",
                )
            )
        else:
            issues.append(
                ValidationIssue(
                    "Path {}".format(label),
                    "FAIL",
                    "{} (missing)".format(directory),
                    bootstrap_hint,
                    category="base_dir",
                )
            )

    for spec in managed_runtime_files(layout):
        if os.path.isfile(spec.path):
            issues.append(
                ValidationIssue(
                    "File {}".format(spec.label),
                    "OK",
                    spec.path,
                    category="base_file",
                    managed_by=spec.managed_by,
                )
            )
        elif spec.required:
            issues.append(
                ValidationIssue(
                    "File {}".format(spec.label),
                    "FAIL",
                    "{} (missing)".format(spec.path),
                    _managed_file_hint(spec, bootstrap_hint),
                    category="base_file",
                    managed_by=spec.managed_by,
                )
            )
        else:
            issues.append(
                ValidationIssue(
                    "File {}".format(spec.label),
                    "WARN",
                    "{} (missing)".format(spec.path),
                    _managed_file_hint(spec, bootstrap_hint),
                    category="base_file",
                    managed_by=spec.managed_by,
                )
            )

    if bundle_specs:
        detail = ", ".join(
            "{}@{}".format(bundle.name, bundle.version) for bundle in bundle_specs
        )
        issues.append(ValidationIssue("Bundles", "OK", detail))

    if merged.resolved:
        issues.append(ValidationIssue("Profiles", "OK", ", ".join(merged.resolved)))

    for directory in merged.directories:
        full_path = os.path.join(layout.root, directory)
        if os.path.isdir(full_path):
            issues.append(
                ValidationIssue(
                    "Profile dir {}".format(directory),
                    "OK",
                    full_path,
                    category="profile_dir",
                )
            )
        else:
            issues.append(
                ValidationIssue(
                    "Profile dir {}".format(directory),
                    "FAIL",
                    "{} (missing for selected profile)".format(full_path),
                    bootstrap_hint,
                    category="profile_dir",
                )
            )

    for file_spec in merged.required_files + merged.optional_files:
        full_path = os.path.join(layout.root, file_spec.path)
        status = "OK" if os.path.isfile(full_path) else ("FAIL" if file_spec.required else "WARN")
        if status == "OK":
            issues.append(
                ValidationIssue(
                    "Profile file {}".format(file_spec.path),
                    status,
                    full_path,
                    category="profile_file",
                    managed_by=_profile_file_managed_by(file_spec),
                )
            )
            continue

        issues.append(
            ValidationIssue(
                "Profile file {}".format(file_spec.path),
                status,
                "{} ({})".format(
                    full_path,
                    "missing for selected profile"
                    if file_spec.required
                    else "recommended by selected profile",
                ),
                bootstrap_hint
                if file_spec.default_text is not None
                else (
                    "This file is required for the selected workflow and must be supplied by the lab."
                    if file_spec.required
                    else "Create this file when the workflow needs it."
                ),
                category="profile_file",
                managed_by=_profile_file_managed_by(file_spec),
            )
        )

    if not saved_state and not bundle_specs and not merged.resolved:
        issues.append(
            ValidationIssue(
                "Bootstrap state",
                "WARN",
                "{} (missing)".format(profile_state_path(layout.root)),
                "Run `pychron-bootstrap` so the install records its selected profiles.",
                category="bootstrap_state",
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
                category="bootstrap_state",
            )
        )

    return RuntimeValidationReport(root=normalize_root(root), issues=tuple(issues))


def validate_runtime_root(root, profiles=None, bundles=None):
    return list(
        build_runtime_validation_report(root, profiles=profiles, bundles=bundles).issues
    )
