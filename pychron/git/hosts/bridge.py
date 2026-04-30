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
"""Bridge git host service.

Implements the IGitHost interface against the Pychron Forgejo Bridge so
the existing add_repository / clone / make_url orchestration can route
through the bridge with no changes to its callers.
"""
from __future__ import absolute_import

from apptools.preferences.api import bind_preference
from traits.api import Bool, Str

from pychron.git.hosts import GitHostService
from pychron.git.hosts._bridge_client import (
    BridgeAuthError,
    BridgeClient,
    BridgeError,
    BridgeLabMismatch,
    BridgeNotFound,
    BridgePermissionError,
)


class BridgeService(GitHostService):
    """Routes repository operations through the Pychron Forgejo Bridge."""

    name = "Bridge"
    preference_path = "pychron.bridge"

    enabled = Bool(False)
    base_url = Str
    bearer_token = Str
    service_account_key_path = Str
    lab_name = Str

    def __init__(self, *args, **kw):
        super(BridgeService, self).__init__(*args, **kw)
        self._client = None
        self._url_cache = {}

    def bind_preferences(self):
        bind_preference(self, "enabled", "{}.enabled".format(self.preference_path))
        bind_preference(self, "base_url", "{}.base_url".format(self.preference_path))
        bind_preference(
            self, "bearer_token", "{}.bearer_token".format(self.preference_path)
        )
        bind_preference(
            self,
            "service_account_key_path",
            "{}.service_account_key_path".format(self.preference_path),
        )
        bind_preference(self, "lab_name", "{}.lab_name".format(self.preference_path))

    def set_authentication(self):
        # Bridge auth is handled per-request via the BridgeClient. SSH push
        # still uses the workstation's existing SSH config (the bridge does
        # not proxy git traffic). No-op here, matching BaseGitHostService.
        return

    def test_api(self):
        c = self._get_client()
        if c is None:
            return False
        return c.healthz()

    def create_repo(self, name, organization, **kw):
        """Ensure the repository exists in Forgejo, creating it if needed.

        `organization` is ignored — the bridge derives the Forgejo org from
        the lab. This signature matches GitHubService.create_repo so the
        host registry can drive both.
        """
        c = self._get_client()
        if c is None:
            return False

        try:
            payload = c.ensure_repository(
                repository_identifier=name,
                lab_name=self.lab_name,
                instrument=kw.get("instrument"),
                project=kw.get("project"),
                principal_investigator=kw.get("principal_investigator"),
                irradiation=kw.get("irradiation"),
                material=kw.get("material"),
                private=kw.get("private", True),
            )
        except BridgeLabMismatch as exc:
            self.warning("Bridge create_repo lab mismatch: {}".format(exc))
            return False
        except (BridgeAuthError, BridgePermissionError) as exc:
            self.warning("Bridge auth failure: {}".format(exc))
            return False
        except BridgeError as exc:
            self.warning("Bridge create_repo failed: {}".format(exc))
            return False

        ssh_url = payload.get("clone_url_ssh")
        if ssh_url:
            self._url_cache[name] = ssh_url
        return True

    def make_url(self, name, organization, protocol=None):
        """Resolve `name` to a clone URL.

        Returns the bridge SSH URL when known, otherwise returns an empty
        string so the caller can fall back to its legacy URL construction.
        """
        cached = self._url_cache.get(name)
        if cached:
            return cached

        c = self._get_client()
        if c is None:
            return ""

        try:
            payload = c.lookup_repository(name)
        except BridgeError as exc:
            self.warning("Bridge make_url lookup failed for {}: {}".format(name, exc))
            return ""

        if payload is None:
            return ""

        url = payload.get("clone_url_ssh", "")
        if url:
            self._url_cache[name] = url
        return url

    def remote_exists(self, organization, name):
        c = self._get_client()
        if c is None:
            return False
        try:
            return c.lookup_repository(name) is not None
        except BridgeError:
            return False

    def get_repo(self, organization, name):
        c = self._get_client()
        if c is None:
            return None
        try:
            payload = c.lookup_repository(name)
        except BridgeError:
            return None
        if not payload:
            return None
        return {
            "name": payload.get("forgejo_repo", name),
            "ssh_url": payload.get("clone_url_ssh", ""),
            "clone_url": payload.get("clone_url_https", ""),
        }

    def get_repos(self, org):
        c = self._get_client()
        if c is None:
            return []
        try:
            payload = c.list_repositories(lab=self.lab_name)
        except BridgeError:
            return []
        return payload.get("repositories", [])

    def get_repository_names(self, organization):
        return [r.get("repository_identifier") for r in self.get_repos(organization)]

    def test_connection(self, organization):
        return self.test_api()

    # -- internals -----------------------------------------------------

    def _get_client(self):
        if not self.enabled:
            return None
        if not (self.base_url and self.bearer_token and self.service_account_key_path):
            self.warning(
                "Bridge enabled but base_url / bearer_token / SA key path is empty; "
                "skipping bridge call."
            )
            return None
        if self._client is None:
            self._client = BridgeClient(
                base_url=self.base_url,
                bearer_token=self.bearer_token,
                service_account_key_path=self.service_account_key_path,
            )
        return self._client


# ============= EOF =============================================
