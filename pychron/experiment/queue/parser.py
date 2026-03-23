# ===============================================================================
# Copyright 2012 Jake Ross
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

# ============= enthought library imports =======================
# ============= standard library imports ========================
# ============= local library imports  ==========================
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from pychron.core.helpers.strtools import to_bool
from pychron.loggable import Loggable
from pychron.pychron_constants import (
    EXTRACT_VALUE,
    COLLECTION_TIME_ZERO_OFFSET,
    DELAY_AFTER,
    WEIGHT,
    RAMP_DURATION,
    POSTCLEANUP,
    PRECLEANUP,
    CLEANUP,
    DURATION,
    LIGHT_VALUE,
    BEAM_DIAMETER,
    USE_CDD_WARMING,
    POSITION,
    PATTERN,
    COMMENT,
    REPOSITORY_IDENTIFIER,
    OVERLAP,
    EXTRACT_UNITS,
    CRYO_TEMP,
    DISABLE_BETWEEN_POSITIONS,
    AUTOCENTER,
)
from pychron.regex import ALIQUOT_REGEX


class RunParser(Loggable):
    def parse(
        self, header: List[str], line: Union[str, List[str]], delim: str = "\t"
    ) -> Tuple[Dict[str, str], Dict[str, Any]]:
        params: Dict[str, Any] = {}
        if not isinstance(line, list):
            line = line.split(delim)

        args = [l.strip() for l in line]
        script_info = self._load_scripts(header, args)
        ln = args[header.index("labnumber")]
        if ALIQUOT_REGEX.match(ln):
            ln, a = ln.split("-")
            params["user_defined_aliquot"] = int(a)

        params["labnumber"] = ln

        self._load_strings(header, args, params)
        self._load_booleans(header, args, params)
        self._load_numbers(header, args, params)

        return script_info, params

    def _load_scripts(
        self, header: List[str], args: List[str]
    ) -> Dict[str, str]:
        script_info: Dict[str, str] = {}
        for attr in [
            "measurement",
            "extraction",
            ("script_options", "s_opt"),
            ("post_measurement", "post_meas"),
            ("post_equilibration", "post_eq"),
        ]:
            v = self._get_attr_value(header, args, attr)
            if v is not None:
                script_info[v[0]] = v[1]

        return script_info

    def _get_attr_value(
        self,
        header: List[str],
        args: List[str],
        attr: Union[str, Tuple[str, str]],
        cast: Optional[Callable[[str], Any]] = None,
    ) -> Optional[Tuple[str, Any]]:
        for hi, ai in self._get_attr(attr):
            idx = self._get_idx(header, ai)
            if idx:
                try:
                    v = args[idx]
                    if v.strip():
                        return hi, cast(v) if cast else v
                except IndexError:
                    pass

    def _load_strings(
        self, header: List[str], args: List[str], params: Dict[str, Any]
    ) -> None:
        for attr in [
            PATTERN,
            POSITION,
            COMMENT,
            ("syn_extraction_script", "syn_extraction"),
            OVERLAP,
            REPOSITORY_IDENTIFIER,
            ("conditionals", "truncate"),
            (EXTRACT_UNITS, "e_units"),
        ]:
            v = self._get_attr_value(header, args, attr)
            if v is not None:
                params[v[0]] = v[1]

    def _load_numbers(
        self, header: List[str], args: List[str], params: Dict[str, Any]
    ) -> None:
        for attr in [
            DURATION,
            CLEANUP,
            PRECLEANUP,
            POSTCLEANUP,
            CRYO_TEMP,
            (RAMP_DURATION, "ramp"),
            WEIGHT,
            DELAY_AFTER,
            (COLLECTION_TIME_ZERO_OFFSET, "t_o"),
            (EXTRACT_VALUE, "e_value"),
            (BEAM_DIAMETER, "beam_diam"),
            LIGHT_VALUE,
            "frequency_group",
        ]:
            v = self._get_attr_value(header, args, attr, cast=float)
            if v is not None:
                params[v[0]] = v[1]

    def _load_booleans(
        self, header: List[str], args: List[str], params: Dict[str, Any]
    ) -> None:
        for attr in [
            AUTOCENTER,
            USE_CDD_WARMING,
            (DISABLE_BETWEEN_POSITIONS, "dis_btw_pos"),
        ]:
            v = self._get_attr_value(
                header, args, attr, cast=lambda x: to_bool(x.strip())
            )
            if v is not None:
                params[v[0]] = v[1]

    def _get_attr(
        self, attr: Union[str, Tuple[str, str]]
    ) -> List[Tuple[str, str]]:
        if isinstance(attr, tuple):
            ref = attr[0]
            return [(ref, hi) for hi in attr]
        return [(attr, attr)]

    def _get_idx(self, header: List[str], attr: str) -> Optional[int]:
        try:
            return header.index(attr)
        except ValueError:
            pass
        return None


class UVRunParser(RunParser):
    def parse(
        self, header: List[str], line: Union[str, List[str]], delim: str = "\t"
    ) -> Tuple[Dict[str, str], Dict[str, Any]]:
        script_info, params = super().parse(header, line, delim)
        if not isinstance(line, list):
            line = line.split(delim)

        args = [l.strip() for l in line]

        def _set(attr: str, cast: Callable[[str], Any]) -> None:
            try:
                idx = self._get_idx(header, attr)
                if idx is not None:
                    v = args[idx]
                    params[attr] = cast(v)
            except (IndexError, ValueError, TypeError):
                pass

        _set("reprate", int)
        _set("attenuator", str)
        _set("mask", str)
        _set("image", str)

        return script_info, params


# ============= EOF =============================================
