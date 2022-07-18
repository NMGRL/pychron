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
from pyface.timer.do_later import do_after
from traits.api import List, Event, Str, Button, Instance
from traitsui.api import View, UItem, Group, VSplit, ListEditor, TabularEditor, VGroup
from traitsui.tabular_adapter import TabularAdapter

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.formatting import floatfmt
from pychron.core.helpers.iterfuncs import groupby_key
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.envisage.tasks.base_editor import BaseTraitsEditor
from pychron.options.options_manager import OptionsController, SeriesOptionsManager
from pychron.options.views.views import view
from pychron.pipeline.plot.editors.figure_editor import FigureEditor
from pychron.pipeline.plot.models.series_model import SeriesModel
from pychron.pychron_constants import DELTA, ARGON_KEYS

TOOLTIP_MAP = {
    "label": "Label",
    "mean": "Weighted mean if data has errors otherwise average",
    "n": "Number of data points",
    "std": "Standard Deviation",
    "se": "Standard Error, aka Taylor error.  1/sqrt(sum(weights)). If data has no errors this column "
    "will be a replica of SD column",
    "sem": "Standard Error of the Mean.  SD/sqrt(n)",
    "mswd": "MSWD of the current fit type",
    "mean_mswd": "MSWD of a mean fit to the data",
    "min": "Minimum value of the data",
    "max": "Maximum value of the data",
    "dev": "Delta, aka difference between Min and Max",
}


class SeriesStatsTabularAdapter(TabularAdapter):
    columns = [
        ("Label", "label"),
        ("Mean", "mean"),
        ("N", "fn"),
        ("SD", "std"),
        ("SE", "se"),
        ("SEM", "sem"),
        ("Fit MSWD", "mswd"),
        ("Mean MSWD", "mean_mswd"),
        ("Min", "min"),
        ("Max", "max"),
        (DELTA, "dev"),
    ]

    def get_tooltip(self, obj, trait, row, column):
        name = self.column_map[column]
        return TOOLTIP_MAP.get(name, "")


class SeriesStatistics:
    def __init__(self, label, reg):
        self.label = label
        self._reg = reg

    def __getattr__(self, attr):
        if hasattr(self._reg, attr):
            v = getattr(self._reg, attr)
            if isinstance(v, float):
                v = floatfmt(v)
            return v


class SeriesEditor(FigureEditor):
    figure_model_klass = SeriesModel
    pickle_path = "series"
    basename = "Series"
    statistics = List
    update_needed = Event

    def _get_component_hook(self, model=None):
        if model is None:
            model = self.figure_model

        ss = []
        for p in model.panels:
            g = p.figures[0].graph
            if g:
                if self.plotter_options.show_statistics_as_table:
                    g.on_trait_change(self._handle_reg, "regression_results")
                    for plot in reversed(g.plots):
                        for k, v in plot.plots.items():
                            if k.startswith("fit") and hasattr(v[0], "regressor"):
                                label = plot.y_axis.title
                                for tag in ("sub", "sup"):
                                    label = label.replace("<{}>".format(tag), "")
                                    label = label.replace("</{}>".format(tag), "")

                                ss.append(SeriesStatistics(label, v[0].regressor))

                else:
                    g.on_trait_change(
                        self._handle_reg, "regression_results", remove=True
                    )

        do_after(1, self.trait_set, statistics=ss)

    def _handle_reg(self, new):
        self.update_needed = True

    def get_table_view(self):
        return Group(
            UItem(
                "statistics",
                height=100,
                editor=TabularEditor(
                    adapter=SeriesStatsTabularAdapter(), update="update_needed"
                ),
            ),
            visible_when="object.plotter_options.show_statistics_as_table",
            label="Stats.",
        )

    def traits_view(self):

        v = View(
            VSplit(self.get_component_view(), self.get_table_view()), resizable=True
        )
        return v


class AnalysisTypeSeriesEditor(SeriesEditor):
    analysis_type = Str
    configure_plotter_options_button = Button
    options_manager = Instance(SeriesOptionsManager)

    def __init__(self, *args, **kw):
        super(AnalysisTypeSeriesEditor, self).__init__(*args, **kw)
        self.plotter_options = self.options_manager.selected_options

    def _options_manager_default(self):
        opt = SeriesOptionsManager(id="{}_series".format(self.analysis_type))
        opt.set_names_via_keys(
            ARGON_KEYS,
            additional_names=[
                "F",
            ],
        )
        return opt

    def _configure_plotter_options_button_fired(self):
        info = OptionsController(model=self.options_manager).edit_traits(
            view=view("Timeseries Options"), kind="livemodal"
        )
        if info.result:
            self.plotter_options = self.options_manager.selected_options
            self.refresh_needed = True

    def traits_view(self):
        return View(
            VGroup(
                icon_button_editor("configure_plotter_options_button", "cog"),
                VSplit(self.get_component_view(), self.get_table_view()),
            ),
            resizable=True,
        )


class AnalysisGroupedSeriesEditor(BaseTraitsEditor):
    editors = List

    def init(self, atypes):
        eds = [AnalysisTypeSeriesEditor(analysis_type=atype) for atype in atypes]
        self.editors = eds

    def refresh(self):
        for ei in self.editors:
            ei.refresh_needed = True

    # def set_options(self, options):
    #     for ei in self.editors:
    #         ei.plotter_options = options

    def set_items(self, items, *args, **kw):
        for atype, ans in groupby_key(items, "analysis_type"):
            for ei in self.editors:
                if ei.analysis_type == atype:
                    ei.set_items(list(ans))
                    break

    def traits_view(self):
        return View(
            UItem(
                "editors",
                style="custom",
                editor=ListEditor(use_notebook=True, page_name=".analysis_type"),
            )
        )


# ============= EOF =============================================
