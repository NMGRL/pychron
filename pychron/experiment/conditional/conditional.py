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

# ============= enthought library imports =======================

from traits.api import Str, Either, Int, Callable, Bool, Float
# ============= standard library imports ========================
import re
from uncertainties import nominal_value, std_dev, ufloat
# ============= local library imports  ==========================
from pychron.experiment.utilities.identifier import AGE_TESTABLE
from pychron.loggable import Loggable

# match .current_point
CP_REGEX = re.compile(r'[\w\d]+\.(current|cur)')
# match .std_dev
STD_REGEX = re.compile(r'[\w\d]+\.(std_dev|sd|stddev)')

#match .inactive
ACTIVE_REGEX = re.compile(r'[\w\d]+\.inactive')

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

BASELINE_REGEX = re.compile(r'[\w\d]+\.bs')
BASELINECOR_REGEX = re.compile(r'[\w\d]+\.bs_corrected')

PARENTHESES_REGEX = re.compile(r'\([\w\d\s]+\)')

COMP_REGEX = re.compile(r'<=|>=|>|<|==')

DEFLECTION_REGEX = re.compile(r'[\w\d]+\.deflection')

RATIO_REGEX = re.compile(r'\d+/\d+')

BETWEEN_REGEX = re.compile(r'(not ){0,1}[\d\w\s]+.between\(([-\d+]+(\.\d)*(,[-\d+]+(\.\d)*))\)')
BETWEEN_REGEX = re.compile(r'(not ){0,1}between\([\w\d\s]+(\.\w+)*\s*,\s*[-\d+]+(\.\d)*(\s*,\s*[-\d+]+(\.\d)*)\)')
ARGS_REGEX = re.compile(r'\(.+\)')


def conditional_from_dict(cd, klass):
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


class BaseConditional(Loggable):
    attr = Str
    comp = Str

    def to_string(self):
        raise NotImplementedError

    def check(self, run, data, cnt):
        """
             check conditional if cnt is greater than start count
             cnt-start count is greater than 0
             and cnt-start count is divisable by frequency

             data: 2-tuple. (keys, signals) where keys==detector names, signals== measured intensities

             return True if check passes. e.i. Write checks to trip on success. to terminate
             if Ar36 intensity is less than x use Ar36<x
        """
        if self._should_check(run, data, cnt):
            return self._check(run, data)

    def _check(self, run, data):
        raise NotImplementedError

    def _should_check(self, run, data, cnt):
        return True

    def __repr__(self):
        return self.to_string()


class AutomatedRunConditional(BaseConditional):
    start_count = Int
    frequency = Int
    message = Str

    # used to specify a window (in counts) of data to average, etc.
    window = Int
    mapper = Str
    analysis_types = None

    _key = ''
    _mapper_key = ''

    active = True
    value = Float

    def __init__(self, attr, comp,
                 start_count=0,
                 frequency=10,
                 *args, **kw):

        self.active = True
        self.attr = attr
        self.comp = comp
        self.start_count = start_count
        self.frequency = frequency
        super(AutomatedRunConditional, self).__init__(*args, **kw)

        # m = re.findall(r'[A-Za-z]+\d*', comp)
        m = PARENTHESES_REGEX.findall(comp)
        if m:
            self._key = m[0][1:-1]
        else:
            m = KEY_REGEX.findall(comp)
            if m:
                k=m[0]
                if k in ('not',):
                    k=m[1]
                self._key = k
            else:
                self._key = self.attr

        if self.mapper:
            m = MAPPER_KEY_REGEX.findall(self.mapper)
            if m:
                self._mapper_key = m[0]

    def to_string(self):
        s = '{} {}'.format(self.comp, self.message)
        return s

    def _should_check(self, run, data, cnt):
        if self.analysis_types:
            if run.analysis_type not in self.analysis_types:
                return

        d = False
        if isinstance(cnt, bool):
            d = True

        a = cnt > self.start_count
        b = (cnt - self.start_count) > 0
        c = (cnt - self.start_count) % self.frequency == 0
        cnt_flag = a and b and c

        return self.active and (cnt_flag or d)

    def get_modified_value(self, arun, key, kattr):
        obj=arun.arar_age
        for reg, ff in ((DEFLECTION_REGEX, lambda k: arun.get_deflection(k, current=True)),
                        (BASELINECOR_REGEX, lambda k: obj.get_baseline_corrected_value(k)),
                        (BASELINE_REGEX, lambda k: obj.get_baseline_value(k)),
                        (CP_REGEX, lambda k: obj.get_current_intensity(k))):
            if reg.match(key):
                return ff(kattr)
        else:
            self.unique_warning('invalid modifier comp="{}"'.format(self.comp))
            return

    def _check(self, arun, data):
        attr = self.attr
        if not self.attr:
            attr = self._key

        obj = arun.arar_age

        def default_wrapper(comp, func, found):
            comp = '{}{}'.format(self._key, remove_attr(comp))
            return func(), comp

        def between_wrapper(comp, func, between):
            v = None
            args = ARGS_REGEX.search(between).group(0)[1:-1].split(',')
            key = args[0]
            if '.' in key:
                self._key = key.split('.')[0].strip()
                v = self.get_modified_value(arun,key, self._key)
            else:
                self._key = key

            # self._key=args[0]
            v1, v2 = args[1:]
            nc = '{}<={}<={}'.format(v1, self._key, v2)

            comp = comp.replace(between, nc)
            if between.startswith('not '):
                comp = 'not {}'.format(comp)

            if v is None:
                v = func()
            # print v, comp
            return v, comp

        def ratio_wrapper(comp, func, ratio):
            v = obj.get_value(ratio)
            key = 'ratio{}'.format(ratio.replace('/', ''))
            comp = '{}{}'.format(key, remove_attr(comp))
            self._key = key
            return v, comp

        cc = self.comp
        invert =False
        if cc.startswith('not '):
            cc = cc[4:]
            invert=True

        for aa in ((CP_REGEX, lambda: obj.get_current_intensity(attr)),
                   (BASELINECOR_REGEX, lambda: obj.get_baseline_corrected_value(attr)),
                   (BASELINE_REGEX, lambda: obj.get_baseline_value(attr)),
                   (ACTIVE_REGEX, lambda: not attr in data[0]),
                   (AVG_REGEX, lambda: obj.get_values(attr, self.window or -1).mean()),
                   (MAX_REGEX, lambda: obj.get_values(attr, self.window or -1).max()),
                   (MIN_REGEX, lambda: obj.get_values(attr, self.window or -1).min()),
                   (SLOPE_REGEX, lambda: obj.get_slope(attr, self.window or -1)),
                   (DEFLECTION_REGEX, lambda: arun.get_deflection(attr, current=True)),
                   (RATIO_REGEX, None, ratio_wrapper),
                   (BETWEEN_REGEX, lambda: obj.get_value(attr), between_wrapper)):

            if len(aa) == 2:
                wrapper = default_wrapper
                reg, func = aa
            else:
                reg, func, wrapper = aa

            found = reg.match(cc)
            if found:
                args = wrapper(cc, func, found.group(0))
                if args:
                    v, comp = args
                    break
        else:
            comp = cc
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
        # else:
        #     between=BETWEEN_REGEX.findall(comp)
        #     if between:
        #         between = between[0]
        #         self._key = between.split('.')[0]
        #         v1,v2=eval(between.split('between')[-1])
        #         nc = '{}<={}<={}'.format(v1, self._key, v2)
        #         comp = comp.replace(between, nc)
        #
        #     if DEFLECTION_REGEX.findall(comp):
        #         v = arun.get_deflection(attr, current=True)
        #         comp = '{}{}'.format(self._key, remove_attr(comp))
        #     else:
        #         ratio = RATIO_REGEX.findall(comp)
        #         if ratio:
        #             ratio = ratio[0]
        #             v = obj.get_value(ratio)
        #             key = 'ratio{}'.format(ratio.replace('/', ''))
        #             comp = '{}{}'.format(key, remove_attr(comp))
        #             self._key = key
        #         else:
        #             try:
        #                 if self.window:
        #                     vs = obj.get_values(attr, self.window)
        #                     if not vs:
        #                         self.warning('Deactivating check. check attr invalid for use with window')
        #                         self.active = False
        #                         return
        #                     v = ufloat(vs.mean(), vs.std())
        #                 else:
        #                     v = obj.get_value(attr)
        #             except Exception, e:
        #                 self.warning('Deactivating check. Check Exception "{}."'.format(e))
        #                 self.active = False

        if self._key == 'age':
            atype = arun.spec.analysis_type
            if not atype in AGE_TESTABLE:
                msg = 'age conditional for {} not allowed'.format(atype)
                self.unique_warning(msg)
                return

        if v is not None:
            vv = std_dev(v) if STD_REGEX.match(comp) else nominal_value(v)
            vv = self._map_value(vv)
            self.value = vv
            if invert:
                comp='not {}'.format(comp)
            self.debug('testing {} (eval={}) key={} attr={} value={} mapped_value={}'.format(self.comp, comp,
                                                                                             self._key, self.attr, v,
                                                                                             vv))

            # print 'comp={},key={},v={}'.format(comp, self._key, vv)
            if eval(comp, {self._key: vv}):
                self.message = 'attr={}, value= {} {} is True'.format(self.attr, vv, self.comp)
                return True

    def _map_value(self, vv):
        if self.mapper and self._mapper_key:
            vv = eval(self.mapper, {self._mapper_key: vv})
        return vv


class TruncationConditional(AutomatedRunConditional):
    abbreviated_count_ratio = 1.0


class TerminationConditional(AutomatedRunConditional):
    nfails = Int


class CancelationConditional(AutomatedRunConditional):
    pass
    # def check(self, run, data, cnt):
    #     result = super(CancelationConditional, self).check(run, data, cnt)
    #     if result:
    #


class ActionConditional(AutomatedRunConditional):
    action = Either(Str, Callable)
    resume = Bool  # resume==True the script continues execution else break out of measure_iteration

    def perform(self, script):
        action = self.action
        if isinstance(action, str):
            script.execute_snippet(action)
        else:
            action()

#============= EOF =============================================
