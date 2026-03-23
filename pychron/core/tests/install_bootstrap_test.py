import os
import tempfile
import unittest

try:
    from pychron.install_bootstrap import bootstrap_runtime_root, should_skip_source_name
    from pychron.install_validation import load_bootstrap_state
except ModuleNotFoundError as exc:
    bootstrap_runtime_root = None
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
            self.assertTrue(
                os.path.isfile(
                    os.path.join(root, "setupfiles", "experiment_defaults.yaml")
                )
            )


if __name__ == "__main__":
    unittest.main()
