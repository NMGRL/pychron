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
"""HTTP client for the Pychron Forgejo Bridge.

The bridge runs behind restricted Cloud Run, so callers must authenticate
twice: a Google-issued ID token in `Authorization: Bearer ...` (so Cloud
Run accepts the request at all) and a lab-scoped bridge bearer in
`X-Bridge-Token` (for app-level auth and lab scope).

This module wraps both flows so the rest of pychrondc can call simple
methods like `ensure_repository(...)`.
"""
from __future__ import absolute_import

import logging
import time
import uuid

import requests

logger = logging.getLogger(__name__)


class BridgeError(Exception):
    """Base class for bridge client errors."""


class BridgeAuthError(BridgeError):
    """401 from the bridge — bearer token is invalid or revoked."""


class BridgePermissionError(BridgeError):
    """403 from the bridge — token lacks the required scope or lab."""


class BridgeNotFound(BridgeError):
    """404 from the bridge — repository or lab not registered."""


class BridgeLabMismatch(BridgeError):
    """409 from the bridge — identifier already bound to a different lab."""


class BridgeUpstreamError(BridgeError):
    """5xx or transport failure after retries."""


def _load_id_token(sa_key_path, target_audience):
    """Mint a Google-issued ID token for Cloud Run invoker auth.

    Imported lazily so installations that disable the bridge don't pay the
    google-auth import cost on startup.
    """
    from google.oauth2 import service_account
    import google.auth.transport.requests

    creds = service_account.IDTokenCredentials.from_service_account_file(
        sa_key_path, target_audience=target_audience
    )
    creds.refresh(google.auth.transport.requests.Request())
    return creds.token


class BridgeClient(object):
    """Synchronous HTTP client. Safe to construct once per pychron session."""

    def __init__(
        self,
        base_url,
        bearer_token,
        service_account_key_path,
        timeout=30.0,
        retry_backoff=0.5,
    ):
        self._base_url = base_url.rstrip("/")
        self._bearer = bearer_token
        self._sa_key_path = service_account_key_path
        self._timeout = timeout
        self._retry_backoff = retry_backoff

    # -- public API ----------------------------------------------------

    def healthz(self):
        """Cheap unauthenticated probe. Returns True iff the bridge is up."""
        try:
            resp = requests.get(self._base_url + "/healthz", timeout=self._timeout)
            return resp.status_code == 200 and resp.json().get("status") == "ok"
        except requests.RequestException:
            return False

    def ensure_repository(
        self,
        repository_identifier,
        lab_name,
        instrument=None,
        project=None,
        principal_investigator=None,
        irradiation=None,
        material=None,
        private=True,
    ):
        body = {
            "repository_identifier": repository_identifier,
            "lab": lab_name,
            "instrument": instrument,
            "project": project,
            "principal_investigator": principal_investigator,
            "irradiation": irradiation,
            "material": material,
            "private": private,
        }
        # Strip None values — the bridge accepts nullable fields but the
        # smaller payload makes logs easier to read.
        body = {k: v for k, v in body.items() if v is not None}
        return self._request("POST", "/v1/repositories/ensure", json=body)

    def lookup_repository(self, repository_identifier):
        try:
            return self._request(
                "GET", "/v1/repositories/{}".format(repository_identifier)
            )
        except BridgeNotFound:
            return None

    def list_repositories(
        self, lab=None, instrument=None, project=None, limit=100, offset=0
    ):
        params = {"limit": limit, "offset": offset}
        if lab:
            params["lab"] = lab
        if instrument:
            params["instrument"] = instrument
        if project:
            params["project"] = project
        return self._request("GET", "/v1/repositories", params=params)

    def validate_repository(self, repository_identifier):
        return self._request(
            "POST",
            "/v1/repositories/{}/validate".format(repository_identifier),
        )

    # -- internals -----------------------------------------------------

    def _headers(self):
        id_token = _load_id_token(self._sa_key_path, self._base_url)
        return {
            "Authorization": "Bearer {}".format(id_token),
            "X-Bridge-Token": self._bearer,
            "X-Request-Id": uuid.uuid4().hex,
            "Accept": "application/json",
        }

    def _request(self, method, path, json=None, params=None):
        url = self._base_url + path
        headers = self._headers()
        request_id = headers["X-Request-Id"]

        last_err = None
        for attempt in (1, 2):
            try:
                resp = requests.request(
                    method,
                    url,
                    headers=headers,
                    json=json,
                    params=params,
                    timeout=self._timeout,
                )
            except requests.RequestException as exc:
                last_err = exc
                logger.warning(
                    "bridge transport error attempt=%s url=%s request_id=%s err=%s",
                    attempt,
                    url,
                    request_id,
                    exc,
                )
                if attempt == 1:
                    time.sleep(self._retry_backoff)
                    continue
                raise BridgeUpstreamError(
                    "transport failed after retry: {}".format(exc)
                ) from exc

            if 500 <= resp.status_code < 600:
                logger.warning(
                    "bridge 5xx attempt=%s url=%s request_id=%s status=%s body=%s",
                    attempt,
                    url,
                    request_id,
                    resp.status_code,
                    resp.text[:200],
                )
                if attempt == 1:
                    time.sleep(self._retry_backoff)
                    continue
                raise BridgeUpstreamError(
                    "{} {} -> {}".format(method, path, resp.status_code)
                )

            self._raise_for_status(method, path, resp)
            logger.info(
                "bridge ok method=%s path=%s request_id=%s status=%s",
                method,
                path,
                request_id,
                resp.status_code,
            )
            return resp.json() if resp.text else {}

        # Defensive: should not reach here.
        raise BridgeUpstreamError("unreachable: {}".format(last_err))

    @staticmethod
    def _raise_for_status(method, path, resp):
        if resp.status_code == 401:
            raise BridgeAuthError("{} {} -> 401 {}".format(method, path, resp.text))
        if resp.status_code == 403:
            raise BridgePermissionError(
                "{} {} -> 403 {}".format(method, path, resp.text)
            )
        if resp.status_code == 404:
            raise BridgeNotFound("{} {} -> 404".format(method, path))
        if resp.status_code == 409:
            raise BridgeLabMismatch(
                "{} {} -> 409 {}".format(method, path, resp.text)
            )
        if resp.status_code >= 400:
            raise BridgeError("{} {} -> {} {}".format(method, path, resp.status_code, resp.text))


# ============= EOF =============================================
