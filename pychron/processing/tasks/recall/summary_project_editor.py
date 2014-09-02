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
from enable.component_editor import ComponentEditor
from traits.api import HasTraits, Button, Instance
from traitsui.api import View, VGroup, UItem
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.processing.tasks.recall.base_summary_editor import BaseSummaryEditor


class SummaryProjectTool(HasTraits):
    ideogram_options_button = Button

    def traits_view(self):
        igrp=VGroup(icon_button_editor('ideogram_options_button', 'cog'),
                    label='Ideogram',show_border=True)
        v=View(VGroup(igrp))
        return v


class SummaryProjectEditor(BaseSummaryEditor):
    tool =Instance(SummaryProjectTool, ())

    def load(self):
        self._create_ideogram()


    def traits_view(self):
        ideogram_grp = VGroup(UItem('ideogram_graph',
                                    visible_when='ideogram_visible',
                                    editor=ComponentEditor()),
                              label='Ideogram')
        v=View(ideogram_grp)
        return v
#============= EOF =============================================



