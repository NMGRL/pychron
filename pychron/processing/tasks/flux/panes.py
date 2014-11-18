#===============================================================================
# Copyright 2013 Jake Ross
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
from traitsui.api import View, Item, EnumEditor, VGroup, TabularEditor, UItem
from pyface.tasks.traits_dock_pane import TraitsDockPane
#============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter


class IrradiationPane(TraitsDockPane):
    name = 'Irradiation'
    id = 'pychron.processing.irradiation'

    def traits_view(self):
        v = View(VGroup(
            Item('irradiation',
                 editor=EnumEditor(name='irradiations')),
            Item('level', editor=EnumEditor(name='levels'))))

        return v


class AnalysisAdapter(TabularAdapter):
    columns = [('RunID', 'record_id'),
               ('Tag', 'tag')]


class AnalysesPane(TraitsDockPane):
    id = 'pychron.processing.analyses'
    name = 'Anaylses'

    def traits_view(self):
        v = View(UItem('analyses',
                       editor=TabularEditor(adapter=AnalysisAdapter())
        ))
        return v

#============= EOF =============================================
