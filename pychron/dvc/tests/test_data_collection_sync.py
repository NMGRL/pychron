import unittest

from pychron.dvc import DATA_COLLECTION_BRANCH
from pychron.dvc.dvc import DVC


class _DummyDVC:
    def __init__(self):
        self.debug_messages = []
        self.debug_exception_calls = 0

    def debug(self, msg, *args):
        if args:
            msg = msg % args
        self.debug_messages.append(msg)

    def debug_exception(self):
        self.debug_exception_calls += 1


class _FakeRepo:
    def __init__(
        self,
        branch="reduce",
        has_remote=True,
        remote_branches="  origin/main\n  origin/data_collection\n",
    ):
        self.name = "example<GitRepo>"
        self._branch = branch
        self._has_remote = has_remote
        self._remote_branches = remote_branches
        self.fetch_calls = []
        self.merge_calls = []

    def get_current_branch(self):
        return self._branch

    def has_remote(self, remote):
        return self._has_remote

    def cmd(self, command, *args):
        if command == "branch" and args == ("-r",):
            return self._remote_branches
        raise AssertionError("unexpected cmd {} {}".format(command, args))

    def fetch(self, remote):
        self.fetch_calls.append(remote)

    def merge(self, branch, inform=False):
        self.merge_calls.append((branch, inform))


class DataCollectionSyncTestCase(unittest.TestCase):
    def test_sync_skips_data_collection_branch(self):
        dvc = _DummyDVC()
        repo = _FakeRepo(branch=DATA_COLLECTION_BRANCH)

        result = DVC._sync_reduction_repo_from_data_collection(dvc, repo)

        self.assertFalse(result)
        self.assertEqual(repo.fetch_calls, [])
        self.assertEqual(repo.merge_calls, [])

    def test_sync_skips_when_remote_missing(self):
        dvc = _DummyDVC()
        repo = _FakeRepo(has_remote=False)

        result = DVC._sync_reduction_repo_from_data_collection(dvc, repo)

        self.assertFalse(result)
        self.assertEqual(repo.fetch_calls, [])
        self.assertEqual(repo.merge_calls, [])

    def test_sync_skips_when_data_collection_remote_branch_missing(self):
        dvc = _DummyDVC()
        repo = _FakeRepo(remote_branches="  origin/main\n")

        result = DVC._sync_reduction_repo_from_data_collection(dvc, repo)

        self.assertFalse(result)
        self.assertEqual(repo.fetch_calls, [])
        self.assertEqual(repo.merge_calls, [])

    def test_sync_merges_origin_data_collection_into_reduction_branch(self):
        dvc = _DummyDVC()
        repo = _FakeRepo()

        result = DVC._sync_reduction_repo_from_data_collection(dvc, repo, inform=True)

        self.assertTrue(result)
        self.assertEqual(repo.fetch_calls, ["origin"])
        self.assertEqual(repo.merge_calls, [("origin/data_collection", True)])


if __name__ == "__main__":
    unittest.main()
