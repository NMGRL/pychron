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
# ============= local library imports  ==========================
from uncertainties import ufloat

from pychron.experiment.conditional.regexes import COMP_REGEX, ARGS_REGEX, DEFLECTION_REGEX, BASELINECOR_REGEX, \
    BASELINE_REGEX, MIN_REGEX, MAX_REGEX, CP_REGEX, PARENTHESES_REGEX, KEY_REGEX, ACTIVE_REGEX, SLOPE_REGEX, AVG_REGEX, \
    RATIO_REGEX, BETWEEN_REGEX


def get_teststr_attr_func(token):
    for args in (
                (DEFLECTION_REGEX, 'obj.get_deflection(attr, current=True)'),
                (ACTIVE_REGEX, 'not attr in data[0]'),
                (CP_REGEX, 'aa.get_current_intensity(attr)'),
                (BASELINECOR_REGEX, 'aa.get_baseline_corrected_value(attr)'),
                (BASELINE_REGEX, 'aa.get_baseline_value(attr)'),
                (SLOPE_REGEX, 'aa.get_slope(attr, window or -1)'),
                (AVG_REGEX, 'aa.get_values(attr, window or -1).mean()'),
                (MAX_REGEX, 'aa.get_values(attr, window or -1).max()'),
                (MIN_REGEX, 'aa.get_values(attr, window or -1).min()'),
                (RATIO_REGEX, 'aa.get_value(attr)', wrapper, ratio_teststr),
                (BETWEEN_REGEX, 'aa.get_value(attr)', between_wrapper, between_teststr)):

        wfunc = wrapper
        if len(args) == 2:
            reg, fstr = args
            tfunc = teststr_func
        else:
            reg, fstr, wfunc, tfunc = args

        found = reg.match(token)
        # print token, fstr, found
        if found:
            attr, key, teststr = tfunc(token)
            func = wfunc(fstr, token, key)
            break
    else:
        teststr = token
        attr = extract_attr(teststr)

        def func(obj, data, window):
            if window:
                vs = obj.arar_age.get_values(attr, window)
                v = ufloat(vs.mean(), vs.std())
            else:
                v = obj.arar_age.get_value(attr)
            return v

    if token.startswith('not'):
        if not teststr.startswith('not'):
            teststr = 'not {}'.format(teststr)

    return teststr, attr, func

#wrappers
def wrapper(fstr, token, ai):
    return lambda obj, data, window: eval(fstr, {'attr': ai,
                                                 'aa': obj.arar_age,
                                                 'obj': obj,
                                                 'data': data, 'window': window})


def between_wrapper(fstr, token, ai):
    aa = ARGS_REGEX.search(token).group(0)[1:-1].split(',')
    kk = aa[0]
    if '.' in kk:
        kk = kk.split('.')[0].strip()

    for aa in ((DEFLECTION_REGEX, 'obj.get_deflection(attr, current=True)'),
               (BASELINECOR_REGEX, 'aa.get_baseline_corrected_value(attr)'),
               (BASELINE_REGEX, 'aa.get_baseline_value(attr)'),
               (MIN_REGEX, 'aa.get_values(attr, window or -1).min()', kfunc()),
               (MAX_REGEX, 'aa.get_values(attr, window or -1).max()', kfunc()),
               (CP_REGEX, 'aa.get_current_intensity(attr)')):
        if len(aa) == 2:
            r, ff = aa
            kf = lambda x: x
        else:
            r, ff, kf = aa
        # print kk, ai, ff, reg.match(kk)
        if r.match(kk):
            # print 'matrch', ff, kk, ai
            return wrapper(ff, token, kf(kk))
    else:
        # if '.' in ai:
        #     self.unique_warning('invalid modifier teststr="{}"'.format(kk))
        #     return
        # else:
        return wrapper(fstr, token, ai)


#teststr
def teststr_func(token):
    c = remove_attr(token)
    a = extract_attr(token)
    ts = '{}{}'.format(a, c)
    return a, a, ts


def between_teststr(token):
    args = ARGS_REGEX.search(token).group(0)[1:-1].split(',')
    kk = args[0]
    if '.' in kk:
        kk = kk.replace('.', '_')
    else:
        for rargs in ((MIN_REGEX,),
                      (MAX_REGEX,)):
            if len(rargs) == 2:
                r, kf = rargs
            else:
                r = rargs[0]
                kf = kfunc()
            if r.match(kk):
                kk = kf(kk)
                break
    v1, v2 = args[1:]
    return kk, kk, '{}<={}<={}'.format(v1, kk, v2)


def ratio_teststr(token):
    c = remove_attr(token)
    key = token.replace(c, '')
    attr = 'ratio{}'.format(key.replace('/', ''))
    teststr = '{}{}'.format(attr, c)
    return attr, key, teststr


def kfunc(n=4):
    def dec(k):
        return k[n:-1]

    return dec


def tokenize(teststr):
    def func():
        ts = teststr.split(' ')
        i = 0
        is_not = False
        while 1:
            try:
                a = ts[i]
                if a == 'not':
                    i += 1
                    is_not = True
                    continue
                b = ts[i + 1]
            except IndexError:
                b = None
                break

            i += 2
            if is_not:
                a = 'not {}'.format(a)
                is_not = False

            yield a, b

        if is_not:
            a = 'not {}'.format(a)

        yield a, b

    return list(func())


def remove_attr(s):
    """
        return >10 where s=Ar40>10
    """
    try:
        c = COMP_REGEX.findall(s)[0]
        return '{}{}'.format(c, s.split(c)[-1])
    except IndexError:
        return ''


def remove_comp(s):
    try:
        c = COMP_REGEX.findall(s)[0]
        s = s.split(c)[0]
        if s.startswith('not '):
            s = s[4:]
        return s
    except IndexError, e:
        return s


def extract_attr(key):
    """
    """

    m = PARENTHESES_REGEX.findall(key)
    if m:
        key = m[0][1:-1]
    else:
        m = KEY_REGEX.findall(key)
        if m:
            k = m[0]
            if k in ('not',):
                k = m[1]
            key = k

    return key

# ============= EOF =============================================



