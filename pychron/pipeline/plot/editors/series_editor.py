# ===============================================================================
# Copyright 2013 Jake Ross
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
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.pipeline.plot.models.series_model import SeriesModel
from pychron.pipeline.plot.editors.figure_editor import FigureEditor


class SeriesEditor(FigureEditor):
    # plotter_options_manager = Instance(PlotterOptionsManager)
    # plotter_options_manager_klass = SeriesOptionsManager
    figure_model_klass = SeriesModel
    pickle_path = 'series'
    basename = 'Series'
    # model_klass = SeriesModel
    # auto_group = False

    # def _plotter_options_manager_default(self):
    # return self.plotter_options_manager_klass()

    def _update_analyses_hook(self):
        # po = self.plotter_options_manager.plotter_options
        po = self.plotter_options
        ref = self.analyses[0]
        po.load_aux_plots(ref)

        self._set_name()

        # def get_component(self, ans, plotter_options):
        # if plotter_options is None:
        #         pom = self.plotter_options_manager_klass()
        #         plotter_options = pom.plotter_options
        #
        #     model = self.model_klass(plot_options=plotter_options)
        #     model.analyses = ans
        #     iv = FigureContainer(model=model)
        #
        #     return model, iv.component

# ============= EOF =============================================
