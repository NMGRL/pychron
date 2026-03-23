import os
import tempfile
import unittest

from pychron.install_validation import profile_state_path, validate_runtime_root


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
                    '{"bundles": ["data-reduction"], "requested": ["data-reduction"]}'
                )

            os.makedirs(os.path.join(root, "setupfiles", "pipeline"), exist_ok=True)
            os.makedirs(os.path.join(root, "scripts", "pipeline"), exist_ok=True)
            os.makedirs(os.path.join(root, "preferences"), exist_ok=True)
            os.makedirs(
                os.path.join(root, "data", ".dvc", "repositories"), exist_ok=True
            )
            with open(os.path.join(root, "setupfiles", "flux_constants.yaml"), "w"):
                pass
            with open(
                os.path.join(root, "setupfiles", "experiment_defaults.yaml"), "w"
            ):
                pass

            issues = validate_runtime_root(root)
            self.assertTrue(any(issue.name == "Bundles" for issue in issues))
            self.assertTrue(any(issue.name == "Profiles" for issue in issues))


if __name__ == "__main__":
    unittest.main()
