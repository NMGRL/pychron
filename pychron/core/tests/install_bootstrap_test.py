import os
import tempfile
import unittest

try:
    from pychron.install_bootstrap import (
        bootstrap_runtime_root,
        repair_runtime_root,
        should_skip_source_name,
    )
    from pychron.install_runtime import load_bootstrap_state
except ModuleNotFoundError as exc:
    bootstrap_runtime_root = None
    repair_runtime_root = None
    should_skip_source_name = None
    load_bootstrap_state = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


@unittest.skipIf(_IMPORT_ERROR is not None, str(_IMPORT_ERROR))
class InstallBootstrapTestCase(unittest.TestCase):
    def test_should_skip_source_name(self):
        self.assertTrue(should_skip_source_name(".DS_Store"))
        self.assertTrue(should_skip_source_name("~foo.txt"))
        self.assertTrue(should_skip_source_name("bar.orig"))
        self.assertFalse(should_skip_source_name("startup_tests.yaml"))

    def test_bootstrap_runtime_root_persists_profile_state(self):
        with tempfile.TemporaryDirectory() as root:
            bootstrap_runtime_root(
                root,
                profiles=("experiment",),
                bundles=("data-reduction",),
            )

            state = load_bootstrap_state(root)
            self.assertEqual(state["bundles"], ["data-reduction"])
            self.assertIn("experiment", state["requested"])
            self.assertEqual(state["root"], root)
            self.assertTrue(state["managed_directories"])
            self.assertTrue(state["managed_files"])
            self.assertTrue(
                os.path.isfile(
                    os.path.join(root, "setupfiles", "experiment_defaults.yaml")
                )
            )

    def test_repair_runtime_root_does_not_overwrite_existing_defaults(self):
        with tempfile.TemporaryDirectory() as root:
            bootstrap_runtime_root(root, profiles=("experiment",))
            path = os.path.join(root, "setupfiles", "experiment_defaults.yaml")
            with open(path, "w") as wfile:
                wfile.write("custom-defaults\n")

            repair_runtime_root(root, profiles=("experiment",))

            with open(path, "r") as rfile:
                self.assertEqual(rfile.read(), "custom-defaults\n")

    def test_bootstrap_runtime_root_overwrites_source_files_when_requested(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as src:
            profile_dir = os.path.join(src, "felix", "setupfiles")
            os.makedirs(profile_dir)
            target = os.path.join(root, "setupfiles", "instrument.cfg")
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w") as wfile:
                wfile.write("existing\n")
            with open(os.path.join(profile_dir, "instrument.cfg"), "w") as wfile:
                wfile.write("replacement\n")

            bootstrap_runtime_root(
                root,
                source_profiles=("felix",),
                setupfiles_source=src,
                overwrite_source_files=True,
            )

            with open(target, "r") as rfile:
                self.assertEqual(rfile.read(), "replacement\n")


if __name__ == "__main__":
    unittest.main()
