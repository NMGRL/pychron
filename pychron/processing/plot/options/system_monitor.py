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

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.processing.plot.options.option import SystemMonitorPlotOptions
from pychron.processing.plot.options.series import SeriesOptions


class SystemMonitorOptions(SeriesOptions):
    plot_option_klass = SystemMonitorPlotOptions

    def _get_dump_attrs(self):
        attrs = super(SystemMonitorOptions, self)._get_dump_attrs()
        attrs += ('aux_plots',)

        return attrs

        # def load_aux_plots(self, ref):
        #     def f(kii):
        #         ff = self.plot_option_klass()
        #         ff.trait_set(use=False, fit='',
        #                      name=kii,
        #                      trait_change_notify=False)
        #
        #         return ff
        #
        #     keys = ref.isotope_keys
        #     keys.extend(['{}bs'.format(ki) for ki in keys])
        #     if 'Ar40' in keys:
        #         if 'Ar39' in keys:
        #             keys.append('Ar40/Ar39')
        #         if 'Ar36' in keys:
        #             keys.append('Ar40/Ar36')
        #
        #     keys.append('PC')
        #     #keys.append('Foo')
        #     #ap = [f(k) for k in keys]
        #
        #     aps = []
        #     for k in keys:
        #         pp = next((ni for ni in self.aux_plots
        #                    if ni.name == k), None)
        #         if pp is None:
        #             pp = f(k)
        #
        #         #pp.use=False
        #         aps.append(pp)
        #
        #     self.aux_plots = aps

# ============= EOF =============================================
