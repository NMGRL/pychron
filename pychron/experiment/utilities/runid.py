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
from pychron.core.utils import alphas, alpha_to_int


def make_rid(ln, a, step=""):
    """
    if ln can be converted to integer return runid
    else return ln-a
    """
    try:
        _ = int(ln)
        return make_runid(ln, a, step)
    except ValueError:
        if not isinstance(a, str):
            a = "{:02d}".format(a)
        return "{}-{}".format(ln, a)


def make_runid(ln, a, s=""):
    _as = make_aliquot_step(a, s)
    return "{}-{}".format(ln, _as)


def make_step(s):
    if isinstance(s, (float, int, int)):
        s = alphas(s)
    return s or ""


def make_increment(s):
    return alpha_to_int(s)


def make_aliquot(a):
    if not isinstance(a, str):
        a = "{:02d}".format(int(a))
    return a


def make_aliquot_step(a, s):
    a = make_aliquot(a)
    s = make_step(s)
    return "{}{}".format(a, s)


# ============= EOF =============================================
