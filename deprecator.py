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
import os


def locate_deprecated(root):
    i=1
    cnt=0
    dcnt=0
    for r, ds, fs in os.walk(root):
        dcnt+=1
        for fi in fs:
            if not fi.endswith('.py') or fi == '__init__.py':
                continue

            cnt+=1
            p = os.path.join(r, fi)
            with open(p, 'r') as fp:
                for li in fp:
                    li = li.strip()
                    if li and not li.startswith('#'):
                        break
                else:
                    print '{:03n} is deprecated {}'.format(i, p)
                    i+=1

    print 'examined {} files from {} directories'.format(cnt, dcnt)

locate_deprecated('/Users/ross/Programming/git/pychron_dev/pychron')


# ============= EOF =============================================



