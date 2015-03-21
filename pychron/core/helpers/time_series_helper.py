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



# ============= enthought library imports =======================

# ============= standard library imports ========================
import struct
# ============= local library imports  ==========================
def build_time_series_blob(ts, vs):
    '''
        @type vs: C{str}
        @param vs:
    '''
    if isinstance(ts, float):
        ts = [ts]
        vs = [vs]
    blob = ''
    for ti, vi in zip(ts, vs):
        blob += struct.pack('>ff', float(vi), float(ti))
    return blob

def parse_time_series_blob(blob):
    '''
    '''
    v = []
    t = []
    for i in range(0, len(blob), 8):
        vi, ti = struct.unpack('>ff', blob[i:i + 8])
        v.append(vi)
        t.append(ti)

    return t, v
# ============= EOF ====================================
