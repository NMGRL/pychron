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

import requests
from envisage.ui.tasks.preferences_pane import PreferencesPane
from traits.api import Bool, Button, Password, Str
from traitsui.api import Color, Group, HGroup, Item, View, VGroup

from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.envisage.tasks.base_preferences_helper import (
    BasePreferencesHelper,
    test_connection_item,
)
from pychron.globals import globalv


class BridgePreferences(BasePreferencesHelper):
    """Preferences for the Pychron Forgejo Bridge service.

    The bridge maps a Pychron repository_identifier to a Forgejo owner/repo
    on demand. When `enabled` is False, this preference pane has no effect
    on the existing GitHub/GitLab paths.
    """

    preferences_path = "pychron.bridge"

    enabled = Bool(False)
    base_url = Str
    bearer_token = Password
    service_account_key_path = Str
    lab_name = Str

    test_connection = Button
    _remote_status = Str
    _remote_status_color = Color

    def _test_connection_fired(self):
        self._remote_status_color = "red"
        self._remote_status = "Invalid"
        if not self.base_url:
            self._remote_status = "No URL"
            return
        try:
            url = self.base_url.rstrip("/") + "/healthz"
            resp = requests.get(url, timeout=10, verify=globalv.cert_file)
            if resp.status_code == 200 and resp.json().get("status") == "ok":
                self._remote_status = "Valid"
                self._remote_status_color = "green"
            else:
                self._remote_status = "Invalid ({})".format(resp.status_code)
        except requests.RequestException as e:
            self._remote_status = "Invalid"
            self.debug("Bridge connection test failed {}: {}".format(self.base_url, e))


class BridgePreferencesPane(PreferencesPane):
    model_factory = BridgePreferences
    category = "Bridge"

    def traits_view(self):
        cred = VGroup(
            Item(
                "enabled",
                tooltip="Route repository_identifier resolution through the "
                "Pychron Forgejo Bridge. When off, GitHub/GitLab paths are "
                "used as before.",
            ),
            Item(
                "base_url",
                tooltip="Cloud Run URL of the bridge service, e.g. "
                "https://pychron-forgejo-bridge-xyz-uc.a.run.app",
                resizable=True,
            ),
            Item(
                "bearer_token",
                tooltip="Lab-scoped bridge token minted via /v1/tokens.",
                resizable=True,
            ),
            Item(
                "service_account_key_path",
                tooltip="Filesystem path to a Google service account JSON key "
                "with roles/run.invoker on the bridge service.",
                resizable=True,
                label="SA Key Path",
            ),
            Item(
                "lab_name",
                tooltip="Lab name as registered in the bridge (matches the "
                "Lab.name column in the bridge database, e.g. NMGRL).",
            ),
            HGroup(
                test_connection_item(),
                CustomLabel(
                    "_remote_status",
                    width=80,
                    color_name="_remote_status_color",
                ),
            ),
            show_border=True,
            label="Pychron Forgejo Bridge",
        )

        return View(Group(cred))


# ============= EOF =============================================
