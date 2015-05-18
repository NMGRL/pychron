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
from traits.api import List, Instance, on_trait_change
from traits.has_traits import HasTraits
from traits.trait_types import Any, Str
from traitsui.api import View, UItem, InstanceEditor
# ============= standard library imports ========================
# ============= local library imports  ===========================
from pychron.envisage.tasks.base_editor import BaseTraitsEditor
from pychron.processing.plotter_options_manager import IdeogramOptionsManager
from pychron.processing.plot.models.ideogram_model import IdeogramModel
from pychron.processing.plot.panels.ideogram_panel import IdeogramPanel


class OptionsView(HasTraits):
    model = Any
    title = Str

    def traits_view(self):
        v = View(UItem('model',
                       style='custom',
                       editor=InstanceEditor()),
                 title=self.title,
                 resizable=True,
                 kind='livemodal',
                 height=0.8,
                 buttons=['OK'])

        return v


class BaseSummaryEditor(BaseTraitsEditor):
    analyses = List

    ideogram_graph = Any
    ideogram_model = Instance(IdeogramModel)
    ideogram_options = Instance(IdeogramOptionsManager)
    ideogram_panel = Instance(IdeogramPanel)

    basename = 'Summary'

    def _create_ideogram(self):
        self.ideogram_options = IdeogramOptionsManager()
        model = IdeogramModel(analyses=self.analyses,
                              plot_options=self.ideogram_options.plotter_options)
        model.refresh_panels()
        p = model.next_panel()

        self.ideogram_graph = p.make_graph()
        self.ideogram_model = model
        self.ideogram_panel = p

    @on_trait_change('tool:ideogram_options_button')
    def _ideogram_options_button_fired(self):
        v = OptionsView(model=self.ideogram_options,
                        title='Edit Ideogram Options')
        v.edit_traits()

    @on_trait_change('ideogram_options:plotter_options:refresh_plot')
    def _ideogram_update(self):
        model = self.ideogram_model
        model.refresh_panels()
        p = model.next_panel()
        self.ideogram_graph = p.make_graph()

    @on_trait_change('ideogram_options:plotter_options')
    def _ideogram_options_update(self, new):
        self.ideogram_model.plot_options = new

# ============= EOF =============================================



