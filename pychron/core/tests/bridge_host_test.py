# ===============================================================================
# Copyright 2026 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
import unittest
from unittest.mock import MagicMock

from pychron.git.hosts._bridge_client import (
    BridgeAuthError,
    BridgeLabMismatch,
    BridgeNotFound,
)
from pychron.git.hosts.bridge import BridgeService


def _make_service(client=None, enabled=True):
    s = BridgeService()
    s.enabled = enabled
    s.base_url = "https://bridge.test"
    s.bearer_token = "bear"
    s.service_account_key_path = "/dev/null"
    s.lab_name = "NMGRL"
    s._client = client
    return s


class BridgeServiceCreateRepoTestCase(unittest.TestCase):
    def test_create_repo_returns_true_and_caches_url(self):
        client = MagicMock()
        client.ensure_repository.return_value = {
            "repository_identifier": "X_001",
            "clone_url_ssh": "ssh://git@host:222/nmgrl/X_001.git",
            "clone_url_https": "https://host/nmgrl/X_001.git",
            "created": True,
        }
        svc = _make_service(client=client)

        result = svc.create_repo("X_001", organization="ignored", instrument="Fusions")

        self.assertTrue(result)
        client.ensure_repository.assert_called_once()
        kwargs = client.ensure_repository.call_args.kwargs
        self.assertEqual(kwargs["repository_identifier"], "X_001")
        self.assertEqual(kwargs["lab_name"], "NMGRL")
        self.assertEqual(kwargs["instrument"], "Fusions")
        self.assertEqual(svc.make_url("X_001", "ignored"), "ssh://git@host:222/nmgrl/X_001.git")

    def test_create_repo_returns_false_on_lab_mismatch(self):
        client = MagicMock()
        client.ensure_repository.side_effect = BridgeLabMismatch("nope")
        svc = _make_service(client=client)
        self.assertFalse(svc.create_repo("X_001", organization="ignored"))

    def test_create_repo_returns_false_on_auth_error(self):
        client = MagicMock()
        client.ensure_repository.side_effect = BridgeAuthError("bad token")
        svc = _make_service(client=client)
        self.assertFalse(svc.create_repo("X_001", organization="ignored"))

    def test_create_repo_returns_false_when_disabled(self):
        svc = _make_service(client=None, enabled=False)
        self.assertFalse(svc.create_repo("X_001", organization="ignored"))


class BridgeServiceMakeUrlTestCase(unittest.TestCase):
    def test_make_url_returns_lookup_result(self):
        client = MagicMock()
        client.lookup_repository.return_value = {
            "clone_url_ssh": "ssh://git@host:222/nmgrl/Y_002.git",
        }
        svc = _make_service(client=client)
        self.assertEqual(svc.make_url("Y_002", "ignored"), "ssh://git@host:222/nmgrl/Y_002.git")

    def test_make_url_returns_empty_on_404(self):
        client = MagicMock()
        client.lookup_repository.return_value = None
        svc = _make_service(client=client)
        self.assertEqual(svc.make_url("Missing", "ignored"), "")

    def test_make_url_returns_empty_when_disabled(self):
        svc = _make_service(client=None, enabled=False)
        self.assertEqual(svc.make_url("Y_002", "ignored"), "")

    def test_make_url_uses_cache_on_repeat(self):
        client = MagicMock()
        client.lookup_repository.return_value = {"clone_url_ssh": "ssh://x"}
        svc = _make_service(client=client)

        svc.make_url("Z_003", "ignored")
        svc.make_url("Z_003", "ignored")

        self.assertEqual(client.lookup_repository.call_count, 1)


class BridgeServiceListsTestCase(unittest.TestCase):
    def test_get_repository_names_extracts_identifiers(self):
        client = MagicMock()
        client.list_repositories.return_value = {
            "repositories": [
                {"repository_identifier": "A"},
                {"repository_identifier": "B"},
            ]
        }
        svc = _make_service(client=client)
        self.assertEqual(svc.get_repository_names("ignored"), ["A", "B"])

    def test_remote_exists_returns_false_on_404(self):
        client = MagicMock()
        client.lookup_repository.side_effect = BridgeNotFound("404")
        svc = _make_service(client=client)
        self.assertFalse(svc.remote_exists("ignored", "Missing"))


if __name__ == "__main__":
    unittest.main()
