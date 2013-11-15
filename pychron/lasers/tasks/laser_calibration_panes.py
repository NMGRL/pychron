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
from traitsui.api import View, UItem, Group, InstanceEditor, HGroup, \
    EnumEditor, Item, spring, Spring, ButtonEditor, VGroup, RangeEditor, \
        VFold
# from pyface.tasks.traits_task_pane import TraitsTaskPane
from pyface.tasks.traits_dock_pane import TraitsDockPane
#============= standard library imports ========================
#============= local library imports  ==========================
class LaserCalibrationExecutePane(TraitsDockPane):
    name = 'Execute'
    id = 'pychron.laser_calibration.execute'
    def traits_view(self):
        v = View(
                 UItem('execute',
                       editor=ButtonEditor(label_value='execute_label')
                       )
                 )
        return v

class LaserCalibrationControlPane(TraitsDockPane):
    name = 'Control'
    id = 'pychron.laser_calibration.control'
    editor = Any
    def traits_view(self):
        v = View(
                 UItem('editor', style='custom',
                       editor=InstanceEditor()
                       )
                 )
        return v
#============= EOF =============================================
