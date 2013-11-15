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
import re
#============= local library imports  ==========================
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
TRANSECT_REGEX = re.compile('[tT]+[\d\W]+-+[\d\W]+$')

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
POSITION_REGEX = re.compile('[pPlLrRdD\d]?[\d]$|[\d]$')

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

ALIQUOT_REGEX = re.compile('\d+-+\d+$')

'''
    e.g. 1-4
    
'''
SLICE_REGEX = re.compile('[\d]+-{1}[\d]+$')
SSLICE_REGEX = re.compile('\d+:{1}\d+:{1}\d+$')
PSLICE_REGEX = re.compile('\d+:{1}\d+$')


def make_image_regex(ext):
    if ext is None:
        ext = ('png', 'tif', 'gif', 'jpeg', 'jpg', 'pct')
    s = '[\d\w-]+\.({})'.format('|'.join(ext))
    return re.compile(s)


ISOREGEX = re.compile('[A-Za-z]{1,2}\d+$')
ALT_ISOREGEX = re.compile('\d+[A-Za-z]{1,2}$')
#============= EOF =============================================
