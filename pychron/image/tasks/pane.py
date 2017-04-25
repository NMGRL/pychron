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
from traitsui.api import View, VGroup, UItem, TabularEditor, Item, TextEditor
from traitsui.tabular_adapter import TabularAdapter

from pychron.core.ui.qt.tabular_editors import FilterTabularEditor
from pychron.envisage.browser.adapters import ProjectAdapter, SampleImageAdapter


class ImageAdapter(TabularAdapter):
    columns = [('Name', 'name'), ('Date', 'create_date')]


# class CameraPane(TraitsTaskPane):
#     def traits_view(self):
#         v = View(UItem('camera', editor=CameraEditor(save_event='save_event'),
#                        width=896, height=680))
#         # v = View(UItem('camera', editor=CameraEditor()))
#         return v

class InfoPane(TraitsDockPane):
    id = 'pychron.image.info'
    name = 'Image Info'

    def traits_view(self):
        v=View(VGroup(Item('object.selected_info_model.create_date', style='readonly'),
                      Item('object.selected_info_model.name'),
                      VGroup(UItem('object.selected_info_model.note', style='custom',
                                   editor=TextEditor(read_only=False)))))
        return v


class SampleBrowserPane(TraitsDockPane):
    id = 'pychron.image.browser'
    name = 'Browser'

    def traits_view(self):
        sample_grp = VGroup(UItem('samples',
                                  editor=FilterTabularEditor(
                                      # adapter=LabnumberAdapter(),
                                      adapter=SampleImageAdapter(),
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
        image_grp = VGroup(UItem('images',
                                 editor=TabularEditor(editable=False,
                                                      adapter=ImageAdapter(),
                                                      multi_select=False,
                                                      dclicked='dclicked',
                                                      selected='selected_image')),
                           show_border=True,
                           label='Images')
        v = View(VGroup(project_grp, sample_grp, image_grp))
        return v

# ============= EOF =============================================


