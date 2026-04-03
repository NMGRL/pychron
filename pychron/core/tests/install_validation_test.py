import os
import tempfile
import unittest

try:
    from pychron.install_validation import (
        build_runtime_validation_report,
        profile_state_path,
        validate_runtime_root,
    )
except ModuleNotFoundError as exc:
    build_runtime_validation_report = None
    profile_state_path = None
    validate_runtime_root = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


@unittest.skipIf(_IMPORT_ERROR is not None, str(_IMPORT_ERROR))
class InstallValidationTestCase(unittest.TestCase):
    def test_validate_runtime_root_does_not_create_directories(self):
        with tempfile.TemporaryDirectory() as base:
            root = os.path.join(base, "Pychron")
            self.assertFalse(os.path.exists(root))
            issues = validate_runtime_root(root, bundles=["data-reduction"])
            self.assertFalse(os.path.exists(root))
            self.assertTrue(any(issue.status == "FAIL" for issue in issues))

    def test_validate_runtime_root_uses_saved_bootstrap_state(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, ".appdata"), exist_ok=True)
            with open(profile_state_path(root), "w") as wfile:
                wfile.write(
                    '{"root": "%s", "bundles": ["data-reduction"], "requested": ["data-reduction"]}'
                    % root
                )

            os.makedirs(os.path.join(root, "setupfiles", "pipeline"), exist_ok=True)
            os.makedirs(os.path.join(root, "scripts", "pipeline"), exist_ok=True)
            os.makedirs(os.path.join(root, "preferences"), exist_ok=True)
            os.makedirs(
                os.path.join(root, "data", ".dvc", "repositories"), exist_ok=True
            )
            os.makedirs(os.path.join(root, "scripts"), exist_ok=True)
            with open(os.path.join(root, "setupfiles", "flux_constants.yaml"), "w"):
                pass
            with open(
                os.path.join(root, "setupfiles", "experiment_defaults.yaml"), "w"
            ):
                pass
            with open(os.path.join(root, "setupfiles", "initialization.xml"), "w"):
                pass
            with open(os.path.join(root, "setupfiles", "startup_tests.yaml"), "w"):
                pass
            with open(os.path.join(root, ".appdata", "identifiers.yaml"), "w"):
                pass
            with open(os.path.join(root, ".appdata", "task_extensions.yaml"), "w"):
                pass

            issues = validate_runtime_root(root)
            self.assertTrue(any(issue.name == "Bundles" for issue in issues))
            self.assertTrue(any(issue.name == "Profiles" for issue in issues))

    def test_build_runtime_validation_report_detects_first_run_state(self):
        with tempfile.TemporaryDirectory() as base:
            root = os.path.join(base, "Pychron")
            report = build_runtime_validation_report(root)
            self.assertTrue(report.should_prompt_first_run)
            self.assertTrue(report.blocking_issues)

    def test_build_runtime_validation_report_summarizes_blocking_issues(self):
        with tempfile.TemporaryDirectory() as base:
            root = os.path.join(base, "Pychron")
            report = build_runtime_validation_report(root)
            self.assertIn("Pychron setup is incomplete", report.summary_lines()[0])


if __name__ == "__main__":
    unittest.main()
