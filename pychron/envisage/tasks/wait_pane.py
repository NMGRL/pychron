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
from pyface.tasks.traits_dock_pane import TraitsDockPane
from traitsui.api import View, UItem, Item, HGroup, VGroup, spring, Spring, \
    RangeEditor, ListEditor, InstanceEditor
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.ui.custom_label_editor import CustomLabel


class WaitPane(TraitsDockPane):
    id = 'pychron.wait'
    name = 'Wait'

    def traits_view(self):
        cview = View(VGroup(
            CustomLabel('message',
                        size=14,
                        weight='bold',
                        color_name='message_color'),

            HGroup(Spring(width=-5, springy=False),
                   Item('high', label='Set Max. Seconds'),
                   spring,
                   CustomLabel('current_time',
                               size=14,
                               weight='bold'),
                   UItem('continue_button')),
            HGroup(Spring(width=-5, springy=False),
                   Item('current_time', show_label=False,
                        editor=RangeEditor(mode='slider', low=1, high_name='duration')))))

        v = View(UItem('active_control',
                       style='custom',
                       visible_when='single',
                       editor=InstanceEditor(view=cview)),
                 UItem('controls',
                       editor=ListEditor(
                           use_notebook=True,
                           selected='active_control',
                           page_name='.page_name',
                           view=cview),
                       style='custom',
                       visible_when='not single'))
        return v

# ============= EOF =============================================
