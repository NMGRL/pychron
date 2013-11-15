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
from pyface.tasks.traits_dock_pane import TraitsDockPane
from traits.api import HasTraits, Str, Instance
from traitsui.api import View, Item

#============= standard library imports ========================
#============= local library imports  ==========================

class SmartSelection(HasTraits):
    project_filter = Str


class SmartSelectionConfigurePane(TraitsDockPane):
    id = 'pychron.smart_selection.configure'

    model = Instance(SmartSelection, ())

    def traits_view(self):
        v = View(Item('project_filter'))
        return v

    #============= EOF =============================================
