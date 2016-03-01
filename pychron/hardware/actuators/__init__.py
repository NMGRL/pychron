# ===============================================================================
# Copyright 2011 Jake Ross
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
from pychron.core.helpers.strtools import to_bool


def get_valve_name(obj):
    if isinstance(obj, (str, int)):
        addr = obj
    else:
        addr = obj.name.split('-')[1]
    return addr


def trim(func):
    def wrapper(*args, **kw):
        r = func(*args, **kw)
        if r:
            r = r.strip()
            # r = r[4:-4]
        return r

    return wrapper


def trim_bool(func):
    def wrapper(*args, **kw):
        r = func(*args, **kw)
        if r:
            r = r.strip()
            r = to_bool(r)
            # r = to_bool(r[4:-4])
        return r

    return wrapper


def invert_trim_bool(func):
    def wrapper(*args, **kw):
        r = func(*args, **kw)
        if r:
            r = r.strip()
            r = to_bool(r)
            # r = to_bool(r[4:-4])
        return not r

    return wrapper