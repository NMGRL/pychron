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
import re

icon_matcher = re.compile(r"icon\('\w+(\.png)*'\)")
ibe_matcher = re.compile(r"icon_button_editor\([\'\(\)\w]+, *\'\w+(\.png)*'")

def locate_used_icons(root):
    def func():
        found = []
        cnt = 0
        dcnt = 0
        lcnt = 0
        for r, ds, fs in os.walk(root):
            # print r
            dcnt += 1
            for fi in fs:
                if not fi.endswith('.py') or fi == '__init__.py':
                    continue

                cnt += 1
                p = os.path.join(r, fi)
                with open(p, 'r') as fp:
                    for li in fp:
                        lcnt += 1
                        li = li.strip()
                        if li.startswith('#'):
                            continue
                        else:
                            # for mat in (icon_matcher, ibe_matcher):
                            for mat in (icon_matcher, ibe_matcher):
                                g = mat.search(li)
                                if g:
                                    m = g.group(0)
                                    if m.startswith('icon_button_editor'):
                                        name=m.split(',')[-1].strip()[1:-1]
                                    else:
                                        name = m[6:-2]
                                    if name in found:
                                        continue
                                    else:
                                        found.append(name)
                                        yield dcnt, cnt, lcnt, m, name
                                        break

        # do a last yield to pass counts
        yield dcnt, cnt, lcnt, None, None

    with open(os.path.join(os.path.dirname(root), 'resources','icon_requirements.txt'), 'w') as fp:
        for di, ci, lcnt, m,name in func():
            if m and name:
                print '{:<40s}{}'.format(name, m)
                fp.write('{}\n'.format(name))

    print 'examined {} files from {} directories {}'.format(ci, di, lcnt)


locate_used_icons('/Users/ross/Programming/git/pychron_dev/pychron')


# ============= EOF =============================================




