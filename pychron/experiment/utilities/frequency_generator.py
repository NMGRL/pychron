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
# ===============================================================================

# ============= enthought library imports =======================

# ============= standard library imports ========================
import re
from itertools import groupby

# ============= local library imports  ==========================
FREQ_REG = re.compile(r'(\d,)*\d(,[eE])?$|(s(,\d)+(,[eE])?)$|^s$|(s,[eE])$|^e$')


def validate_frequency_template(v):
    return FREQ_REG.match(v)


def parse_frequency_template(freq):
    start, end, excl, idx = False, False, False, None
    if freq.startswith('s'):
        start = True
        freq = freq[2:]

    if freq.endswith('e'):
        end = True
        freq = freq[:-2]
    elif freq.endswith('E'):
        end = True
        freq = freq[:-2]
        excl = True

    if freq:
        idx = eval(freq)
        if isinstance(idx, int):
            idx = [idx]
        else:
            idx = list(idx)

    return start, end, excl, idx


def compress_runs(runs, incrementable):
    """
        return a 2-tuple list (idx, run) filter out not incrementables

    """
    return [(i, r) for i, r in enumerate(runs)
            if r.analysis_type in incrementable]


def render_template(freq, runs, sidx):
    start, end, excl, idxs = parse_frequency_template(freq)
    s = sidx
    for j, (g, rs) in enumerate(groupby(runs, key=lambda x: x[1].aliquot)):
        if start:
            if excl:
                rs=list(rs)
                force = rs[0][0] != s
                if not j or force:
                    if force:
                        s = rs[0][0]
                    yield s
            else:
                yield s

        if idxs:
            a = 0

            t = idxs[:]
            sc=0
            for i, (k, ai) in enumerate(rs):
                if ai.skip:
                    sc+=1

                if i + 1 in idxs:
                    k -= i
                    a += k
                    t.remove(i + 1)
                    yield s + i + 1 + sc

            s += i + 1 + a
            if t:
                end = True

        else:
            rr = list(rs)
            s = rr[-1][0] + 1

        if end:
            yield s


def render_simple(freq, runs, sidx, before, after):
    cnt = 0
    n = len(runs)
    for i, ai in runs:
        if cnt % freq:
            cnt += 1
            continue

        i += sidx
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


def frequency_index_gen(runs, freq, incrementable, before, after, sidx=0):
    runs = compress_runs(runs, incrementable)
    if isinstance(freq, (str,unicode)):
        return render_template(freq, runs, sidx)
    else:
        return render_simple(freq, runs, sidx, before, after)

        #

# ============= EOF =============================================
