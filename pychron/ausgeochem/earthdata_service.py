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

import re
from datetime import datetime

import requests
from traits.api import Str
from uncertainties import nominal_value, std_dev

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

AGE_SUMMARY_FIELDS = (
    "age",
    "ageCalcTypeId",
    "ageCalcTypeName",
    "ageUncertainty",
    "ageUncertaintyTypeId",
    "ageUncertaintyTypeName",
    "agepvalue",
    "arArDataPointId",
    "calculatedAgeUncertaintyTypeId",
    "calculatedAgeUncertaintyTypeName",
    "calculatedAgeUncertaintyTypeUnitsId",
    "calculatedAgeUncertaintyTypeUnitsName",
    "dataInterpretationToolId",
    "dataInterpretationToolName",
    "description",
    "id",
    "interpretationId",
    "interpretationName",
    "mswd",
    "nAnalysisGrouped",
    "preferredAge",
)

DATA_POINT_FIELDS = (
    "analysisDate",
    "analysisScaleId",
    "analysisScaleName",
    "analysisUnits",
    "analyticalUncertaintyTypeId",
    "analyticalUncertaintyTypeName",
    "analyticalUncertaintyUnitId",
    "analyticalUncertaintyUnitName",
    "apparentAgeUncertaintyTypeId",
    "apparentAgeUncertaintyTypeName",
    "apparentAgeUncertaintyUnitId",
    "apparentAgeUncertaintyUnitName",
    "arArAnalyticalSetUpId",
    "arMethodId",
    "arMethodName",
    "commentAnalyte",
    "grainDiameterMax",
    "grainDiameterMin",
    "id",
    "irradiationBatchIDId",
    "jvalueUncertaintyUnitId",
    "jvalueUncertaintyUnitName",
    "lithologyId",
    "lithologyName",
    "mineralId",
    "mineralName",
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

    def build_age_summary_payload(self, analysis_group=None, **overrides):
        """Map an AnalysisGroup into an ArArAgeSummaryDTO structure."""

        payload = dict(((field, None) for field in AGE_SUMMARY_FIELDS))
        payload.update(overrides)

        if analysis_group is None:
            return self._cleanup_payload(payload)

        pv = analysis_group.get_preferred_obj("age")
        calc_name = getattr(pv, "computed_kind", pv.kind)
        age_units = getattr(getattr(analysis_group, "arar_constants", None), "age_units", "Ma")
        scaled_age = analysis_group.get_ma_scaled_age()
        mswd, _, _, pvalue = analysis_group.get_preferred_mswd_tuple()

        payload.setdefault("age", float(nominal_value(scaled_age)))
        payload.setdefault("ageUncertainty", float(std_dev(scaled_age)))
        payload.setdefault("ageCalcTypeName", calc_name)
        payload.setdefault("ageUncertaintyTypeName", pv.error_kind)
        payload.setdefault("calculatedAgeUncertaintyTypeName", pv.error_kind)
        payload.setdefault("calculatedAgeUncertaintyTypeUnitsName", age_units)
        payload.setdefault("nAnalysisGrouped", analysis_group.nanalyses)
        payload.setdefault("mswd", mswd)
        payload.setdefault("agepvalue", pvalue)
        payload.setdefault("preferredAge", True)
        payload.setdefault("dataInterpretationToolName", "Pychron")
        payload.setdefault(
            "description", self._analysis_group_description(analysis_group)
        )
        payload.setdefault(
            "interpretationName",
            self._interpretation_name(analysis_group, calc_name),
        )

        return self._cleanup_payload(payload)

    def build_data_point_payload(self, analysis_group=None, analysis=None, **overrides):
        """Map an Analysis or AnalysisGroup to an ArArDataPointDTO."""

        payload = dict(((field, None) for field in DATA_POINT_FIELDS))
        payload.update(overrides)

        if analysis is None and analysis_group is not None:
            analysis = analysis_group.analyses[0] if analysis_group.analyses else None

        if analysis is None:
            return self._cleanup_payload(payload)

        grain_min, grain_max = self._parse_grain_size(
            getattr(analysis, "grainsize", None)
            or getattr(analysis_group, "grainsize", None)
        )
        payload.setdefault("analysisDate", self._format_analysis_date(analysis))
        payload.setdefault("analysisUnits", "fA")
        payload.setdefault(
            "analysisScaleName", self._analysis_scale_name(analysis_group)
        )
        payload.setdefault(
            "analyticalUncertaintyTypeName",
            getattr(analysis_group, "age_error_kind", None),
        )
        payload.setdefault("analyticalUncertaintyUnitName", "Absolute")
        payload.setdefault(
            "apparentAgeUncertaintyTypeName",
            getattr(analysis_group, "age_error_kind", None),
        )
        payload.setdefault("apparentAgeUncertaintyUnitName", "Absolute")
        payload.setdefault(
            "arMethodName",
            getattr(analysis, "experiment_type", None)
            or getattr(analysis, "analysis_type", None),
        )
        payload.setdefault("commentAnalyte", self._analysis_comment(analysis))
        payload.setdefault("grainDiameterMin", grain_min)
        payload.setdefault("grainDiameterMax", grain_max)
        payload.setdefault(
            "lithologyName",
            getattr(analysis_group, "lithology", None)
            or getattr(analysis, "lithology", None),
        )
        payload.setdefault(
            "mineralName",
            getattr(analysis_group, "material", None)
            or getattr(analysis, "material", None),
        )
        payload.setdefault("jvalueUncertaintyUnitName", "Absolute")

        return self._cleanup_payload(payload)

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

    def _analysis_group_description(self, analysis_group):
        pieces = []
        sample = getattr(analysis_group, "sample", None)
        project = getattr(analysis_group, "project", None)
        comments = getattr(analysis_group, "comments", None)

        if sample:
            pieces.append("Sample {}".format(sample))
        if project:
            pieces.append("Project {}".format(project))
        if comments:
            pieces.append(comments)

        return "; ".join(pieces) if pieces else None

    def _interpretation_name(self, analysis_group, calc_name):
        sample = getattr(analysis_group, "sample", None)
        if sample and calc_name:
            return "{} {}".format(sample, calc_name)
        if sample:
            return sample
        return calc_name

    def _format_analysis_date(self, analysis):
        dt = getattr(analysis, "rundate", None)
        if dt is None:
            ts = getattr(analysis, "timestamp", None)
            if isinstance(ts, datetime):
                dt = ts
            elif isinstance(ts, (int, float)):
                dt = datetime.fromtimestamp(ts)
        if dt is None:
            return None
        try:
            return dt.strftime("%d/%m/%Y")
        except (AttributeError, ValueError):
            return None

    def _analysis_scale_name(self, analysis_group):
        if analysis_group is None:
            return None
        n = analysis_group.nanalyses if analysis_group.nanalyses else 0
        if n == 1:
            return "Single analysis"
        if n > 1:
            return "{} analyses".format(n)
        return None

    def _analysis_comment(self, analysis):
        comments = []
        for attr in ("sample_note", "sample_prep_comment"):
            val = getattr(analysis, attr, None)
            if val:
                comments.append(val)
        return "; ".join(comments) if comments else None

    def _parse_grain_size(self, grainsize):
        if not grainsize:
            return None, None
        values = [float(v) for v in re.findall(r"[0-9]+\.?[0-9]*", str(grainsize))]
        if not values:
            return None, None
        if len(values) == 1:
            return values[0], values[0]
        return min(values), max(values)


# ============= EOF =============================================
