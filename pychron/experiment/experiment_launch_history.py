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
from pychron.core.ui import set_qt

set_qt()
# ============= enthought library imports =======================
from pyface.timer.do_later import do_later
from traits.api import HasTraits, Str, Int, List, Event, Instance
from traitsui.api import View, UItem, Handler
from traitsui.tabular_adapter import TabularAdapter

# ============= standard library imports ========================
import os
import time
# ============= local library imports  ==========================
from pychron.core.helpers.datetime_tools import get_datetime
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.paths import paths


def update_launch_history(path):
    out = []
    exists = False
    if os.path.isfile(paths.experiment_launch_history):
        with open(paths.experiment_launch_history, 'r') as rfile:
            for line in rfile:
                line = line.strip()
                if line:
                    l, t, p = line.split(',')
                    t = int(t)
                    if p == path:
                        t += 1
                        l = time.time()
                        exists = True
                    out.append((l, t, p))

    if not exists:
        out.append((time.time(), 1, path))
        # else:
        # out.append((time.time(), 1, p))

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


class ELHHandler(Handler):
    def object_dclicked_changed(self, info):
        if info.initialized:
            do_later(info.ui.dispose, True)


class ExperimentLaunchHistory(HasTraits):
    items = List
    selected = Instance(LaunchItem)
    dclicked = Event

    def load(self):
        def factory(l):
            l = l.strip()
            if l:
                l, t, p = l.split(',')
                n = os.path.basename(p)
                n, _ = os.path.splitext(n)

                l = get_datetime(float(l)).strftime('%a %H:%M %m-%d-%Y')

                return LaunchItem(name=n, path=p, last_run_time=l, total_launches=int(t))

        with open(paths.experiment_launch_history, 'r') as rfile:
            items = [factory(line) for line in rfile]
            self.items = [i for i in items if i]

    def traits_view(self):
        v = View(UItem('items', editor=myTabularEditor(adapter=ELHAdapter(),
                                                       selected='selected',
                                                       dclicked='dclicked',
                                                       editable=False)),
                 handler=ELHHandler(),
                 width=700,
                 title='Experiment Launch History',
                 buttons=['OK', 'Cancel'],
                 resizable=True, kind='livemodal')
        return v


if __name__ == '__main__':
    paths.build('_dev')
    elh = ExperimentLaunchHistory()
    elh.load()
    elh.configure_traits()
# ============= EOF =============================================
