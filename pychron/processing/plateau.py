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
from traits.api import HasTraits, List, Array

# ============= standard library imports ========================
from numpy import argmax, array
# ============= local library imports  ==========================
# from pychron.core.helpers.logger_setup import logging_setup, new_logger
# logging_setup('plateau', use_archiver=False)
# log = new_logger('foo')
from pychron.core.stats.core import validate_mswd, calculate_mswd


def memoize(function):
    cache = {}

    def closure(*args):
        # return function(*args)
        if args not in cache:
            cache[args] = function(*args)
        return cache[args]

    return closure


class Log():
    def debug(self, txt):
        pass
        # print 'debug --- {}'.format(txt)

log = Log()


class Plateau(HasTraits):
    ages = Array
    errors = Array
    signals = Array
    exclude = List

    nsteps = 3
    overlap_sigma = 2
    gas_fraction = 50

    use_overlap = True  # fleck criterion
    use_mswd = False  #mahon criterion

    def find_plateaus(self, method=''):
        """
            method: str either fleck 1977 or mahon 1996
        """
        if method.lower() == 'mahon 1996':
            self.use_mswd = True
            self.use_overlap = False
        else:
            self.use_mswd = False
            self.use_overlap = True

        n = len(self.ages)
        exclude = self.exclude
        ss = [s for i, s in enumerate(self.signals)
              if not i in exclude]

        self.total_signal = float(sum(ss))
        # log.info(self.total_signal)

        idxs = []
        spans = []

        overlap_func = memoize(self._overlap)
        for i in range(n):
            if i in exclude:
                continue
            idx = self._find_plateaus(n, i, exclude, overlap_func)
            if idx:
                # log.debug('found {} {}'.format(*idx))
                idxs.append(idx)
                spans.append(idx[1] - idx[0])

        if spans:
            return idxs[argmax(array(spans))]

        return idxs

    def _find_plateaus(self, n, start, exclude, overlap_func):
        potential_end = None
        for i in range(start, n, 1):
            if i in exclude:
                continue

            if not self.check_nsteps(start, i):
                log.debug('{} {} nsteps failed'.format(start, i))
                continue

            if self.use_overlap and not self.check_overlap(start, i, overlap_func):
                log.debug('{} {} overlap failed'.format(start, i))
                # potential_end=None
                break

            if self.use_mswd and not self.check_mswd(start, i):
                continue

            if not self.check_percent_released(start, i):
                log.debug('{} {} percent failed'.format(start, i))
                continue

            potential_end = i

        if potential_end:
            return start, potential_end

    def check_percent_released(self, start, end):
        ss = sum([(s if not i in self.exclude else 0)
                  for i, s in enumerate(self.signals)][start:end + 1])

        log.debug('percent {} {} {}'.format(start, end, ss / self.total_signal))

        return ss / self.total_signal >= self.gas_fraction/100.

    def check_mswd(self, start, end):
        """
            return False if not valid
        """
        ages = self.ages[start, end + 1]
        errors = self.errors[start, end + 1]
        mswd = calculate_mswd(ages, errors)
        return validate_mswd(mswd, len(ages))

    def check_overlap(self, start, end, overlap_func):
        overlap_sigma = self.overlap_sigma
        for c, i in enumerate(range(start, end, 1)):
            for j in range(start + c, end + 1, 1):
                if i == j:
                    continue
                if not overlap_func(i, j, overlap_sigma):
                    return
        else:
            return True

    def _overlap(self, start, end, overlap_sigma):
        # log.debug('checking overlap {} {} '.format(start, end))

        a1 = self.ages[start]
        a2 = self.ages[end]
        e1 = self.errors[start]
        e2 = self.errors[end]

        e1 *= overlap_sigma
        e2 *= overlap_sigma

        # log.debug('{}<{} {}>{}'.format(a1 - e1 , a2 + e2, a1 + e1 , a2 - e2))
        return a1 - e1 < a2 + e2 and a1 + e1 > a2 - e2

    def check_nsteps(self, start, end):
        return (end - start) + 1 >= self.nsteps

# ============= EOF =============================================

