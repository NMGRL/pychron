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
"""Unit tests for the dvc.make_url bridge-first hook (PR 3).

These tests exercise the new prioritisation logic in DVC.make_url without
spinning up a full DVC instance. We construct a stripped-down stand-in that
mirrors the relevant attributes (`application`, `organization`, `warning`)
so we can call the real method bound from `DVC`.
"""
import unittest
from types import MethodType
from unittest.mock import MagicMock

from pychron.dvc.dvc import DVC


class _FakeApp:
    def __init__(self, services, single):
        self._services = services
        self._single = single

    def get_services(self, _proto):
        return list(self._services)

    def get_service(self, _proto):
        return self._single


class _FakeService:
    def __init__(self, name, url, enabled=True):
        self.name = name
        self.enabled = enabled
        self._url = url
        self.calls = 0

    def make_url(self, name, organization, **kw):
        self.calls += 1
        return self._url


def _stand_in(services, single):
    """Build an object that has just enough surface for DVC.make_url to run."""
    obj = MagicMock()
    obj.application = _FakeApp(services, single)
    obj.organization = "ignored"
    obj.warning = MagicMock()
    obj.make_url = MethodType(DVC.make_url, obj)
    return obj


class DvcMakeUrlBridgeFirstTestCase(unittest.TestCase):
    def test_bridge_enabled_with_url_short_circuits(self):
        bridge = _FakeService("Bridge", "ssh://bridge/foo.git", enabled=True)
        github = _FakeService("GitHub", "ssh://github/foo.git", enabled=True)
        single = github
        target = _stand_in([bridge, github], single)

        url = target.make_url("Foo")

        self.assertEqual(url, "ssh://bridge/foo.git")
        self.assertEqual(bridge.calls, 1)
        self.assertEqual(github.calls, 0)

    def test_bridge_disabled_falls_back_to_legacy(self):
        bridge = _FakeService("Bridge", "ssh://bridge/foo.git", enabled=False)
        github = _FakeService("GitHub", "ssh://github/foo.git", enabled=True)
        single = github
        target = _stand_in([bridge, github], single)

        url = target.make_url("Foo")

        self.assertEqual(url, "ssh://github/foo.git")
        self.assertEqual(bridge.calls, 0)
        self.assertEqual(github.calls, 1)

    def test_bridge_empty_url_falls_back_and_warns(self):
        bridge = _FakeService("Bridge", "", enabled=True)
        github = _FakeService("GitHub", "ssh://github/foo.git", enabled=True)
        single = github
        target = _stand_in([bridge, github], single)

        url = target.make_url("Foo")

        self.assertEqual(url, "ssh://github/foo.git")
        self.assertEqual(bridge.calls, 1)
        self.assertEqual(github.calls, 1)
        target.warning.assert_called_once()

    def test_no_bridge_registered_uses_single_service_path(self):
        github = _FakeService("GitHub", "ssh://github/foo.git", enabled=True)
        target = _stand_in([github], github)

        url = target.make_url("Foo")

        self.assertEqual(url, "ssh://github/foo.git")
        self.assertEqual(github.calls, 1)

    def test_legacy_path_when_get_services_returns_none(self):
        github = _FakeService("GitHub", "ssh://github/foo.git", enabled=True)

        class _AppNone:
            organization = "ignored"

            def get_services(self, _p):
                return None

            def get_service(self, _p):
                return github

        obj = MagicMock()
        obj.application = _AppNone()
        obj.organization = "ignored"
        obj.warning = MagicMock()
        obj.make_url = MethodType(DVC.make_url, obj)

        url = obj.make_url("Foo")

        self.assertEqual(url, "ssh://github/foo.git")
        self.assertEqual(github.calls, 1)


if __name__ == "__main__":
    unittest.main()
