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
from enable.component_editor import ComponentEditor
from traits.api import Button
from traitsui.api import View, Item, Readonly, UItem
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pyface.tasks.traits_task_pane import TraitsTaskPane


class FurnacePane(TraitsTaskPane):
    dump_sample_button = Button('Dump')

    def _dump_sample_button_fired(self):
        self.model.dump_sample()

    def traits_view(self):
        v = View(Item('setpoint'),
                 Readonly('setpoint_readback'),
                 UItem('pane.dump_sample_button'),
                 UItem('canvas', style='custom', editor=ComponentEditor()),

                 )
        return v

# ============= EOF =============================================
