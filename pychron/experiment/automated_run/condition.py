# ===============================================================================
# Copyright 2012 Jake Ross
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

#============= enthought library imports =======================

from traits.api import Str, Either, Int, Callable, Bool, Float
#============= standard library imports ========================
import re
from uncertainties import nominal_value, std_dev, ufloat
#============= local library imports  ==========================
from pychron.loggable import Loggable

#match .current_point
CP_REGEX = re.compile(r'\.(current|cur)')
#match .std_dev
STD_REGEX = re.compile(r'\.(std_dev|sd|stddev)')

#match .active
ACTIVE_REGEX = re.compile(r'\.inactive')

#match average(ar##)
AVG_REGEX = re.compile(r'average\([A-Za-z]+\d*\)')
#match max(ar##)
MAX_REGEX = re.compile(r'max\([A-Za-z]+\d*\)')
#match min(ar##)
MIN_REGEX = re.compile(r'min\([A-Za-z]+\d*\)')

#match slope(ar##)
SLOPE_REGEX = re.compile(r'slope\([A-Za-z]+\d*\)')

#match x in x**2+3x+1
MAPPER_KEY_REGEX = re.compile(r'[A-Za-z]+')

#match kca, ar40, etc..
KEY_REGEX = re.compile(r'[A-Za-z]+\d*')

BASELINE_REGEX = re.compile(r'\.bs')
BASELINECOR_REGEX = re.compile(r'\.bs_corrected')

PARENTHESES_REGEX = re.compile(r'\([\w\d\s]+\)')

COMP_REGEX = re.compile(r'<=|>=|>|<|==')


def condition_from_dict(cd, klass):
    if isinstance(klass, str):
        klass = globals()[klass]

    comp = cd.get('check', None)
    if not comp:
        return

    attr = cd.get('attr', '')
    start = cd.get('start', 30)
    freq = cd.get('frequency', 5)
    win = cd.get('window', 0)
    mapper = cd.get('mapper', '')
    cx = klass(attr, comp, start_count=start, frequency=freq, window=win, mapper=mapper)
    return cx


def remove_attr(s):
    """
        return >10 where s=Ar40>10
    """
    try:
        c = COMP_REGEX.findall(s)[0]
        return '{}{}'.format(c, s.split(c)[-1])
    except IndexError:
        return ''


class AutomatedRunCondition(Loggable):
    attr = Str
    comp = Str

    start_count = Int
    frequency = Int
    message = Str

    # used to specify a window (in counts) of data to average, etc.
    window = Int
    mapper = Str

    _key = ''
    _mapper_key = ''

    value = Float
    active = True

    def __init__(self, attr, comp,
                 start_count=0,
                 frequency=10,
                 *args, **kw):

        self.active = True
        self.attr = attr
        self.comp = comp
        self.start_count = start_count
        self.frequency = frequency
        super(AutomatedRunCondition, self).__init__(*args, **kw)

        # m = re.findall(r'[A-Za-z]+\d*', comp)
        m = PARENTHESES_REGEX.findall(comp)
        if m:
            self._key = m[0][1:-1]
        else:
            m = KEY_REGEX.findall(comp)
            if m:
                self._key = m[0]
            else:
                self._key = self.attr

        if self.mapper:
            m = MAPPER_KEY_REGEX.findall(self.mapper)
            if m:
                self._mapper_key = m[0]

    def to_string(self):
        s = '{} {}'.format(self.comp, self.message)
        return s

    def check(self, obj, data, cnt):
        """
             check condition if cnt is greater than start count
             cnt-start count is greater than 0
             and cnt-start count is divisable by frequency

             data: 2-tuple. (keys, signals) where keys==detector names, signals== measured intensities
        """
        d = False
        if isinstance(cnt, bool):
            d = True

        a = cnt > self.start_count
        b = (cnt - self.start_count) > 0
        c = (cnt - self.start_count) % self.frequency == 0
        cnt_flag = a and b and c

        if self.active and (cnt_flag or d):
            return self._check(obj, data)

    def _check(self, obj, data):
        attr = self.attr
        if not self.attr:
            attr = self._key

        comp = self.comp
        for reg, func in ((CP_REGEX, lambda: obj.get_current_intensity(attr)),
                          (BASELINECOR_REGEX, lambda: obj.get_baseline_corrected_value(attr)),
                          (BASELINE_REGEX, lambda: obj.get_baseline_value(attr)),
                          (ACTIVE_REGEX, lambda: not attr in data[0]),
                          (AVG_REGEX, lambda: obj.get_values(attr, self.window or -1).mean()),
                          (MAX_REGEX, lambda: obj.get_values(attr, self.window or -1).max()),
                          (MIN_REGEX, lambda: obj.get_values(attr, self.window or -1).min()),
                          (SLOPE_REGEX, lambda: obj.get_slope(attr, self.window or -1))):
            if reg.findall(comp):
                v = func()
                comp = '{}{}'.format(self._key, remove_attr(comp))
                break
        else:
            try:
                if self.window:
                    vs = obj.get_values(attr, self.window)
                    if not vs:
                        self.warning('Deactivating check. check attr invalid for use with window')
                        self.active = False
                        return
                    v = ufloat(vs.mean(), vs.std())
                else:
                    v = obj.get_value(attr)
            except Exception, e:
                self.warning('Deactivating check. Check Exception "{}."'.format(e))
                self.active = False

        self.debug('testing {} (eval={}) key={} attr={} value={}'.format(self.comp, comp, self._key, self.attr, v))
        vv = std_dev(v) if STD_REGEX.match(comp) else nominal_value(v)
        vv = self._map_value(vv)
        self.value = vv

        self.debug('testing {} (eval={}) key={} attr={} value={} mapped_value={}'.format(self.comp, comp,
                                                                                         self._key, self.attr, v, vv))
        if eval(comp, {self._key: vv}):
            self.message = 'attr={}, value= {} {} is True'.format(self.attr, vv, self.comp)
            return True

    def _map_value(self, vv):
        if self.mapper and self._mapper_key:
            vv = eval(self.mapper, {self._mapper_key: vv})
        return vv


class TruncationCondition(AutomatedRunCondition):
    abbreviated_count_ratio = 1.0


class TerminationCondition(AutomatedRunCondition):
    pass


class ActionCondition(AutomatedRunCondition):
    action = Either(Str, Callable)
    resume = Bool  # resume==True the script continues execution else break out of measure_iteration

    def perform(self, script):
        action = self.action
        if isinstance(action, str):
            script.execute_snippet(action)
        else:
            action()

#============= EOF =============================================
