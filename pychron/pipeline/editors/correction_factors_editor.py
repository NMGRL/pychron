# ===============================================================================
# Copyright 2018 ross
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
from chaco.array_data_source import ArrayDataSource
from numpy import array, arange
from traits.api import HasTraits, Int, Str, Float, List, Instance, Property
from traitsui.api import View, UItem, TabularEditor, VSplit
from traitsui.tabular_adapter import TabularAdapter
from uncertainties import nominal_value, std_dev

from pychron.core.helpers.formatting import floatfmt
from pychron.core.stats import calculate_weighted_mean, calculate_mswd
from pychron.envisage.tasks.base_editor import BaseTraitsEditor
from pychron.graph.error_bar_overlay import ErrorBarOverlay
from pychron.graph.stacked_regression_graph import StackedRegressionGraph
from pychron.pychron_constants import PLUSMINUS_ONE_SIGMA


class Result(HasTraits):
    value = Float
    error = Float
    name = Str
    wm_value = Float
    wm_error = Float
    mswd = Float

    def __init__(self, ratios, name, *args, **kw):
        super(Result, self).__init__(*args, **kw)
        vs = array([nominal_value(ri) for ri in ratios])
        es = array([std_dev(ri) for ri in ratios])

        self.name = name
        m = ratios.mean()
        self.value = nominal_value(m)
        self.error = std_dev(m)
        wm, we = calculate_weighted_mean(vs, es)
        self.wm_value = wm
        self.wm_error = we
        self.mswd = calculate_mswd(vs, es, wm=wm)


class ResultsAdapter(TabularAdapter):
    columns = [
        ("Name", "name"),
        ("Mean", "value"),
        (PLUSMINUS_ONE_SIGMA, "error"),
        ("Wt. Mean", "wm_value"),
        (PLUSMINUS_ONE_SIGMA, "wm_error"),
        ("MSWD", "mswd"),
    ]

    name_width = Int(100)
    value_width = Int(125)
    error_width = Int(125)
    wm_value_width = Int(125)
    wm_error_width = Int(125)

    value_text = Property
    error_text = Property
    wm_value_text = Property
    wm_error_text = Property
    mswd_text = Property

    def _get_value_text(self):
        return floatfmt(self.item.value, n=7)

    def _get_error_text(self):
        return floatfmt(self.item.error, n=7)

    def _get_wm_value_text(self):
        return floatfmt(self.item.wm_value, n=7)

    def _get_wm_error_text(self):
        return floatfmt(self.item.wm_error, n=7)

    def _get_mswd_text(self):
        return floatfmt(self.item.mswd, n=4)


class BaseCorrectionFactorsEditor(BaseTraitsEditor):
    analyses = List
    results = List
    graph = Instance(StackedRegressionGraph, ())

    def initialize(self):
        self.calculate()

    def calculate(self):
        raise NotImplementedError

    def _pre_calculate(self):
        for a in self.analyses:
            a.calculate_no_interference()

    def _calculate(self, dkey, atmo_ratio, ratios, atmo_correction_key):
        self._pre_calculate()

        results = []
        n = len(self.analyses)

        dv = array([a.isotopes[dkey].decay_corrected for a in self.analyses])

        for i, (nkey, tag) in enumerate(ratios):
            nv = array([a.get_ic_corrected_value(nkey) for a in self.analyses])
            if nkey == atmo_correction_key:
                nv -= array(
                    [a.get_ic_corrected_value(nkey) * atmo_ratio for a in self.analyses]
                )
            rs = nv / dv

            results.append(Result(array(rs), tag))
            self._plot(rs, tag, n, i)

        self.graph.refresh()
        self.results = results[::-1]

    def _plot(self, rs, tag, n, plotid):
        plot = self.graph.new_plot(padding_left=100)
        plot.y_axis.title = tag

        xs = arange(n)
        ys = array([nominal_value(ri) for ri in rs])
        yes = array([std_dev(ri) for ri in rs])

        p, s, l = self.graph.new_series(
            xs, ys, yerror=yes, fit="weighted mean", type="scatter"
        )

        ebo = ErrorBarOverlay(
            component=s, orientation="y", nsigma=2, visible=True, use_end_caps=True
        )

        s.underlays.append(ebo)
        s.yerror = ArrayDataSource(yes)

        self.graph.set_x_limits(pad="0.1", plotid=plotid)

        ymin, ymax = min(ys - 2 * yes), max(ys + 2 * yes)
        self.graph.set_y_limits(min_=ymin, max_=ymax, pad="0.1", plotid=plotid)

    def traits_view(self):
        v = View(
            VSplit(
                UItem(
                    "results",
                    height=100,
                    editor=TabularEditor(editable=False, adapter=ResultsAdapter()),
                ),
                UItem("graph", style="custom"),
            )
        )
        return v


class KCorrectionFactorsEditor(BaseCorrectionFactorsEditor):
    def calculate(self):
        dkey = "Ar39"
        ratios = (
            ("Ar37", "(37/39)K"),
            ("Ar38", "(38/39)K"),
            ("Ar40", "(40/39)K"),
        )
        atmo_ratio = self.analyses[0].arar_constants.atm4036
        atmo_correction_key = "Ar40"

        self._calculate(dkey, atmo_ratio, ratios, atmo_correction_key)


class CaCorrectionFactorsEditor(BaseCorrectionFactorsEditor):
    def calculate(self):
        dkey = "Ar37"
        ratios = (
            ("Ar36", "(36/37)Ca"),
            ("Ar38", "(38/37)Ca"),
            ("Ar39", "(39/37)Ca"),
        )

        atmo_ratio = self.analyses[0].arar_constants.atm3836
        atmo_correction_key = "Ar38"

        self._calculate(dkey, atmo_ratio, ratios, atmo_correction_key)


# ============= EOF =============================================
