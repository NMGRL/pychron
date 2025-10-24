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
from chaco.abstract_overlay import AbstractOverlay
from chaco.label import Label
from pyface.timer.do_later import do_later
from traits.api import Instance, List, Property, on_trait_change
from traitsui.api import View, VSplit, VGroup, HSplit
from traitsui.group import HGroup

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.traitsui_shortcuts import listeditor
from pychron.pipeline.plot.editors.ideogram_results_table import IdeogramResultsTable
from pychron.pipeline.plot.editors.interpreted_age_editor import InterpretedAgeEditor
from pychron.pipeline.plot.editors.rvalues_table import RValuesTable
from pychron.pipeline.plot.editors.ttest_table import TTestTable
from pychron.pipeline.plot.models.ideogram_model import IdeogramModel
from pychron.processing.analyses.file_analysis import InterpretedAgeAnalysis


class Caption(AbstractOverlay):
    label = Instance(Label, ())

    def __init__(self, text, *args, **kw):
        super(Caption, self).__init__(*args, **kw)
        self.label.text = text

    def _draw_component(self, gc, view_bounds=None, mode="normal"):
        print("casdcasd")

    def _draw_overlay(self, gc, view_bounds=None, mode="normal"):
        print("asdfasdfasdf")

    def _draw_underlay(self, gc, view_bounds=None, mode="normal"):
        print("unasdf")

    def draw(self, gc, view_bounds=None, mode="default"):
        print("dafasfasfd")
        with gc:
            self.label.draw()


class IdeogramEditor(InterpretedAgeEditor):
    figure_model_klass = IdeogramModel
    basename = "ideo"
    results_tables = List
    ttest_tables = List
    rvalues_tables = List

    additional_visible = Property

    def _get_additional_visible(self):
        return self.ttest_tables or self.results_tables or self.rvalues_tables

    @on_trait_change("figure_model:panels:figures:recalculate_event")
    def _handle_recalculate(self):
        self._get_component_hook()

    def _get_component_hook(self, model=None):
        if model is None:
            model = self.figure_model

        rs = []
        ts = []
        rvs = []

        for p in model.panels:
            ags = []
            for pp in p.figures:
                ag = pp.analysis_group
                group = pp.options.get_group(pp.group_id)
                color = group.color
                ag.color = color
                ags.append(ag)

            if self.plotter_options.show_results_table:
                r = IdeogramResultsTable(ags, self.plotter_options.nsigma)
                rs.append(r)

            if self.plotter_options.show_ttest_table and len(ags) > 1:
                t = TTestTable(ags)
                ts.append(t)

            if self.plotter_options.show_rvalues and len(ags) > 1:
                t = RValuesTable(ags)
                rvs.append(t)

        do_later(self.trait_set, results_tables=rs, ttest_tables=ts, rvalues_tables=rvs)

    def plot_interpreted_ages(self, iages):
        def construct(a):
            i = InterpretedAgeAnalysis(
                record_id="{} ({})".format(a.sample, a.identifier),
                sample=a.sample,
                age=a.age,
                age_err=a.age_err,
            )
            return i

        self.disable_aux_plots()

        ans = [construct(ia) for ia in iages]
        self.items = ans
        self._update_analyses()
        self.dump_tool()

    def disable_aux_plots(self):
        po = self.plotter_options_manager.plotter_options
        for ap in po.aux_plots:
            if ap.name.lower() not in (
                "ideogram",
                "analysis number",
                "analysis number nonsorted",
            ):
                ap.use = False
                ap.enabled = False

    def traits_view(self):
        tbl_grp = VGroup(
            listeditor(
                "results_tables",
                # height=0.2
            ),
            scrollable=True,
            visible_when="results_tables",
        )

        ttest_grp = VGroup(
            listeditor(
                "ttest_tables",
                # height=0.2
            ),
            scrollable=True,
            visible_when="ttest_tables",
        )

        rvalues_grp = VGroup(
            listeditor(
                "rvalues_tables",
                # height=0.2
            ),
            scrollable=True,
            visible_when="rvalues_tables",
        )

        g = self.get_component_view()
        # g.height = 0.75
        # v = View(g,
        #          resizable=True)
        v = View(
            VSplit(
                g,
                HGroup(
                    tbl_grp, ttest_grp, rvalues_grp, visible_when="additional_visible"
                ),
            ),
            resizable=True,
        )
        return v


# ============= EOF =============================================
