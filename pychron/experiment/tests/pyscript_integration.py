from __future__ import absolute_import

import tempfile
import unittest
from os import remove
from os.path import join
from types import MethodType

from pychron.experiment.automated_run.spec import AutomatedRunSpec
from pychron.experiment.utilities.script import resolve_script_name, script_name_candidates


class _DummyRun(object):
    def __init__(self, measurement_script=None):
        self.measurement_script = measurement_script
        self.post_measurement_script = None
        self.post_equilibration_script = None
        self.extraction_script = None
        self.syn_extraction_script = None
        self.spec = None

    def refresh_scripts(self):
        pass


class _DummyScript(object):
    def syntax_ok(self):
        return True

    def calculate_estimated_duration(self, ctx):
        return 1


class PyScriptIntegrationTestCase(unittest.TestCase):
    def test_script_name_candidates_prefers_mass_spec_prefix(self):
        self.assertEqual(
            script_name_candidates("foo", "jan"),
            ["jan_foo.py", "foo.py"],
        )

    def test_script_name_candidates_strips_duplicate_prefix(self):
        self.assertEqual(
            script_name_candidates("jan_foo.py", "jan"),
            ["jan_foo.py", "foo.py"],
        )

    def test_resolve_script_name_falls_back_to_unprefixed_script(self):
        with tempfile.TemporaryDirectory() as root:
            path = join(root, "foo.py")
            with open(path, "w"):
                pass

            self.assertEqual(resolve_script_name(root, "foo", "jan"), "foo.py")

    def test_missing_configured_script_marks_spec_non_executable(self):
        spec = AutomatedRunSpec(labnumber="10001", measurement_script="missing_script")
        dummy = _DummyRun(measurement_script=None)
        spec.make_run = MethodType(lambda self, new_uuid=False: dummy, spec)

        spec.test_scripts(duration=False)

        self.assertFalse(spec.executable)

    def test_loaded_configured_script_keeps_spec_executable(self):
        spec = AutomatedRunSpec(labnumber="10001", measurement_script="ok_script")
        dummy = _DummyRun(measurement_script=_DummyScript())
        spec.make_run = MethodType(lambda self, new_uuid=False: dummy, spec)

        spec.test_scripts(duration=False)

        self.assertTrue(spec.executable)


if __name__ == "__main__":
    unittest.main()
