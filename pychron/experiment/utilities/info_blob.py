#===============================================================================
# Copyright 2012 Jake Ross
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
import struct
#============= local library imports  ==========================

class MemoryBlock(object):
    def __init__(self, blob=''):
        self._blob = blob
        self._start = 0

    def get_short(self):
        v = self._get_value('!h', 2)
        return v

    def get_float(self):
        v = self._get_value('!f', 4)
        return v

    def get_double(self):
        v = self._get_value('!d', 8)
        return v

    def _get_value(self, fmt, width):
        txt = self._blob
        start = self._start
        v = struct.unpack(fmt, txt[start:start + width])
        self._start += width
        return v[0]

    def add_short(self, value):
        self._add_value('!h', value)

    def add_float(self, value):
        self._add_value('!f', value)

    def add_double(self, value):
        self._add_value('!d', value)

    def _add_value(self, fmt, value):
        v = struct.pack(fmt, value)
        self._blob += v

    def clear(self):
        self._blob = ''

    def tostring(self):
        return self._blob

def decode_infoblob(blob):
    mb = MemoryBlock(blob)
    rpts = mb.get_short()
    npos = mb.get_short()

    pos_segments = []
    for _ in range(npos):
        pos_segments.append(mb.get_float())

    nsegs = mb.get_short()
    bs_segments = []
    bs_seg_params = []
    bs_seg_errs = []
    for _ in range(nsegs):
        bs_segments.append(mb.get_float())
        pp = []
        for _ in range(4):
            pp.append(mb.get_double())
        bs_seg_params.append(pp)
        bs_seg_errs.append(mb.get_float())

    return rpts, pos_segments, bs_segments, bs_seg_params, bs_seg_errs

def encode_infoblob(rpts, pos_segments, bs_segments, bs_seg_params, bs_seg_errs):
    mb = MemoryBlock()
    mb.add_short(rpts)

    npos = len(pos_segments)
    mb.add_short(npos)
    for pi in pos_segments:
        mb.add_float(pi)

    nseg = len(bs_segments)
    mb.add_short(nseg)
    for i in range(nseg):
        mb.add_float(bs_segments[i])
        for k in range(4):
            mb.add_double(bs_seg_params[i][k])
        mb.add_float(bs_seg_errs[i])
    return mb.tostring()
#============= EOF =============================================
