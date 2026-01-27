# ===============================================================================
# Copyright 2024 Pychron Developers
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

from __future__ import absolute_import

import requests
from traits.api import Str

from pychron.core.ui.preference_binding import bind_preference
from pychron.loggable import Loggable

AGE_CALC_FIELDS = (
    "airRatioId",
    "airRatioName",
    "arArDataPointId",
    "comment",
    "decayConstantId",
    "decayConstantName",
    "fluxMonitorId",
    "fluxMonitorName",
    "id",
)


class AusGeochemEarthDataService(Loggable):
    """HTTP helper for the AusGeochem EarthData API."""

    base_url = Str("https://app.ausgeochem.org")
    username = Str
    password = Str

    _token = None

    def __init__(self, bind=True, *args, **kw):
        super(AusGeochemEarthDataService, self).__init__(*args, **kw)
        self._session = requests.Session()
        if bind:
            self._bind_preferences()

    # ------------------------------------------------------------------
    # public API
    def test_connection(self):
        """Ping the account endpoint to verify credentials."""

        resp = self._request("get", "/api/account")
        return bool(resp and resp.ok)

    def create_age_calculation(self, dto):
        """Create an Ar/Ar age calculation record.

        Parameters
        ----------
        dto : dict
            Payload matching ``ArArAgeCalcDTO``. ``None`` values are removed
            before submission.
        """

        payload = self._cleanup_payload(dto)
        resp = self._request(
            "post",
            "/api/arar/ArArAgeCalc",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        if resp is None:
            return

        if not resp.content:
            return None

        try:
            return resp.json()
        except ValueError:
            return resp.text

    def build_age_calc_payload(self, analysis_group=None, **overrides):
        """Build a DTO skeleton from an analysis group and manual overrides."""

        payload = dict(((field, None) for field in AGE_CALC_FIELDS))
        payload.update(overrides)

        if analysis_group is not None:
            payload.setdefault("comment", self._default_comment(analysis_group))
            payload.setdefault("fluxMonitorName", getattr(analysis_group, "monitor_info", None))

        return self._cleanup_payload(payload)

    def upload_analysis_group(self, analysis_group, **overrides):
        """Helper that builds and submits an age calculation DTO."""

        payload = self.build_age_calc_payload(analysis_group, **overrides)
        if not payload:
            self.warning("AusGeochem payload is empty; nothing to upload")
            return

        return self.create_age_calculation(payload)

    # ------------------------------------------------------------------
    # private helpers
    def _bind_preferences(self):
        prefid = "pychron.ausgeochem"
        bind_preference(self, "base_url", "{}.base_url".format(prefid))
        bind_preference(self, "username", "{}.username".format(prefid))
        bind_preference(self, "password", "{}.password".format(prefid))

    def _ensure_token(self):
        if self._token:
            return self._token

        if not self.username or not self.password:
            self.warning("AusGeochem credentials are not configured")
            return

        payload = {
            "username": self.username,
            "password": self.password,
            "rememberMe": False,
        }

        url = self._url("/api/authenticate")
        try:
            resp = self._session.post(url, json=payload, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as exc:
            self.warning("AusGeochem authentication failed: {}".format(exc))
            return

        token = resp.json().get("id_token")
        if not token:
            self.warning("AusGeochem authentication response did not include a token")
            return

        self._token = token
        return token

    def _request(self, method, path, require_auth=True, **kw):
        url = self._url(path)
        headers = kw.pop("headers", {})
        timeout = kw.pop("timeout", 30)

        if require_auth:
            token = self._ensure_token()
            if not token:
                return
            headers.setdefault("Authorization", "Bearer {}".format(token))

        try:
            resp = self._session.request(
                method, url, headers=headers, timeout=timeout, **kw
            )
        except requests.RequestException as exc:
            self.warning("AusGeochem request error ({}): {}".format(path, exc))
            return

        if resp.status_code == 401 and require_auth:
            self.debug("Token expired, refreshing and retrying request")
            self._token = None
            token = self._ensure_token()
            if not token:
                return
            headers["Authorization"] = "Bearer {}".format(token)
            try:
                resp = self._session.request(
                    method, url, headers=headers, timeout=timeout, **kw
                )
            except requests.RequestException as exc:
                self.warning("AusGeochem retry failed ({}): {}".format(path, exc))
                return

        if not resp.ok:
            self.warning(
                "AusGeochem request failed ({} {}): {}".format(
                    method.upper(), path, resp.text
                )
            )
            return

        return resp

    def _url(self, path):
        if path.startswith("http"):
            return path
        if not path.startswith("/"):
            path = "/" + path
        return "{}{}".format(self.base_url.rstrip("/"), path)

    def _cleanup_payload(self, payload):
        return {k: v for k, v in payload.items() if v not in (None, "")}

    def _default_comment(self, analysis_group):
        sample = getattr(analysis_group, "sample", None)
        project = getattr(analysis_group, "project", None)
        if sample and project:
            return "{} ({})".format(sample, project)
        if sample:
            return sample
        return None


# ============= EOF =============================================
