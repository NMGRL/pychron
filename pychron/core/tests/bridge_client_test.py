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
from unittest.mock import MagicMock, patch

import requests

from pychron.git.hosts import _bridge_client
from pychron.git.hosts._bridge_client import (
    BridgeAuthError,
    BridgeClient,
    BridgeLabMismatch,
    BridgeNotFound,
    BridgePermissionError,
    BridgeUpstreamError,
)


def _make_response(status, json_body=None, text=""):
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status
    resp.text = text or (str(json_body) if json_body else "")
    resp.json.return_value = json_body or {}
    return resp


class BridgeClientHeadersTestCase(unittest.TestCase):
    def setUp(self):
        self._id_patch = patch.object(
            _bridge_client, "_load_id_token", return_value="fake-id-token"
        )
        self._id_patch.start()
        self.client = BridgeClient(
            base_url="https://bridge.test",
            bearer_token="lab-bearer",
            service_account_key_path="/dev/null",
            retry_backoff=0,
        )

    def tearDown(self):
        self._id_patch.stop()

    def test_headers_include_id_token_and_bridge_bearer(self):
        with patch.object(_bridge_client.requests, "request") as req:
            req.return_value = _make_response(200, {"status": "ok"})
            self.client.lookup_repository("Foo_001")

        kwargs = req.call_args.kwargs
        headers = kwargs["headers"]
        self.assertEqual(headers["Authorization"], "Bearer fake-id-token")
        self.assertEqual(headers["X-Bridge-Token"], "lab-bearer")
        self.assertIn("X-Request-Id", headers)


class BridgeClientStatusMappingTestCase(unittest.TestCase):
    def setUp(self):
        self._id_patch = patch.object(
            _bridge_client, "_load_id_token", return_value="fake"
        )
        self._id_patch.start()
        self.client = BridgeClient(
            base_url="https://bridge.test",
            bearer_token="bear",
            service_account_key_path="/dev/null",
            retry_backoff=0,
        )

    def tearDown(self):
        self._id_patch.stop()

    def _patch_request(self, response):
        return patch.object(
            _bridge_client.requests, "request", return_value=response
        )

    def test_401_maps_to_auth_error(self):
        with self._patch_request(_make_response(401)):
            with self.assertRaises(BridgeAuthError):
                self.client.ensure_repository("X_001", "NMGRL")

    def test_403_maps_to_permission_error(self):
        with self._patch_request(_make_response(403)):
            with self.assertRaises(BridgePermissionError):
                self.client.ensure_repository("X_001", "NMGRL")

    def test_404_lookup_returns_none(self):
        with self._patch_request(_make_response(404)):
            self.assertIsNone(self.client.lookup_repository("Missing"))

    def test_404_validate_raises_not_found(self):
        with self._patch_request(_make_response(404)):
            with self.assertRaises(BridgeNotFound):
                self.client.validate_repository("Missing")

    def test_409_maps_to_lab_mismatch(self):
        with self._patch_request(_make_response(409, text="diff lab")):
            with self.assertRaises(BridgeLabMismatch):
                self.client.ensure_repository("X_001", "NMGRL")


class BridgeClientRetryTestCase(unittest.TestCase):
    def setUp(self):
        self._id_patch = patch.object(
            _bridge_client, "_load_id_token", return_value="fake"
        )
        self._id_patch.start()
        self._sleep_patch = patch.object(_bridge_client.time, "sleep")
        self._sleep_patch.start()
        self.client = BridgeClient(
            base_url="https://bridge.test",
            bearer_token="bear",
            service_account_key_path="/dev/null",
            retry_backoff=0,
        )

    def tearDown(self):
        self._id_patch.stop()
        self._sleep_patch.stop()

    def test_5xx_retries_then_raises_upstream_error(self):
        with patch.object(
            _bridge_client.requests,
            "request",
            side_effect=[_make_response(503), _make_response(503)],
        ) as req:
            with self.assertRaises(BridgeUpstreamError):
                self.client.lookup_repository("Foo")
        self.assertEqual(req.call_count, 2)

    def test_5xx_then_200_succeeds(self):
        responses = [
            _make_response(503),
            _make_response(
                200,
                {
                    "repository_identifier": "Foo",
                    "clone_url_ssh": "ssh://x",
                    "clone_url_https": "https://x",
                },
            ),
        ]
        with patch.object(
            _bridge_client.requests, "request", side_effect=responses
        ) as req:
            payload = self.client.lookup_repository("Foo")
        self.assertEqual(req.call_count, 2)
        self.assertEqual(payload["clone_url_ssh"], "ssh://x")

    def test_transport_error_retries_then_raises(self):
        with patch.object(
            _bridge_client.requests,
            "request",
            side_effect=requests.ConnectionError("nope"),
        ) as req:
            with self.assertRaises(BridgeUpstreamError):
                self.client.lookup_repository("Foo")
        self.assertEqual(req.call_count, 2)


class BridgeClientHealthzTestCase(unittest.TestCase):
    def test_healthz_does_not_send_auth_headers(self):
        client = BridgeClient(
            base_url="https://bridge.test",
            bearer_token="bear",
            service_account_key_path="/dev/null",
        )
        with patch.object(_bridge_client.requests, "get") as g:
            g.return_value = _make_response(200, {"status": "ok"})
            self.assertTrue(client.healthz())
            self.assertEqual(g.call_args.args[0], "https://bridge.test/healthz")
            self.assertNotIn("headers", g.call_args.kwargs)


if __name__ == "__main__":
    unittest.main()
