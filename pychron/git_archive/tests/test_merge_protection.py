import unittest

try:
    from pychron.git_archive.repo_manager import GitRepoManager
except ModuleNotFoundError as exc:
    GitRepoManager = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


@unittest.skipIf(_IMPORT_ERROR is not None, "Git archive dependencies not available")
class MergeProtectionTestCase(unittest.TestCase):
    def setUp(self):
        self.repo = GitRepoManager()

    def test_flags_uuid_backed_analysis_deletions(self):
        paths = [
            "abcde/f7ab86e8/4ccc/a6c5/f7ab86e8-4ccc-4a6c-a123-118ff07c5083.json",
            "abcde/f7ab86e8/4ccc/a6c5/f7ab86e8-4ccc-4a6c-a123-118ff07c5083.extr.json",
        ]
        deleted = self.repo._protected_uuid_deletions(paths)
        self.assertEqual(deleted, paths)

    def test_ignores_non_uuid_paths(self):
        paths = [
            "Foo123/Foo123-01.json",
            "metadata/productions.json",
            "12345/12345-01.icfa.json",
        ]
        self.assertEqual(self.repo._protected_uuid_deletions(paths), [])


if __name__ == "__main__":
    unittest.main()
