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
from __future__ import annotations

import os
import re
from itertools import groupby
from typing import Dict, List, Optional, Tuple, Union

# ============= local library imports  ==========================
from pychron.core.yaml import yload
from pychron.file_defaults import IDENTIFIERS_DEFAULT
from pychron.paths import paths
from pychron.pychron_constants import LINE_STR, SPECIAL_IDENTIFIER

IDENTIFIER_REGEX = re.compile(r"(?P<identifier>\d+)-(?P<aliquot>\d+)(?P<step>\w*)")
SPECIAL_IDENTIFIER_REGEX = re.compile(
    r"(?P<identifier>\w{1,2}-[\d\w]+-\w)-(?P<aliquot>\d+)"
)

ANALYSIS_MAPPING_UNDERSCORE_KEY: Dict[str, str] = dict()
ANALYSIS_MAPPING: Dict[str, str] = dict()
NON_EXTRACTABLE: Dict[str, str] = dict()
ANALYSIS_MAPPING_INTS: Dict[str, int] = dict()
SPECIAL_MAPPING: Dict[str, str] = dict()
SPECIAL_NAMES: List[str] = [SPECIAL_IDENTIFIER, LINE_STR]
SPECIAL_KEYS: List[str] = []


def load_identifiers_file() -> None:
    p = None
    if paths.hidden_dir:
        p = os.path.join(paths.hidden_dir, "identifiers.yaml")
    if p and os.path.isfile(p):
        yd = yload(p)
    else:
        yd = yload(IDENTIFIERS_DEFAULT)

    for i, idn_d in enumerate(yd):
        key = idn_d["shortname"]
        value = idn_d["name"]
        ANALYSIS_MAPPING[key] = value

        underscore_name = value.lower().replace(" ", "_")

        ANALYSIS_MAPPING_INTS[underscore_name] = i
        ANALYSIS_MAPPING_UNDERSCORE_KEY[underscore_name] = key

        if not idn_d["extractable"]:
            NON_EXTRACTABLE[key] = value

        if idn_d["special"]:
            SPECIAL_MAPPING[underscore_name] = key
            SPECIAL_NAMES.append(value)
            SPECIAL_KEYS.append(key)


try:
    load_identifiers_file()
except BaseException:
    import logging

    logging.getLogger(__name__).warning("failed loading identifier file")


def convert_identifier_to_int(ln: Union[str, int]) -> int:
    m = {"ba": 1, "bc": 2, "bu": 3, "bg": 4, "u": 5, "c": 6, "ic": 7}

    try:
        return int(ln)
    except ValueError:
        return m[ln]


def convert_special_name(
    name: Union[str, int], output: str = "shortname"
) -> Union[str, int]:
    if isinstance(name, str):
        name_lower = name.lower().replace(" ", "_")
        if name_lower in SPECIAL_MAPPING:
            sn = SPECIAL_MAPPING[name_lower]
            if output == "labnumber":
                sn = convert_identifier(sn)
            return sn
    return name


def convert_identifier(identifier: str) -> str:
    if "-" in identifier:
        ln = identifier.split("-")[0]
        try:
            int(ln)
            return str(ln)
        except ValueError:
            return identifier

    return identifier


def get_analysis_type(idn: str) -> str:
    idn = idn.lower()

    items = SPECIAL_MAPPING.items()

    def key(x: Tuple[str, str]) -> int:
        return len(x[1])

    for cnt, gitems in groupby(sorted(items, key=key, reverse=True), key=key):
        for atype, tag in gitems:
            if idn.startswith(tag):
                return atype

    return "unknown"


def get_analysis_type_shortname(idn: str) -> str:
    at = get_analysis_type(idn)
    if at != "unknown":
        at = SPECIAL_MAPPING[at]
    else:
        at = "u"
    return at


def strip_runid(r: str) -> Tuple[str, int, str]:
    l, x = r.split("-")

    a = ""
    for i, xi in enumerate(x):
        a += xi
        try:
            int(a)
        except ValueError:
            a = x[:i]
            s = x[i:]
            break
    else:
        s = ""

    return l, int(a), s


def make_identifier(ln: str, ed: Union[str, int], ms: Union[str, int]) -> str:
    try:
        _ = int(ln)
        return ln
    except ValueError:
        return make_special_identifier(ln, ed, ms)


def make_standard_identifier(
    ln: Union[str, int],
    modifier: Union[str, int],
    ms: Union[str, int],
    aliquot: Optional[int] = None,
) -> str:
    if isinstance(ms, int):
        ms = "{:02d}".format(ms)
    try:
        modifier = "{:02d}".format(modifier)
    except ValueError:
        pass

    d = "{}-{}-{}".format(ln, modifier, ms)
    if aliquot:
        d = "{}-{:02d}".format(d, aliquot)
    return d


def make_special_identifier(
    ln: Union[str, int], ed: Union[str, int], ms: Union[str, int], aliquot: Optional[Union[str, int]] = None
) -> str:
    if isinstance(ed, int):
        ed = "{:02d}".format(ed)
    if isinstance(ms, int):
        ms = "{:02d}".format(ms)

    d = "{}-{}-{}".format(ln, ed, ms)
    if aliquot:
        if not isinstance(aliquot, str):
            aliquot = "{:02d}".format(aliquot)

        d = "{}-{}".format(d, aliquot)
    return d


def is_special(ln: str) -> bool:
    if "-" in ln:
        return ln.split("-")[0] in ANALYSIS_MAPPING
    return False


STEPHEATRE = re.compile(r"^\d+-\d+[A_Z]{1,2}$")


def is_step_heat(runid: str) -> Optional[re.Match]:
    return STEPHEATRE.match(runid)


def convert_extract_device(name: str) -> str:
    n = ""
    if name:
        n = name.replace(" ", "")
    return n


def pretty_extract_device(ident: str) -> str:
    n = ""
    if ident:
        args = ident.split("_")
        if args[-1] in ("uv, co2"):
            n = " ".join([a.capitalize() for a in args[:-1]])
            n = "{} {}".format(n, args[-1].upper())
        else:
            n = " ".join([a.capitalize() for a in args])
    return n


# ============= EOF =============================================
