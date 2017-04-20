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

ALIQUOT_REGEX = re.compile('\d+-+\d+$')


def make_image_regex(ext):
    if ext is None:
        ext = ('png', 'tif', 'gif', 'jpeg', 'jpg', 'pct')
    s = '[\d\w-]+\.({})'.format('|'.join(ext))
    return re.compile(s)


ISOREGEX = re.compile('[A-Za-z]{1,2}\d+$')
ALT_ISOREGEX = re.compile('\d+[A-Za-z]{1,2}$')
# ============= EOF =============================================
