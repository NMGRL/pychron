# ===============================================================================
# Copyright 2020 ross
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
from __future__ import annotations

from typing import Union

from pychron.core.utils import alphas, alpha_to_int


def make_rid(ln: str, a: Union[str, int], step: str = "") -> str:
    try:
        _ = int(ln)
        return make_runid(ln, a, step)
    except ValueError:
        if not isinstance(a, str):
            a = "{:02d}".format(a)
        return "{}-{}".format(ln, a)


def make_runid(ln: str, a: Union[str, int], s: str = "") -> str:
    _as = make_aliquot_step(a, s)
    return "{}-{}".format(ln, _as)


def make_step(s: Union[str, int, float]) -> str:
    if isinstance(s, (float, int)):
        s = alphas(s)
    return str(s) if s else ""


def make_increment(s: str) -> int:
    return alpha_to_int(s)


def make_aliquot(a: Union[str, int]) -> str:
    if not isinstance(a, str):
        a = "{:02d}".format(int(a))
    return a


def make_aliquot_step(a: Union[str, int], s: Union[str, int, float]) -> str:
    a = make_aliquot(a)
    s = make_step(s)
    return "{}{}".format(a, s)


# ============= EOF =============================================
