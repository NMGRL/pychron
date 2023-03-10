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
    def parse(self, header, line, delim="\t"):
        params = dict()
        if not isinstance(line, list):
            line = line.split(delim)

        args = [l.strip() for l in line]
        script_info = self._load_scripts(header, args)
        ln = args[header.index("labnumber")]
        if ALIQUOT_REGEX.match(ln):
            ln, a = ln.split("-")
            # params['aliquot'] = int(a)
            params["user_defined_aliquot"] = int(a)

        params["labnumber"] = ln

        # load strings
        self._load_strings(header, args, params)

        # load booleans
        self._load_booleans(header, args, params)

        # load numbers
        self._load_numbers(header, args, params)

        return script_info, params

    def _load_scripts(self, header, args):
        script_info = dict()
        # load scripts
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

    def _get_attr_value(self, header, args, attr, cast=None):
        for hi, ai in self._get_attr(attr):
            idx = self._get_idx(header, ai)
            # print header
            # print hi, ai, idx
            if idx:
                try:
                    v = args[idx]
                    if v.strip():
                        return hi, cast(v) if cast else v
                except IndexError as e:
                    pass
                    # print 'exception', e, attr, idx, args

    def _load_strings(self, header, args, params):
        for attr in [
            PATTERN,
            POSITION,
            COMMENT,
            "syn_extraction",
            OVERLAP,
            REPOSITORY_IDENTIFIER,
            ("conditionals", "truncate"),
            (EXTRACT_UNITS, "e_units"),
        ]:
            v = self._get_attr_value(header, args, attr)
            # print attr, v
            if v is not None:
                params[v[0]] = v[1]

    def _load_numbers(self, header, args, params):
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

    def _load_booleans(self, header, args, params):
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

    def _get_attr(self, attr):
        if isinstance(attr, tuple):
            ref = attr[0]
            return [(ref, hi) for hi in attr]
        else:
            return [(attr, attr)]

    def _get_idx(self, header, attr):
        try:
            return header.index(attr)
        except ValueError:
            pass


class UVRunParser(RunParser):
    def parse(self, header, line, delim="\t"):
        script_info, params = super(UVRunParser, self).parse(header, line, delim)
        if not isinstance(line, list):
            line = line.split(delim)

        args = [l.strip() for l in line]

        def _set(attr, cast):
            try:
                idx = self._get_idx(header, attr)
                v = args[idx]
                params[attr] = cast(v)
            except (IndexError, ValueError, TypeError) as e:
                # print 'exception', e
                pass

        _set("reprate", int)
        _set("attenuator", str)
        _set("mask", str)
        _set("image", str)

        return script_info, params

        # ============= EOF =============================================
