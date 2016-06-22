# ===============================================================================
# Copyright 2016 Jake Ross
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


# ============= EOF =============================================
from pychron.core.helpers.strtools import to_bool


def trim(func):
    def wrapper(*args, **kw):
        r = func(*args, **kw)
        if r:
            r = r.strip()
        return r

    return wrapper


def trim_bool(func):
    return _itrim_bool(func)


def invert_trim_bool(func):
    return _itrim_bool(func, True)


def _itrim_bool(func, invert=False):
    def wrapper(*args, **kw):
        r = func(*args, **kw)
        if r:
            r = r.strip()
            r = to_bool(r)
            if invert:
                r = not r
        return r

    return wrapper
