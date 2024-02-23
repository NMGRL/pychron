# ===============================================================================
# Copyright 2019 ross
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
from uncertainties import nominal_value, std_dev, ufloat

from pychron.pipeline.plot.plotter.series import Series


class RatioSeries(Series):
    def build(self, plots, plot_dict=None, *args, **kwargs):
        graph = self.graph
        # plots = (pp for pp in plots if self._has_attr(pp.name))

        for i, po in enumerate(plots):
            ytitle, kw = self._get_plot_kw(po)

            p = graph.new_plot(**kw)

            if i == 0:
                self._add_info(p)

            p.value_range.tight_bounds = False
            self._setup_plot(i, p, po, ytitle)

    # private
    def _get_ys(self, po):
        ys, yserr = super(RatioSeries, self)._get_ys(po)
        uys = [ufloat(*d) / po.standard_ratio for d in zip(ys, yserr)]
        return [nominal_value(yi) for yi in uys], [std_dev(yi) for yi in uys]


# ============= EOF =============================================
