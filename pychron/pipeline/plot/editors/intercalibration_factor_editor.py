# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from traits.api import Str

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.pipeline.plot.editors.interpolation_editor import InterpolationEditor
from pychron.pipeline.plot.models.icfactor_model import ICFactorModel


class IntercalibrationFactorEditor(InterpolationEditor):
    figure_model_klass = ICFactorModel
    references_name = Str
    basename = 'ICFactors'

    def _figure_model_factory(self):
        model = self.figure_model
        if model is None:
            model = self.figure_model_klass()
            self.figure_model = model

        model.trait_set(plot_options=self.plotter_options,
                        # analysis_groups=self.analysis_groups,
                        references_name=self.references_name,
                        analyses=self.items,
                        references=self.references)

        return model

# ============= EOF =============================================
