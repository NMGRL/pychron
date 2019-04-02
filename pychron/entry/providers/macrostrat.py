# ===============================================================================
# Copyright 2017 ross
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
import requests

DEFS_URL = 'http://macrostrat.org/api/defs'
CACHED_LITHOLOGIES = None


def get_minerals(min_type=None):
    s = requests.Session()

    url = '{}/minerals?'.format(DEFS_URL)
    if min_type:
        url = '{}mineral_type={}'.format(min_type)
    else:
        url = '{}all'.format(url)

    r = s.get(url)
    obj = r.json()

    return obj['success']['data']


def get_lithologies(lith_type=None, lith_class=None, lith_group=None):
    s = requests.Session()

    url = '{}/lithologies?'.format(DEFS_URL)
    qs = []
    if lith_type:
        qs.append('lith_type={}'.format(lith_type))

    if lith_class:
        qs.append('lith_class={}'.format(lith_class))

    if lith_group:
        qs.append('lith_group={}'.format(lith_group))

    if not qs:
        url = '{}all'.format(url)
    else:
        url = '{}{}'.format(url, '&'.join(qs))

    r = s.get(url)

    obj = r.json()
    return obj['success']['data']


def get_lithology_values():
    global CACHED_LITHOLOGIES
    ret = CACHED_LITHOLOGIES
    if ret is None:
        ls = get_lithologies()
        groups = []
        classes = []
        types = []
        liths = []
        for li in ls:
            groups.append(li['group'])
            types.append(li['type'])
            classes.append(li['class'])
            liths.append(li['name'])

        ret = [sorted(list(set(a))) for a in (liths, groups, classes, types)]
        CACHED_LITHOLOGIES = ret

    return ret


# ============= EOF =============================================
