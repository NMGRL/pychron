# ===============================================================================
# Copyright 2016 ross
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

# ============= standard library imports ========================
# ============= local library imports  ==========================
from __future__ import absolute_import

import re

from uncertainties import nominal_value, std_dev

from pychron.pychron_constants import PLUSMINUS, SIGMA, LAMBDA


def iso_value(attr, ve='value'):
    def f(x, k):
        if k in x.isotopes:
            iso = x.isotopes[k]
            if attr == 'intercept':
                v = iso.uvalue
            elif attr == 'baseline_corrected':
                v = iso.get_baseline_corrected_value()
            elif attr == 'baseline':
                v = iso.baseline.uvalue
            elif attr == 'disc_ic_corrected':
                v = iso.get_intensity()
            elif attr == 'interference_corrected':
                v = iso.get_interference_corrected_value()
            elif attr == 'blank':
                v = iso.blank.uvalue
        if v is not None:
            return nominal_value(v) if ve == 'value' else std_dev(v)
        else:
            return ''

    return f


def correction_value(ve='value'):
    def f(x, k):
        v = None
        if k in x.interference_corrections:
            v = x.interference_corrections[k]
        elif k in x.production_ratios:
            v = x.production_ratios[k]

        if v is not None:
            return nominal_value(v) if ve == 'value' else std_dev(v)
        else:
            return ''

    return f


def icf_value(x, k):
    det = k.split('_')[0]
    return nominal_value(x.get_ic_factor(det))


def icf_error(x, k):
    det = k.split('_')[0]
    v = std_dev(x.get_ic_factor(det))
    if v < 1e-10:
        v = 0
    return v


def value(x, k):
    x = getattr(x, k)
    if x is not None:
        return nominal_value(x)
    else:
        return ''


def error(x, k):
    x = getattr(x, k)
    if x is not None:
        return std_dev(x)
    else:
        return ''


def age_value(target_units='Ma'):
    def wrapper(x, k):
        v = value(x, k)
        if v and target_units != x.arar_constants.age_units:
            v = x.arar_constants.scale_age(v, target_units)
            # v /= x.arar_constants.ma_age_scalar
        return v
    return wrapper


subreg = re.compile(r'^<sub>(?P<item>.+)</sub>')
supreg = re.compile(r'^<sup>(?P<item>.+)</sup>')
italreg = re.compile(r'^<ital>(?P<item>.+)</ital>')
boldreg = re.compile(r'^<bold>(?P<item>.+)</bold>')


def interpolate_noteline(line, sup, sub, ital, bold):
    line = line.replace('<plus_minus>', PLUSMINUS)
    line = line.replace('<sigma>', SIGMA)
    line = line.replace('<lambda>', LAMBDA)

    def parse(line):
        args = []
        for fmt, reg, taglen in ((sup, supreg, 5),
                                 (sub, subreg, 5),
                                 (ital, italreg, 6),
                                 (bold, boldreg, 6),
                                 ):
            g = reg.match(line)
            if g:
                args.append(fmt)
                args.append('{} '.format(g.group('item')))
                break
        else:
            args.append('{} '.format(line))
        return args

    ns = []
    for token in line.split(' '):
        ns.extend(parse(token))
    return ns
# ============= EOF =============================================
