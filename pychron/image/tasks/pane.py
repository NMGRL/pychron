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
from traits.api import HasTraits, Button
from traitsui.api import View, Item, VGroup, UItem
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.ui.qt.camera_editor import CameraEditor
from pychron.core.ui.qt.tabular_editors import FilterTabularEditor
from pychron.envisage.browser.adapters import LabnumberAdapter, ProjectAdapter


class CameraPane(TraitsTaskPane):
    def traits_view(self):
        v = View(UItem('camera', editor=CameraEditor(),
                       width=680, height=510))
        # v = View(UItem('camera', editor=CameraEditor()))
        return v

class SampleBrowserPane(TraitsDockPane):
    id = 'pychron.image.browser'
    name = 'Browser'

    def traits_view(self):
        sample_grp = VGroup(UItem('samples',
                                  editor=FilterTabularEditor(
                                      adapter=LabnumberAdapter(),
                                      editable=False,
                                      multi_select=True,
                                      selected='selected_samples',
                                      stretch_last_section=False),
                                  height=-200,
                                  width=75),
                            show_border=True, label='Samples')

        project_grp = VGroup(
            UItem('projects',
                  editor=FilterTabularEditor(editable=False,
                                             selected='selected_projects',
                                             adapter=ProjectAdapter(),
                                             multi_select=True),
                  height=-200,
                  width=175),
            show_border=True,
            label='Projects')

        v = View(VGroup(project_grp, sample_grp))
        return v
# ============= EOF =============================================


