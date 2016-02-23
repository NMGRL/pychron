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
import os

from traits.api import Str, Either, Int, Callable, Bool, Float, Enum

# ============= standard library imports ========================
from traits.trait_types import BaseStr
from uncertainties import nominal_value, std_dev
import pprint
# ============= local library imports  ==========================
import yaml
from pychron.experiment.conditional.regexes import MAPPER_KEY_REGEX, \
    STD_REGEX, INTERPOLATE_REGEX, EXTRACTION_STR_ABS_REGEX, EXTRACTION_STR_PERCENT_REGEX
from pychron.experiment.conditional.utilities import tokenize, get_teststr_attr_func, extract_attr
from pychron.experiment.utilities.conditionals import RUN, QUEUE, SYSTEM
from pychron.loggable import Loggable
from pychron.paths import paths


def dictgetter(d, attrs, default=None):
    if not isinstance(attrs, tuple):
        attrs = (attrs,)

    for ai in attrs:
        try:
            return d[ai]
        except KeyError:
            pass
    else:
        return default


def conditionals_from_file(p, name=None, level=SYSTEM, **kw):
    with open(p, 'r') as rfile:
        yd = yaml.load(rfile)
        cs = (('TruncationConditional', 'truncation', 'truncations'),
              ('ActionConditional', 'action', 'actions'),
              ('ActionConditional', 'action', 'post_run_actions'),
              ('TerminationConditional', 'termination', 'terminations'),
              ('TerminationConditional', 'pre_run_termination', 'pre_run_terminations'),
              ('TerminationConditional', 'post_run_termination', 'post_run_terminations'),
              ('CancelationConditional', 'cancelation', 'cancelations'))

        conddict = {}
        for klass, _, tag in cs:
            if name and tag != name:
                continue

            yl = yd.get(tag)
            if not yl:
                continue

            # print 'yyyy', yl
            # var = getattr(self, '{}_conditionals'.format(var))
            conds = [conditional_from_dict(ti, klass, level=level, location=p, **kw) for ti in yl]
            # print 'ffff', conds
            conds = [c for c in conds if c is not None]
            if conds:
                conddict[tag] = conds

                # var.extend(conds)

        if name:
            try:
                conddict = conddict[name]
            except KeyError:
                conddict = None

        return conddict


def conditional_from_dict(cd, klass, level=None, location=None, **kw):
    if isinstance(klass, str):
        klass = globals()[klass]

    # try:
    # teststr = cd['teststr']
    # except KeyError:
    # #for pre 2.0.5 conditionals files
    # teststr = cd.get('check')
    # if not teststr:
    # return

    # attr = cd.get('attr')
    # if not attr:
    # return
    teststr = dictgetter(cd, ('teststr', 'comp', 'check'))
    if not teststr:
        return

    # start = dictgetter(cd, ('start', 'start_count'), default=50)
    # freq = cd.get('frequency', 1)
    # win = cd.get('window', 0)
    # mapper = cd.get('mapper', '')
    #
    # ntrips = cd.get('ntrips', 1)
    #
    # analysis_types = cd.get('analysis_types')
    # if analysis_types:
    #     analysis_types = [a.lower() for a in analysis_types]
    # attr = extract_attr(teststr)
    # cx = klass(teststr, start_count=start, frequency=freq,
    #            attr=attr,
    #            window=win, mapper=mapper, action=action,
    #            ntrips=ntrips, analysis_types=analysis_types,
    #            **kw)
    cx = klass(teststr)
    cx.from_dict(teststr, cd, kw)

    if level:
        cx.level = level
    if location:
        location = os.path.relpath(location, paths.root_dir)
        cx.location = location

    return cx


class BaseConditional(Loggable):
    attr = Str
    teststr = Str
    start_count = Int
    level = Enum(None, SYSTEM, QUEUE, RUN)
    tripped = Bool
    location = Str

    def from_dict(self, teststr, cd, kw):
        start = dictgetter(cd, ('start', 'start_count'), default=50)
        freq = cd.get('frequency', 1)
        win = cd.get('window', 0)
        mapper = cd.get('mapper', '')

        ntrips = cd.get('ntrips', 1)

        analysis_types = cd.get('analysis_types')
        if analysis_types:
            analysis_types = [a.lower() for a in analysis_types]
        attr = extract_attr(teststr)

        self.trait_set(start_count=start, frequency=freq,
                       attr=attr,
                       window=win, mapper=mapper,
                       ntrips=ntrips, analysis_types=analysis_types,
                       **kw)
        self._from_dict_hook(cd)

    def _from_dict_hook(self, cd):
        pass

    def to_string(self):
        raise NotImplementedError

    def check(self, run, data, cnt):
        """
        check conditional if cnt is greater than start count
        cnt-start count is greater than 0
        and cnt-start count is divisable by frequency

        returns True if check passes. e.i. Write checks to trip on success. To terminate if Ar36 intensity is less than
        x use Ar36<x

        :param run: ``AutomatedRun``
        :param data: 2-tuple. (keys, signals) where keys==detector names, signals== measured intensities
        :param cnt: int
        :return: True if check passes. e.i. Write checks to trip on success.

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
    frequency = Int
    message = Str

    # used to specify a window (in counts) of data to average, etc.
    window = Int
    mapper = Str
    analysis_types = None

    _mapper_key = ''

    active = True
    value = Float
    ntrips = Int(1)
    trips = 0

    _teststr = None
    _ctx = None

    # def __init__(self, attr, teststr,
    # start_count=0,
    # frequency=1,
    # *args, **kw):

    def __init__(self, teststr,
                 start_count=0,
                 frequency=1,
                 *args, **kw):

        self.active = True
        # self.attr = attr
        self.teststr = teststr
        self.start_count = start_count
        self.frequency = frequency
        super(AutomatedRunConditional, self).__init__(*args, **kw)

    def to_string(self):
        s = '{} {}'.format(self.teststr, self.message)
        return s

    def to_dict(self):
        d = self._attr_dict()
        d['hash_id'] = self._hash_id(d)
        return d

    def _hash_id(self, d=None):
        if d is None:
            d = self._attr_dict()
        return hash(frozenset(d.items()))

    def _attr_dict(self):
        return {'teststr': self.teststr, 'start_count': self.start_count,
                'frequency': self.frequency, 'ntrips': self.ntrips,
                'level': self.level,
                'analysis_types': self.analysis_types, 'location': self.location}

    def result_dict(self):
        hash_id = self._hash_id()
        return {'teststr': self._teststr, 'context': self._ctx, 'hash_id': hash_id}

    def _should_check(self, run, data, cnt):
        if self.analysis_types:
            if run.analysis_type.lower() not in self.analysis_types:
                return

        if self.active:
            if isinstance(cnt, bool):
                return cnt
            else:

                ocnt = cnt - self.start_count

                # "a" flag not necessary cnt>scnt == cnt-scnt>0
                # a = cnt > self.start_count
                b = ocnt > 0
                c = ocnt % self.frequency == 0
                cnt_flag = b and c
                # print ocnt, self.frequency, b, c
                return cnt_flag

    def _check(self, run, data):
        """
        make a teststr and context from the run and data
        evaluate the teststr with the context

        """
        teststr, ctx = self._make_context(run, data)
        self._teststr, self._ctx = teststr, ctx

        self.value_context = vc = pprint.pformat(ctx, width=1)

        self.debug('testing {}'.format(teststr))
        msg = 'evaluate ot="{}" t="{}", ctx="{}"'.format(self.teststr, teststr, vc)
        self.debug(msg)
        if eval(teststr, ctx):
            self.trips += 1
            self.debug('condition {} is true trips={}/{}'.format(teststr, self.trips,
                                                                 self.ntrips))
            if self.trips >= self.ntrips:
                self.tripped = True
                self.message = 'condition {} is True'.format(teststr)
                self.trips = 0
                return True
        else:
            self.trips = 0

    def _make_context(self, obj, data):
        teststr = self.teststr

        ctx = {}
        tt = []
        for ti, oper in tokenize(teststr):
            ts, attr, func = get_teststr_attr_func(ti)
            v = func(obj, data, self.window)

            vv = std_dev(v) if STD_REGEX.match(teststr) else nominal_value(v)
            vv = self._map_value(vv)
            ctx[attr] = vv

            ts = self._interpolate_teststr(ts, obj, data)
            tt.append(ts)
            if oper:
                tt.append(oper)

        return ' '.join(tt), ctx

    def _map_value(self, vv):
        if self.mapper:
            m = MAPPER_KEY_REGEX.search(self.mapper)
            if m:
                key = m.group(0)
                vv = eval(self.mapper, {key: vv})
        return vv

    def _interpolate_teststr(self, ts, obj, data):
        nts = ts
        for temp in INTERPOLATE_REGEX.finditer(ts):
            temp = temp.group(0)
            new = obj.get_interpolated_value(temp)
            nts = nts.replace(temp, str(new))
        return nts


class TruncationConditional(AutomatedRunConditional):
    """
    stops the current measurement and continues to next step in pyscript.
    If more measure calls are main use abbreviated_count_ratio to reduce
    the number of counts. for example of abbreviated_count_ratio = 0.5 and
    the original baseline counts = 100, only 50 counts will be made for a truncated
    run.

    """
    abbreviated_count_ratio = 1.0


class TerminationConditional(AutomatedRunConditional):
    """
    Stop the current analysis immediately. Don't save to database.
    Continue to next run in experiment queue
    """


class CancelationConditional(AutomatedRunConditional):
    """
    Stop the current analysis immediately then stop the experiment.
    """


class ActionConditional(AutomatedRunConditional):
    """
    Executes a specified action. The action string is executed as pyscript snippet. actions
    therefore may be any valid measuremnt pyscript code. for example::

        # call a gosub
        gosub("someGoSub")

        # open a valve
        open("V")

    """
    action = Either(Str, Callable)
    resume = Bool  # resume==True the script continues execution else break out of measure_iteration

    def _from_dict_hook(self, cd):
        for tag in ('action', 'resume'):
            if tag in cd:
                setattr(self, tag, cd[tag])

    def perform(self, script):
        """
        perform the specified action.

        use ``MeasurementPyScript.execute_snippet`` to perform desired action

        :param script: MeasurementPyScript
        """
        action = self.action
        if isinstance(action, str):
            try:
                script.execute_snippet(action)
            except BaseException:
                self.warning('Invalid action: "{}"'.format(action))

        elif hasattr(action, '__call__'):
            action()


MODIFICATION_ACTIONS = ('Skip Next Run', 'Skip N Runs', 'Skip Aliquot', 'Skip to Last in Aliquot', 'Set Extract')


class ExtractionStr(BaseStr):
    def validate(self, obj, name, value):
        if value == '':
            return value

        for r in (EXTRACTION_STR_ABS_REGEX, EXTRACTION_STR_PERCENT_REGEX):
            if r.match(value):
                return value
        else:
            self.error(obj, name, value)


def get_extraction_steps(s):
    use_percent = bool(EXTRACTION_STR_PERCENT_REGEX.match(s))

    def gen():
        for si in s.split(','):
            si = si.strip()
            if si.endswith('%'):
                si = si[:-1]
            yield float(si)
        raise StopIteration

    return gen, use_percent


class QueueModificationConditional(AutomatedRunConditional):
    use_truncation = Bool
    use_termination = Bool
    nskip = Int
    action = Enum(MODIFICATION_ACTIONS)
    extraction_str = ExtractionStr

    def do_modifications(self, queue, current_run):
        runs = queue.cleaned_automated_runs
        func = getattr(self, self.action.lower().replace(' ', '_'))
        func(runs, current_run)
        queue.refresh_table_needed = True

    def _from_dict_hook(self, cd):
        for tag in ('action', 'nskip', 'use_truncation', 'use_termination'):
            if tag in cd:
                setattr(self, tag, cd[tag])

    def _skip_n_runs(self, runs, current_run, n=None):
        if n is None:
            n = self.nskip

        for i in xrange(n):
            r = runs[i]
            r.skip = True

    def _skip_next_run(self, runs, current_run):
        self._skip_n_runs(runs, current_run, 1)

    def _skip_aliquot(self, runs, current_run):

        identifier = current_run.spec.identifier
        aliquot = current_run.spec.aliquot
        for r in runs:
            if r.is_special():
                continue

            if r.identifier == identifier and r.aliquot == aliquot:
                r.skip = True

    def _skip_to_last_in_aliquot(self, runs, current_run):
        identifier = current_run.spec.identifier
        for i, r in enumerate(runs):
            if r.is_special():
                continue

            try:
                nrun = runs[i + 1]
                if nrun.identifier != identifier:
                    break
                else:
                    r.skip = True

            except IndexError:
                pass

    def _set_extract(self, runs, current_run):

        es = self.extraction_str

        identifier = current_run.spec.identifier
        aliquot = current_run.spec.aliquot

        steps_gen, use_percent = get_extraction_steps(es)
        for r in runs:
            if r.is_special():
                continue

            if r.identifier != identifier or r.aliquot != aliquot:
                break

            try:
                nstep = steps_gen.next()
                if use_percent:
                    r.extract_value *= (1 + nstep / 100.)
                else:
                    r.extract_value += nstep
            except StopIteration:
                break

# ============= EOF =============================================
# attr = extract_attr(token)
# tkey = attr
# def default_wrapper(teststr, found):
# teststr = '{}{}'.format(tkey, remove_attr(teststr))
# return teststr, tkey
#
# def between_wrapper(teststr, func, between):
# v = None
# args = ARGS_REGEX.search(between).group(0)[1:-1].split(',')
# key = args[0]
# if '.' in key:
# key = key.split('.')[0].strip()
# v = 0
# # v = self.get_modified_value(arun, key, key)
#
# v1, v2 = args[1:]
# nc = '{}<={}<={}'.format(v1, key, v2)
#
# teststr = teststr.replace(between, nc)
#     if between.startswith('not '):
#         teststr = 'not {}'.format(teststr)
#
#     if v is None:
#         v = func()
#     return v, teststr, key
#
# def ratio_wrapper(teststr, func, ratio):
#     v = obj.get_value(ratio)
#     key = 'ratio{}'.format(ratio.replace('/', ''))
#     teststr = '{}{}'.format(key, remove_attr(teststr))
#     return v, teststr, key
# for aa in ((CP_REGEX, lambda obj, data, window: obj.arar_age.get_current_intensity(attr)),
#            (BASELINECOR_REGEX, lambda obj, data, window: obj.garar_age.et_baseline_corrected_value(attr)),
#            (BASELINE_REGEX, lambda obj, data, window: obj.arar_age.get_baseline_value(attr)),
#            (ACTIVE_REGEX, lambda obj, data, window: not attr in data[0]),
#            (AVG_REGEX, lambda obj, data, window: obj.arar_age.get_values(attr, window or -1).mean()),
#            (MAX_REGEX, lambda obj, data, window: obj.arar_age.get_values(attr, window or -1).max()),
#            (MIN_REGEX, lambda obj, data, window: obj.arar_age.get_values(attr, window or -1).min()),
#            (SLOPE_REGEX, lambda obj, data, window: obj.arar_age.get_slope(attr, window or -1)),
#            (DEFLECTION_REGEX, lambda obj, data, window: obj.get_deflection(attr, current=True)),
#            (RATIO_REGEX, None, ratio_wrapper),
#            (BETWEEN_REGEX, lambda obj, data, window: obj.arar_age.get_value(attr), between_wrapper)):
#
#     if len(aa) == 2:
#         wrapper = default_wrapper
#         reg, func = aa
#     else:
#         reg, func, wrapper = aa
#
#     found = reg.match(attr)
#     if found:
#         args = wrapper(attr, found.group(0))
#         if args:
#             teststr, tkey = args
#             # teststr, tkey = args
#             break
# else:
#     teststr='asdf'
# def _get_simple_key(self, teststr):
# m = PARENTHESES_REGEX.findall(teststr)
# if m:
# key = m[0][1:-1]
# else:
#         m = KEY_REGEX.findall(teststr)
#         if m:
#             k = m[0]
#             if k in ('not',):
#                 k = m[1]
#             key = k
#         else:
#             key = self.attr
#     return key

# def _check(self, arun, data):
#     obj = arun.arar_age
#     # attr = self.attr
#
#     cc = self.teststr
#     invert = False
#     if cc.startswith('not '):
#         cc = cc[4:]
#         invert = True
#
#     tkey = self._get_simple_key(cc)
#
#     def default_wrapper(teststr, func, found):
#         teststr = '{}{}'.format(tkey, remove_attr(teststr))
#         return func(), teststr, tkey
#
#     def between_wrapper(teststr, func, between):
#         v = None
#         args = ARGS_REGEX.search(between).group(0)[1:-1].split(',')
#         key = args[0]
#         if '.' in key:
#             key = key.split('.')[0].strip()
#             v = self.get_modified_value(arun, key, key)
#
#         v1, v2 = args[1:]
#         nc = '{}<={}<={}'.format(v1, key, v2)
#
#         teststr = teststr.replace(between, nc)
#         if between.startswith('not '):
#             teststr = 'not {}'.format(teststr)
#
#         if v is None:
#             v = func()
#         return v, teststr, key
#
#     def ratio_wrapper(teststr, func, ratio):
#         v = obj.get_value(ratio)
#         key = 'ratio{}'.format(ratio.replace('/', ''))
#         teststr = '{}{}'.format(key, remove_attr(teststr))
#         return v, teststr, key
#
#     for aa in ((CP_REGEX, lambda: obj.get_current_intensity(attr)),
#                (BASELINECOR_REGEX, lambda: obj.get_baseline_corrected_value(attr)),
#                (BASELINE_REGEX, lambda: obj.get_baseline_value(attr)),
#                (ACTIVE_REGEX, lambda: not attr in data[0]),
#                (AVG_REGEX, lambda: obj.get_values(attr, self.window or -1).mean()),
#                (MAX_REGEX, lambda: obj.get_values(attr, self.window or -1).max()),
#                (MIN_REGEX, lambda: obj.get_values(attr, self.window or -1).min()),
#                (SLOPE_REGEX, lambda: obj.get_slope(attr, self.window or -1)),
#                (DEFLECTION_REGEX, lambda: arun.get_deflection(attr, current=True)),
#                (RATIO_REGEX, None, ratio_wrapper),
#                (BETWEEN_REGEX, lambda: obj.get_value(attr), between_wrapper)):
#
#         if len(aa) == 2:
#             wrapper = default_wrapper
#             reg, func = aa
#         else:
#             reg, func, wrapper = aa
#
#         found = reg.match(cc)
#         if found:
#             args = wrapper(cc, func, found.group(0))
#             if args:
#                 v, teststr, tkey = args
#                 break
#     else:
#         teststr = cc
#         try:
#             if self.window:
#                 vs = obj.get_values(attr, self.window)
#                 if not vs:
#                     self.warning('Deactivating check. check attr invalid for use with window')
#                     self.active = False
#                     return
#                 v = ufloat(vs.mean(), vs.std())
#             else:
#                 v = obj.get_value(attr)
#         except Exception, e:
#             self.warning('Deactivating check. Check Exception "{}."'.format(e))
#             self.active = False
#
#     if tkey == 'age':
#         atype = arun.spec.analysis_type
#         if not atype in AGE_TESTABLE:
#             msg = 'age conditional for {} not allowed'.format(atype)
#             self.unique_warning(msg)
#             return
#
#     if v is not None:
#         vv = std_dev(v) if STD_REGEX.match(teststr) else nominal_value(v)
#         vv = self._map_value(vv)
#         self.value = vv
#         if invert:
#             teststr = 'not {}'.format(teststr)
#
#         self.debug('testing {} (eval={}) key={} attr={} value={} mapped_value={}'.format(self.teststr, teststr,
#                                                                                          tkey, self.attr, v,
#                                                                                          vv))
#         if eval(teststr, {tkey: vv}):
#             self.debug('condition {} is true'.format(teststr))
#             self.message = 'attr={}, value= {} {} is True'.format(self.attr, vv, self.teststr)
#             return True
