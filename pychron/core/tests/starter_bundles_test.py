import unittest

from pychron.starter_bundles import bundle_profiles, resolve_bundles


class StarterBundlesTestCase(unittest.TestCase):
    def test_resolve_bundle_alias(self):
        bundles = resolve_bundles(["ngx"])
        self.assertEqual(bundles[0].name, "ngx-collection")

    def test_bundle_profiles_are_deduplicated(self):
        profiles = bundle_profiles(["ngx-collection", "experiment-control"])
        self.assertEqual(profiles, ("experiment", "ngx"))


if __name__ == "__main__":
    unittest.main()
