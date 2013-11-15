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
from traits.api import Instance
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.processing.tasks.figures.figure_editor import FigureEditor
from pychron.processing.plotters.figure_container import FigureContainer
from pychron.processing.plotter_options_manager import SpectrumOptionsManager
#from pychron.processing.tasks.figures.editors.auto_controls import AutoSpectrumControl


class SpectrumEditor(FigureEditor):
    plotter_options_manager = Instance(SpectrumOptionsManager, ())
    basename = 'spec'

    def get_component(self, ans, plotter_options):
        if plotter_options is None:
            pom = SpectrumOptionsManager()
            plotter_options = pom.plotter_options

        from pychron.processing.plotters.spectrum.spectrum_model import SpectrumModel

        model = SpectrumModel(plot_options=plotter_options)
        model.analyses = ans
        iv = FigureContainer(model=model)
        #self._model = model
        return model, iv.component


#class AutoSpectrumEditor(SpectrumEditor):
#    auto_figure_control = Instance(AutoSpectrumControl, ())

#============= EOF =============================================
