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
from traits.api import Bool, Enum, String

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.processing.plotters.options.plotter import PlotterOptions


class AgeOptions(PlotterOptions):
    include_j_error = Bool(True)
    include_irradiation_error = Bool(True)
    include_decay_error = Bool(False)
    nsigma = Enum(1, 2, 3)
    show_info = Bool(True)
    show_mean_info=Bool(True)
    show_error_type_info=Bool(True)
    label_box = Bool(False)
    index_attr=None
    analysis_label_format = String
    analysis_label_display = String

    def _get_dump_attrs(self):
        attrs = super(AgeOptions, self)._get_dump_attrs()
        attrs += ['include_j_error',
                  'include_irradiation_error',
                  'include_decay_error',
                  'nsigma','label_box',
                  'show_info', 'show_mean_info', 'show_error_type_info',
                  'analysis_label_display',
                  'analysis_label_format']
        return attrs


#============= EOF =============================================
