# ===============================================================================
# Copyright 2015 Jake Ross
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
import os
import time

from traits.api import HasTraits, Str, Int, List, Event
from traitsui.api import View, UItem

# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.paths import paths


def update_launch_history(path):
    out = []
    with open(paths.experiment_launch_history, 'r') as rfile:
        for line in rfile:
            l, t, p = line.split(',')
            if p == path:
                t += 1
                l = time.time()
            out.append((t, l, p))

        else:
            out.append((time.time(), 1, p))

    with open(paths.experiment_launch_history, 'w') as wfile:

        for o in sorted(out, reverse=True)[:25]:
            wfile.write('{},{},{}\n'.format(*o))


class ELHAdapter(TabularAdapter):
    columns = [('Name', 'name'), ('Last', 'last_run_time'), ('N', 'total_launches')]


class LaunchItem(HasTraits):
    name = Str
    path = Str
    last_run_time = Str
    total_launches = Int


class ExperimentLaunchHistory(HasTraits):
    items = List
    selected = LaunchItem
    dclicked = Event

    def load(self):
        def factory(l):
            l = l.strip()
            if l:
                l, t, p = l.split(',')
                n = os.path.basename(p)
                n, _ = os.path.splitext(n)
                return LaunchItem(name=n, path=p, last_run_time=l, total_launches=int(t))

        with open(paths.experiment_launch_history, 'r') as rfile:
            items = [factory(line) for line in rfile]
            self.items = [i for i in items if i]

    def traits_view(self):
        v = View(UItem('items', editor=myTabularEditor(adapter=ELHAdapter(),
                                                       selected='selected',
                                                       dclicked='dclicked',
                                                       editable=False)),
                 title='Experiment Launch History',
                 buttons=['OK', 'Cancel'],
                 resizable=True, kind='livemodal')
        return v


if __name__ == '__main__':
    elh = ExperimentLaunchHistory()
    elh.configure_traits()
# ============= EOF =============================================
