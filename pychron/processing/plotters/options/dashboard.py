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

#============= enthought library imports =======================

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.processing.plotters.options.option import SystemMonitorPlotOptions
from pychron.processing.plotters.options.series import SeriesOptions


class DashboardOptions(SeriesOptions):
    plot_option_klass = SystemMonitorPlotOptions

    def _get_dump_attrs(self):
        attrs = super(DashboardOptions, self)._get_dump_attrs()
        attrs += ('aux_plots',)

        return attrs

    def load_aux_plots(self, keys):
        def f(kii):
            ff = self.plot_option_klass()
            ff.trait_set(use=False, fit='',
                         name=kii,
                         trait_change_notify=False)

            return ff

        aps = []
        for k in keys:
            pp = next((ni for ni in self.aux_plots
                       if ni.name == k), None)
            if pp is None:
                pp = f(k)

            #pp.use=False
            aps.append(pp)

        self.aux_plots = aps

# ============= EOF =============================================
