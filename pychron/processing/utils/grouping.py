#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================

#============= standard library imports ========================
from itertools import groupby
#============= local library imports  ==========================
# def group_analyses_by_key(editor, items, key):
def group_analyses_by_key(items, key):
    if isinstance(key,str):
        keyfunc=lambda x: getattr(x, key)
    else:
        keyfunc=key
        
    ids = []
    for it in items:
        v = keyfunc(it)
        if not v in ids:
            ids.append(v)

    sitems = sorted(items, key=keyfunc)
    #for i, (_, analyses) in enumerate(groupby(sitems, key=key)):
    for k, analyses in groupby(sitems, key=keyfunc):
        gid = ids.index(k)
        for it in analyses:
            setattr(it, 'group_id', gid)
            # idxs = [items.index(ai) for ai in analyses]
            # editor.set_group(idxs, gid, refresh=False)
            # for
  
#============= EOF =============================================
