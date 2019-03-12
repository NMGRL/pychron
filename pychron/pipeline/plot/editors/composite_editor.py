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
from traits.api import Instance, on_trait_change

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.options.options_manager import CompositeOptionsManager
from pychron.pipeline.plot.editors.figure_editor import FigureEditor
from pychron.pipeline.plot.models.composite_model import CompositeModel


class CompositeEditor(FigureEditor):
    plotter_options_manager = Instance(CompositeOptionsManager, ())
    figure_model_klass = CompositeModel

    @on_trait_change('figure_model:panels:figures:recalculate_event')
    def _handle_recalculate(self, obj, name, old, new):
        print('recalads')

        for p in self.figure_model.panels:
            for f in p.figures:
                if obj != f:
                    f.replot()
        # for p in self.figure_model.panels:
        #     p.make_figures()

        # self.figure_model.reset_panel_gen()
        # self.figure_container.model_changed()

        # self.figure_model.refresh()
        # self._get_component_hook()

    # def get_component(self, ans, *args, **kw):
    #     # if plotter_options is None:
    #     # pom = IdeogramOptionsManager()
    #     #     plotter_options = pom.plotter_options
    #
    #     model = self.figure_model
    #     if not model:
    #         model = CompositeModel()
    #         # from pychron.processing.plotters.ideogram.ideogram_model import IdeogramModel
    #         #
    #         # model = IdeogramModel(plot_options=plotter_options,
    #         #                       titles=self.titles)
    #
    #     model.trait_set(plot_options=self.plotter_options_manager.plotter_options,
    #                     titles=self.titles,
    #                     analyses=ans)
    #
    #     iv = FigureContainer(model=model)
    #     component = iv.component
    #
    #     return model, component

# ============= EOF =============================================
