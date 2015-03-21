# ===============================================================================
# Copyright 2014 Jake Ross
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

# ============= standard library imports ========================
# ============= local library imports  ==========================


def generate_hops(hops):
    # for c in xrange(self.ncycles):
    c = 0
    while 1:
        for hopstr, counts, settle in hops:
            is_baselines, isos, dets, defls = zip(*split_hopstr(hopstr))
            if any(is_baselines):
                yield c, is_baselines, dets, isos, defls, settle, counts
            else:
                for i in xrange(int(counts)):
                    yield c, is_baselines, dets, isos, defls, settle, i
        c += 1


def parse_hops(hops, ret=None):
    """
        hops list of hop tuples
        ret: comma-delimited str. valid values are ``iso``, ``det``, ``defl``
             eg. "iso,det"
    """
    for hopstr, cnt, s in hops:
        for is_baseline, iso, det, defl in split_hopstr(hopstr):
            if ret:
                loc = locals()
                r = [loc[ri.strip()] for ri in ret.split(',')]
                yield r
            else:
                yield is_baseline, iso, det, defl, cnt, s


def split_hopstr(hop):
    for hi in hop.split(','):
        args = map(str.strip, hi.split(':'))
        defl = None
        is_baseline = False
        if len(args) == 4:
            #this is a baseline
            _, iso, det, defl = args
            is_baseline = True
        elif len(args) == 3:
            iso, det, defl = args
            if iso == 'bs':
                is_baseline = True
                iso = det
                det = defl
                defl = None
        else:
            iso, det = args

        yield is_baseline, iso, det, defl

# ============= EOF =============================================
