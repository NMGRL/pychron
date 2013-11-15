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
from traits.api import HasTraits, List, Button
from traitsui.api import View, Item, TabularEditor, HGroup, spring
from traitsui.tabular_adapter import TabularAdapter
#============= standard library imports ========================
#============= local library imports  ==========================

class ProcessAdapter(TabularAdapter):
    columns = [('Name', 'name'), ('RunID', 'rid'),
               ('State', 'state'),
#               ('Dur.', 'duration')
               ]


class ProcessView(HasTraits):
    processes = List
    clear = Button

    def _clear_fired(self):
        self.processes = []

    def traits_view(self):
        p = Item('processes', show_label=False,
                 editor=TabularEditor(adapter=ProcessAdapter(),
                                      editable=False
                                      )
                 )
        v = View(p,
                 HGroup(spring, Item('clear', show_label=False))
                 )
        return v

    def update_plist(self, obj, name, old, new):
        if new:
            self.processes.append(new[0])
        else:
            self.processes.remove(old[0])

#============= EOF =============================================
