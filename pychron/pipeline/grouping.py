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
from operator import attrgetter


def group_analyses_by_key(
    items,
    key,
    attr="group_id",
    id_func=None,
    sorting_enabled=True,
    parent_group=None,
    as_int=True,
):
    if isinstance(key, str):
        keyfunc = attrgetter(key)
    else:
        keyfunc = key

    ids = []
    for it in items:
        v = keyfunc(it)
        if v not in ids:
            ids.append(v)

    if sorting_enabled:
        items = sorted(items, key=keyfunc)

    if parent_group is None:
        parent_group = "group_id"

    for _, gitems in groupby(items, attrgetter(parent_group)):
        gitems = list(gitems)

        for k, analyses in groupby(sorted(gitems, key=keyfunc), key=keyfunc):
            analyses = list(analyses)
            gid = ids.index(k) if as_int else k
            if id_func:
                id_func(gid, analyses)
            else:
                for it in analyses:
                    setattr(it, attr, gid)
                    setattr(it, attr.replace("_id", "_name"), k)
    return items


# ============= EOF =============================================
