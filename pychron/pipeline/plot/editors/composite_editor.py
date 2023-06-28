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
from chaco.api import PlotLabel
from traits.api import Instance, on_trait_change

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.options.options_manager import CompositeOptionsManager
from pychron.pipeline.plot.editors.interpreted_age_editor import InterpretedAgeEditor
from pychron.pipeline.plot.models.composite_model import CompositeModel


class CompositeEditor(InterpretedAgeEditor):
    plotter_options_manager = Instance(CompositeOptionsManager, ())
    figure_model_klass = CompositeModel

    def _get_component_hook(self, model, *args, **kw):
        # comp = super(CompositeEditor, self)._component_factory()
        comp = self.figure_container.component
        if self.plotter_options.auto_generate_title:
            l = PlotLabel(
                component=comp,
                padding_top=50,
                overlay_position="inside top",
                font=self.plotter_options.title_font,
                text=self.plotter_options.generate_title(model.analyses, 0),
            )
            comp.overlays.append(l)

    @on_trait_change("figure_model:panels:figures:recalculate_event")
    def _handle_recalculate(self, obj, name, old, new):
        if obj.suppress_recalculate_event:
            return

        for p in self.figure_model.panels:
            for f in p.figures:
                if obj != f and f.graph:
                    f.suppress_recalculate_event = True
                    f.replot()
                    f.suppress_recalculate_event = False

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
