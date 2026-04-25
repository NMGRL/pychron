import os
import tempfile
import unittest
import zipfile

from pychron.install_support import (
    build_install_plan,
    export_config_bundle,
    import_config_bundle,
)


class InstallSupportTestCase(unittest.TestCase):
    def test_build_install_plan_includes_bundle_profiles(self):
        plan = build_install_plan(["data-reduction"], bundles=["ngx"])
        self.assertIn("ngx-collection", plan.requested_bundles)
        self.assertIn("experiment", plan.resolved_profiles)
        self.assertIn("spectrometer-ngx", plan.extras)

    def test_build_install_plan_includes_expected_extras(self):
        plan = build_install_plan(["ngx", "chromiumco2"], root="~/Pychron")
        self.assertIn("hardware", plan.extras)
        self.assertIn("laser", plan.extras)
        self.assertIn("spectrometer-ngx", plan.extras)

    def test_export_and_import_config_bundle(self):
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as dest:
            os.makedirs(os.path.join(src, "setupfiles"), exist_ok=True)
            os.makedirs(os.path.join(src, "scripts", "measurement"), exist_ok=True)

            with open(
                os.path.join(src, "setupfiles", "initialization.xml"), "w"
            ) as wfile:
                wfile.write("<root/>")
            with open(
                os.path.join(src, "scripts", "measurement", "foo.py"), "w"
            ) as wfile:
                wfile.write("print('ok')\n")

            archive = os.path.join(src, "bundle.zip")
            exported = export_config_bundle(src, archive, include_appdata=False)
            self.assertIn("setupfiles/initialization.xml", exported)
            self.assertIn("scripts/measurement/foo.py", exported)

            with zipfile.ZipFile(archive, "r") as zf:
                self.assertIn("manifest.json", zf.namelist())

            extracted, skipped = import_config_bundle(dest, archive)
            self.assertIn("setupfiles/initialization.xml", extracted)
            self.assertIn("scripts/measurement/foo.py", extracted)
            self.assertEqual(skipped, [])
            self.assertTrue(
                os.path.isfile(os.path.join(dest, "setupfiles", "initialization.xml"))
            )
            self.assertTrue(
                os.path.isfile(os.path.join(dest, "scripts", "measurement", "foo.py"))
            )


if __name__ == "__main__":
    unittest.main()
