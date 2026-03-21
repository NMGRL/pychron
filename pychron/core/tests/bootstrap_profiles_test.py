import unittest

from pychron.cli_profiles import available_profile_names, merge_profiles


class BootstrapProfilesTestCase(unittest.TestCase):
    def test_available_profiles_include_expected_aliases(self):
        names = available_profile_names()
        self.assertIn("ngx", names)
        self.assertIn("chromiumco2", names)
        self.assertIn("data-reduction", names)

    def test_ngx_alias_expands_to_spectrometer_profile(self):
        merged = merge_profiles(["ngx"])
        self.assertIn("spectrometer", merged.resolved)
        self.assertIn("spectrometer-ngx", merged.resolved)

    def test_chromiumco2_profile_composes_multiple_profiles(self):
        merged = merge_profiles(["chromiumco2"])
        self.assertIn("experiment", merged.resolved)
        self.assertIn("extraction-line", merged.resolved)
        self.assertIn("chromium", merged.resolved)
        self.assertIn("laser-co2", merged.resolved)

    def test_multiple_profiles_merge_without_duplicate_directories(self):
        merged = merge_profiles(["ngx", "data-reduction"])
        self.assertEqual(len(merged.directories), len(set(merged.directories)))
        self.assertEqual(len(merged.required_files), len({f.path for f in merged.required_files}))


if __name__ == "__main__":
    unittest.main()
