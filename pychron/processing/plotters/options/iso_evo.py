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
from traits.api import List
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.processing.fits.iso_evo_fit_selector import IsoFilterFit
from pychron.processing.plotters.options.figure_plotter_options import FigurePlotterOptions
from pychron.processing.plotters.options.option import AuxPlotOptions


class IsoFilterFitAuxPlot(AuxPlotOptions, IsoFilterFit):
    names = List(['Ar40', 'Ar39'])


class IsotopeEvolutionOptions(FigurePlotterOptions):
    plot_option_klass = IsoFilterFitAuxPlot
    # def get_aux_plots(self):
    # return [IsoFilterFit(name='Ar40', fit='linear')]


# ============= EOF =============================================



