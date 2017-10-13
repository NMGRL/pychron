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


class MacroStrat:
    api_url = 'http://macrostrat.org/api'

    def get_lithologies(self, lith_type=None, lith_class=None, lith_group=None):
        s = requests.Session()

        url = '{}/defs/lithologies?'.format(self.api_url)
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

        print 'url={}'.format(url)
        r = s.get(url)

        obj = r.json()
        # print obj.keys()
        return obj['success']['data']

    def get_lithology_values(self):
        ls = self.get_lithologies()
        groups = []
        classes = []
        types = []

        for li in ls:
            groups.append(li['group'])
            types.append(li['type'])
            classes.append(li['class'])

        groups = list(set(groups))
        classes = list(set(classes))
        types = list(set(types))

        return groups, classes, types

    def get_minerals(self, min_type=None):
        s = requests.Session()

        url = '{}/defs/minerals?'.format(self.api_url)
        if min_type:
            url = '{}mineral_type={}'.format(min_type)
        else:
            url = '{}all'.format(url)

        print 'url={}'.format(url)
        r = s.get(url)
        obj = r.json()

        return obj['success']['data']


if __name__ == '__main__':
    c =  MacroStrat()
    # c.get_lithologies()
    print c.get_lithology_values()
# ============= EOF =============================================
