#===============================================================================
# Copyright 2013 Jake Ross
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
import re

#============= standard library imports ========================
#============= local library imports  ==========================

def pos_gen(s, e, inc=1):
    if s > e:
        inc *= -1
    return range(s, e + inc, inc)


def increment_list(ps, start=0):
    if len(ps) == 1:
        return [ps[0] + 1]
    else:
        s, e, o = ps[0], ps[-1], ps[1] - ps[0]
        #i=1 if s<e else -1
        if start:
            n = start
        else:
            n = e - s + o

        return [p + n for p in ps]


def slice_func(pos):
    s, e = map(int, pos.split('-'))
    return pos_gen(s, e)


def islice_func(pos, start=0):
    ps = slice_func(pos)
    nls = increment_list(ps, start)
    return '{}-{}'.format(nls[0], nls[-1])


def sslice_func(pos):
    s, e, inc = map(int, pos.split(':'))
    return pos_gen(s, e, inc)


def isslice_func(pos):
    ps = sslice_func(pos)
    nls = increment_list(ps)
    step = nls[1] - nls[0]
    return '{}:{}:{}'.format(nls[0], nls[-1], step)


def pslice_func(pos):
    s, e = map(int, pos.split(':'))
    return pos_gen(s, e)


def ipslice_func(pos):
    ps = pslice_func(pos)
    nls = increment_list(ps)
    return '{}:{}'.format(nls[0], nls[-1])


def cslice_func(pos):
    args = pos.split(';')
    positions = []
    for ai in args:
        if '-' in ai:
            positions.extend(slice_func(ai))
        else:
            positions.append(int(ai))
    return positions


def icslice_func(pos):
    args = pos.split(';')
    ns = []
    x = args[-1]

    if '-' in x:
        start = int(x.split('-')[-1])
    else:
        start = int(x)

    for ai in args:
        if '-' in ai:
            ns.append(islice_func(ai, start))
        else:
            ns.append(str(int(ai) + start))

    return ';'.join(ns)


SLICE_REGEX = (re.compile(r'[\d]+-{1}[\d]+$'),
               slice_func, islice_func)#1-4
SSLICE_REGEX = (re.compile(r'\d+:{1}\d+:{1}\d+$'),
                sslice_func, isslice_func) #1:4:2
PSLICE_REGEX = (re.compile(r'\d+:{1}\d+$'),
                pslice_func, ipslice_func) #1:4

# 1-4;6;9;11-15
# 1-4;6;9
# 1-4;6
# 6;9;11-15
# 1-4;6;9;11-15;50-42

CSLICE_REGEX = (re.compile(r'((\d+-\d+)|\d+)(;+\d+)+((-\d+)|(;+\d+))*'),
                cslice_func, icslice_func)

'''
    use regex to match valid tansect entry
    e.g t2-3   point 3 of transect 2

    this re says
    match any string where
    1. [tT]     the first character is t or T
    2. [\d\W]+  followed by at least one digit character and no word characters
    3. -         followed by -
    4. [\d\W]+  followed by at least one digit character and no word characters
    5  $         end of string
'''
TRANSECT_REGEX = (re.compile('[tT]+[\d\W]+-+[\d\W]+$'), None, None)

'''
    use regex to match valid position
    e.g. p1, 1

    this re says
    match any string where
    1. [pPlLrRdD\d]     the first character is p,P,l,L,r,R,d,D or any digit
    2. [\d\W]$  followed by at least one digit character and no word characters
    3. | or
    4. [\d\W]$  at least one digit character and no word characters

'''
# POSITION_REGEX = re.compile('[pPlLrRdD\d]+[\d\W]$|[\d\W]$')
POSITION_REGEX = (re.compile('[pPlLrRdD\d]?[\d]$|[\d]$'), None, None)

'''
    e.g. 1.00,3.01
'''
XY_REGEX = re.compile('[-,\d+].*\d*,[-,\d+].*\d*')

'''
    e.g d1
        d2
        D34
'''
DRILL_REGEX = re.compile('[dD]\d+$')
POINT_REGEX = re.compile('p\d+$')
#============= EOF =============================================
