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
from __future__ import absolute_import

import re

# ============= local library imports  ==========================

ALIQUOT_REGEX = re.compile('\d+-+\d+$')


def make_image_regex(ext):
    if ext is None:
        ext = ('png', 'tif', 'gif', 'jpeg', 'jpg', 'pct')
    s = '[\d\w-]+\.({})'.format('|'.join(ext))
    return re.compile(s)


ISOREGEX = re.compile('[A-Za-z]{1,2}\d+$')
ALT_ISOREGEX = re.compile('\d+[A-Za-z]{1,2}$')

PACKETREGEX = re.compile(r'(?P<prefix>[a-zA-Z]+)?(?P<number>\d+)')
IPREGEX = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')

GITREFREGEX = re.compile(r'^[\w]{40}')

MDD_PARAM_REGEX = re.compile(r'E= {3}(?P<E>\d+.\d+) {7}\+\- {4}(?P<Eerr>\d+.\d+) '
                             r'{11}Ordinate= {3}(?P<O>\d+.\d+) {7}\+\- {2}(?P<Oerr>\d+.\d+)')

# ============= EOF =============================================
