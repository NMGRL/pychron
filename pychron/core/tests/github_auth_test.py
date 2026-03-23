import os
import tempfile
import unittest
from unittest.mock import patch

from pychron.git.tasks import github_auth


class GitHubAuthTestCase(unittest.TestCase):
    def test_load_and_save_token(self):
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, "oauth.json")
            with patch.object(github_auth, "_oauth_file", return_value=path):
                self.assertEqual(github_auth.load_token(), {})
                github_auth.save_token({"access_token": "abc123"})
                self.assertEqual(github_auth.get_access_token(), "abc123")

    def test_authorization_headers(self):
        headers = github_auth.authorization_headers("abc123")
        self.assertEqual(headers["Authorization"], "token abc123")


if __name__ == "__main__":
    unittest.main()
