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
from pyface.tasks.traits_dock_pane import TraitsDockPane
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traitsui.api import View, UItem, HGroup, Item, VGroup

# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.editors import TabularEditor
from traitsui.tabular_adapter import TabularAdapter
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.envisage.icon_button_editor import icon_button_editor


class ExportAnalysisAdapter(TabularAdapter):
    columns = [('RunID', 'record_id'), ('Sample', 'sample'), ('Tag', 'tag')]
    font = '10'


class ExportCentralPane(TraitsTaskPane):
    def traits_view(self):
        editor = TabularEditor(adapter=ExportAnalysisAdapter(),
                               editable=False)
        v = View(
            VGroup(HGroup(Item('kind', label='Export Kind')),
                   # VGroup(UItem('object.exporter.destination', style='custom'),
                   #        label='Destination', show_border=True),
            UItem('exported_analyses', editor=editor)))
        return v

#
#
# class DestinationPane(TraitsDockPane):
#     name = 'Destination'
#     id = 'pychron.export.destination'
#
#     def traits_view(self):
#         v = View(
#             UItem('kind'),
#             UItem('object.exporter.destination', style='custom'))
#         return v
#
#     # ============= EOF =============================================
#
