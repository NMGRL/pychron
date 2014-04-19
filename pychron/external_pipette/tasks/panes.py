#===============================================================================
# Copyright 2014 Jake Ross
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
from traitsui.api import View, Item, UItem, VGroup, HGroup
from enable.component_editor import ComponentEditor
from pyface.tasks.traits_task_pane import TraitsTaskPane

#============= standard library imports ========================
#============= local library imports  ==========================


class ExternalPipettePane(TraitsTaskPane):
    def traits_view(self):
        v = View(VGroup(HGroup(UItem('test_load_1',
                                     enabled_when='not testing'),
                               UItem('reload_canvas_button')),
                        Item('test_result',
                      style='readonly',
                      label='Test Result')),
                 UItem('canvas', style='custom',
                       editor=ComponentEditor()))
        return v

#============= EOF =============================================

