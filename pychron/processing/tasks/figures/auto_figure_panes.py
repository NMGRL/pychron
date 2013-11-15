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
from traits.api import HasTraits, Any
from traitsui.api import View, Item, UItem, InstanceEditor
from pyface.tasks.traits_dock_pane import TraitsDockPane
#============= standard library imports ========================
#============= local library imports  ==========================

class AutoFigureControlPane(TraitsDockPane):
    id = 'pychron.processing.auto_figure_controls'
    name = 'Auto Figure Controls'
    auto_control = Any
    def traits_view(self):
        return View(UItem('auto_control',
                          style='custom',
                          editor=InstanceEditor()))
#         v = View(Item('group_by_labnumber'))
#         return v
#============= EOF =============================================
