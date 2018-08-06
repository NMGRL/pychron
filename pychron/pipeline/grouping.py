# ===============================================================================
# Copyright 2018 ross
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
from itertools import groupby


def group_analyses_by_key(items, key, attr='group_id', id_func=None, sorting_enabled=True):
    if isinstance(key, str):
        keyfunc = lambda x: getattr(x, key)
    else:
        keyfunc = key

    ids = []
    for it in items:
        v = keyfunc(it)
        if v not in ids:
            ids.append(v)

    if sorting_enabled:
        items = sorted(items, key=keyfunc)

    for k, analyses in groupby(items, key=keyfunc):
        gid = ids.index(k)
        if id_func:
            gid = id_func(gid, analyses)
        for it in analyses:
            setattr(it, attr, gid)

# ============= EOF =============================================
