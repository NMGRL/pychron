# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
# ============= standard library imports ========================

import re

# ============= local library imports  ==========================

ALIQUOT_REGEX = re.compile('\S+-+\d+$')


def make_image_regex(ext):
    if ext is None:
        ext = ('png', 'tif', 'gif', 'jpeg', 'jpg', 'pct')
    s = '[\d\w-]+\.({})'.format('|'.join(ext))
    return re.compile(s)


ISOREGEX = re.compile(r'[A-Za-z]{1,2}\d+$')
ALT_ISOREGEX = re.compile(r'\d+[A-Za-z]{1,2}$')

PACKETREGEX = re.compile(r'(?P<prefix>[a-zA-Z]+)?(?P<number>\d+)')
IPREGEX = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
URLREGEX = re.compile(r'^[\w\-_]+\.([\w\-_].*)*$')
GITREFREGEX = re.compile(r'^[\w]{40}')

MDD_PARAM_REGEX = re.compile(r'E= {3}(?P<E>\d+.\d+) {7}\+\- {4}(?P<Eerr>\d+.\d+) '
                             r'{11}Ordinate= {3}(?P<O>\d+.\d+) {7}\+\- {2}(?P<Oerr>\d+.\d+)')

STEPREGEX = re.compile(r'^[a-zA-Z]+$|^[0-9]+$')

DETREGEX = re.compile(r'^(H1|H2|L1|L2|CDD|AX)(\(CDD\))?$')

tags = 'icfactors', 'blanks', 'baselines', 'intercepts', 'peakcenter'
a = '|'.join(['{}\\/'.format(tag) for tag in tags])
b = '|'.join(['{}\\.'.format(tag[:4]) for tag in tags])
p = r'^.{{3,5}}\/(?P<tag>{})?[\w-]+\.({})?json$'.format(a, b)
RUNID_PATH_REGEX = re.compile(p)

TAG_PATH_REGEX = re.compile(r'^(?P<head>\w{5})\/tags\/(?P<tail>[\w-]*).tags.json$')

ORDER_PREFIX_REGEX = re.compile(r'^(?P<prefix>\d+:)(?P<label>.*)$')

LOAD_REGEX = re.compile(r'^(?P<prefix>.*?)(?P<inc>\d+)$')
# ============= EOF =============================================
