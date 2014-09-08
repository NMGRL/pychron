# ===============================================================================
# Copyright 2014 Jake Ross
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
#===============================================================================

#============= enthought library imports =======================

#============= standard library imports ========================
#============= local library imports  ==========================

def frequency_index_gen(runs, freq, incrementable, before, after, sidx=0):
    cnt = 0
    n = len(runs)
    for i, ai in enumerate(runs):
        if ai.analysis_type not in incrementable:
            continue

        if cnt % freq:
            cnt += 1
            continue

        i += sidx
        # print i
        if before and not after:
            yield i
        elif after and not before:
            if i + freq - sidx <= n:
                yield i + freq
        elif not before and not after:
            if i + freq < n:
                yield i + freq
        else:
            yield i
        cnt += 1

    if before and after:
        yield i + freq


#============= EOF =============================================
