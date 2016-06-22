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
from traits.api import Dict
# ============= standard library imports ========================
from numpy.random import random
import os
# ============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.paths import paths


def write_txt_file(p, out):
    with open(p, 'w') as wfile:
        for line in out:
            wfile.write('{}\n'.format(','.join(map(str, line))))


class AutomatedRunDurationTracker(Loggable):
    _items = Dict
    _frequencies = Dict

    def __init__(self, *args, **kw):
        super(AutomatedRunDurationTracker, self).__init__(*args, **kw)
        self.load()

    def load(self):
        items = {}
        if os.path.isfile(paths.duration_tracker):
            with open(paths.duration_tracker, 'r') as rfile:
                for line in rfile:
                    line = line.strip()
                    if line:
                        args = line.split(',')
                        items[args[0]] = float(args[1])

        self._items = items

        # load frequencies
        freq = {}
        if os.path.isfile(paths.duration_tracker_frequencies):
            with open(paths.duration_tracker_frequencies, 'r') as rfile:
                for line in rfile:
                    if line:
                        h, total, truncated = line.split(',')

                    freq[h] = float(truncated) / float(total)
        self._frequencies = freq

    def update(self, run, t):
        rh = run.spec.script_hash_truncated
        self.debug('update duration runid={}, duration={}, md5={}'.format(run.spec.runid, t, rh[:8]))

        p = paths.duration_tracker

        out = []
        exists = False

        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                for line in rfile:
                    line = line.strip()
                    if line:
                        args = line.split(',')

                        h, ct, ds = args[0], args[1], args[2:]
                        # update the runs duration by taking running average of last 10
                        if h == rh:
                            exists = True

                            ds = map(float, ds)
                            ds.append(t)
                            ds = ds[-10:]
                            if len(ds):
                                args = [h, sum(ds) / len(ds)]
                                args.extend(ds)

                        out.append(args)

        if not exists:
            self.debug('adding {} {} to durations'.format(run.spec.runid, rh[:8]))
            out.append((rh, t))

        write_txt_file(p, out)

        # update frequencies
        rh = run.spec.script_hash
        out = []
        exists = False
        p = paths.duration_tracker_frequencies

        ist = run.spec.is_truncated()
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                for line in rfile:
                    line = line.strip()
                    if line:
                        h, total, truncated = line.split(',')
                        if h == rh:
                            exists = True
                            total = int(total) + 1
                            if ist:
                                truncated = int(truncated) + 1

                        out.append((h, total, truncated))

        if not exists:
            self.debug('adding {} {} to frequencies'.format(run.spec.runid, rh[:8]))
            out.append((rh, 1, 1 if ist else 0))

        write_txt_file(p, out)
        self.load()

    def probability_model(self, h, ht):
        self.debug('using probability model')
        prob = self._frequencies.get(h, 0)

        self.debug('probability: {}'.format(prob))
        # probability run is truncated
        if random() < prob:
            h = ht
            self.debug('use truncated duration')

        dur = self._items[h]
        return dur

    def __contains__(self, v):
        return v in self._items

    def __getitem__(self, k):
        return self._items[k]

# ============= EOF =============================================
