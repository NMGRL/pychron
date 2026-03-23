# ===============================================================================
# Copyright 2013 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
from __future__ import annotations

import re
from typing import Callable, List, Tuple, Union

# ============= standard library imports ========================
# ============= local library imports  ==========================


def pos_gen(s: int, e: int, inc: int = 1) -> List[int]:
    if s > e:
        inc *= -1
    return list(range(s, e + inc, inc))


def increment_list(ps: List[int], start: int = 0) -> List[int]:
    if len(ps) == 1:
        return [ps[0] + 1]
    else:
        s, e, o = ps[0], ps[-1], ps[1] - ps[0]
        if start:
            n = start
        else:
            n = e - s + o

        return [p + n for p in ps]


def slice_func(pos: str) -> List[int]:
    s, e = pos.split("-")
    return pos_gen(int(s), int(e))


def islice_func(pos: str, start: int = 0) -> str:
    ps = slice_func(pos)
    nls = increment_list(ps, start)
    return "{}-{}".format(nls[0], nls[-1])


def sslice_func(pos: str) -> List[int]:
    s, e, inc = pos.split(":")

    return pos_gen(int(s), int(e), int(inc))


def isslice_func(pos: str) -> str:
    ps = sslice_func(pos)
    nls = increment_list(ps)
    step = nls[1] - nls[0]
    return "{}:{}:{}".format(nls[0], nls[-1], step)


def pslice_func(pos: str) -> List[int]:
    s, e = pos.split(":")
    return pos_gen(int(s), int(e))


def ipslice_func(pos: str) -> str:
    ps = pslice_func(pos)
    nls = increment_list(ps)
    return "{}:{}".format(nls[0], nls[-1])


def cslice_func(pos: str) -> List[int]:
    args = pos.split(";")
    positions = []
    for ai in args:
        if "-" in ai:
            positions.extend(slice_func(ai))
        else:
            positions.append(int(ai))
    return positions


def icslice_func(pos: str) -> str:
    args = pos.split(";")
    ns = []
    x = args[-1]

    if "-" in x:
        start = int(x.split("-")[-1])
    else:
        start = int(x)

    for ai in args:
        if "-" in ai:
            ns.append(islice_func(ai, start))
        else:
            ns.append(str(int(ai) + start))

    return ";".join(ns)


SLICE_REGEX: Tuple[re.Pattern, Callable[[str], List[int]], Callable[[str, int], str], str] = (
    re.compile(r"[\d]+-{1}[\d]+$"),
    slice_func,
    islice_func,
    "Slice",
)
SSLICE_REGEX: Tuple[re.Pattern, Callable[[str], List[int]], Callable[[str], str], str] = (
    re.compile(r"\d+:{1}\d+:{1}\d+$"),
    sslice_func,
    isslice_func,
    "SSlice",
)
PSLICE_REGEX: Tuple[re.Pattern, Callable[[str], List[int]], Callable[[str], str], str] = (
    re.compile(r"\d+:{1}\d+$"),
    pslice_func,
    ipslice_func,
    "PSlice",
)

CSLICE_REGEX: Tuple[re.Pattern, Callable[[str], List[int]], Callable[[str], str], str] = (
    re.compile(r"((\d+-\d+)|\d+)(;+\d+)+((-\d+)|(;+\d+))*"),
    cslice_func,
    icslice_func,
    "CSlice",
)


def transect_func(pos: str) -> List[str]:
    return [pos]


def transect_ifunc(pos: str) -> str:
    t, p = pos.split("-")
    return "{}-{}".format(t, int(p) + 1)


TRANSECT_REGEX: Tuple[re.Pattern, Callable[[str], List[str]], Callable[[str], str], str] = (
    re.compile(r"[tT]+[\d\W]+-+[\d\W]+$"),
    transect_func,
    transect_ifunc,
    "Transect",
)

POSITION_REGEX: Tuple[re.Pattern, None, None, str] = (
    re.compile(r"[pPlLrRdD\d]?[\d]$|[\d]$"),
    None,
    None,
    "Position",
)


def xy_func(p: str) -> List[str]:
    return p.split(";")


XY_REGEX: Tuple[re.Pattern, Callable[[str], List[str]], None, str] = (
    re.compile(
        r"([-\d+]+(\.\d)+(,[-\d+]+(\.\d)+){1,2})(;([-\d+]+(\.\d)+(,[-\d+]+(\.\d+)){1,2}))*$"
    ),
    xy_func,
    None,
    "XY",
)

DRILL_REGEX = re.compile(r"^(?P<id>[dD]\d+)$")
POINT_REGEX = re.compile(r"^(?P<id>[pP]\d+)$")

SCAN_REGEX: Tuple[re.Pattern, None, None, str] = (
    re.compile(r"^(?P<id>[sS]\d+)$"),
    None,
    None,
    "Scan",
)

if __name__ == "__main__":
    for pos in ("-1.0,2.0;", "1.0;", "1.0;2.0", "1.0,2.0;3.0,4.0"):
        for r, f, _, name in (
            SLICE_REGEX,
            SSLICE_REGEX,
            PSLICE_REGEX,
            TRANSECT_REGEX,
            POSITION_REGEX,
            XY_REGEX,
        ):
            if r.match(pos):
                print("matched {} to {}".format(name, pos))
                print(f(pos))
# ============= EOF =============================================
