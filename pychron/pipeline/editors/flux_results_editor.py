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
from operator import attrgetter
import csv

# ============= enthought library imports =======================
from numpy import average, array, diff, arctan, Inf
from scipy.stats import mode
from traits.api import (
    HasTraits,
    Str,
    Int,
    Bool,
    Float,
    Property,
    List,
    Event,
    Button,
    on_trait_change,
)
from traitsui.api import (
    View,
    UItem,
    TableEditor,
    VGroup,
    HGroup,
    Item,
    spring,
    Tabbed,
    Readonly,
    EnumEditor,
)
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn
from uncertainties import nominal_value, std_dev

from pychron.core.helpers.filetools import add_extension
from pychron.core.helpers.formatting import calc_percent_error, floatfmt
from pychron.core.helpers.iterfuncs import groupby_key
from pychron.core.pychron_traits import BorderVGroup, BorderHGroup
from pychron.core.stats import validate_mswd
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.paths import paths
from pychron.pipeline.editors.flux_visualization_editor import (
    BaseFluxVisualizationEditor,
    HEADER_KEYS,
)
from pychron.pipeline.plot.plotter.arar_figure import SelectionFigure
from pychron.processing.flux import mean_j
from pychron.pychron_constants import LEAST_SQUARES_1D, WEIGHTED_MEAN_1D
from pychron.pychron_constants import PLUSMINUS_ONE_SIGMA


def column(klass=ObjectColumn, editable=False, **kw):
    return klass(text_font="arial 10", editable=editable, **kw)


def sciformat(x):
    return "{:0.6E}".format(x) if x else ""


def ff(x):
    return floatfmt(x, n=2) if x else ""


MONITOR_COLUMNS = [
    column(klass=CheckboxColumn, name="use", label="Use", editable=True, width=30),
    column(klass=CheckboxColumn, name="save", label="Save", editable=True, width=30),
    column(
        klass=CheckboxColumn,
        name="save_predicted",
        label="Save Pred.",
        editable=True,
        width=60,
    ),
    column(name="hole_id", label="Hole"),
    column(name="identifier", label="Identifier"),
    column(name="sample", label="Sample", width=115),
    column(name="n", label="N"),
    column(name="saved_j", label="Saved J", format_func=sciformat),
    column(name="saved_jerr", label=PLUSMINUS_ONE_SIGMA, format_func=sciformat),
    column(name="percent_saved_error", label="%", format_func=ff),
    column(name="mean_j", label="Mean J", format_func=sciformat),
    column(name="mean_jerr", label=PLUSMINUS_ONE_SIGMA, format_func=sciformat),
    column(name="percent_mean_error", label="%", format_func=ff),
    column(name="mean_j_mswd", label="MSWD", format_func=ff),
    column(name="j", label="Pred. J", format_func=sciformat, width=75),
    column(name="jerr", format_func=sciformat, label=PLUSMINUS_ONE_SIGMA, width=75),
    column(name="percent_pred_error", label="%", format_func=ff),
    column(name="dev", label="dev", format="%0.2f", width=70),
    column(name="position_jerr", format_func=sciformat, label="Position Err."),
    column(name="percent_position_jerr", label="%", format_func=ff),
]

MONITOR_EDITOR = TableEditor(
    columns=MONITOR_COLUMNS,
    selected="selected_monitors",
    selection_mode="rows",
    sortable=False,
    reorderable=False,
)


class FluxPosition(HasTraits):
    hole_id = Int
    identifier = Str
    sample = Str
    x = Float
    y = Float
    z = Float
    r = Float
    theta = Float
    saved_j = Float
    saved_jerr = Float

    mean_j = Float
    mean_jerr = Float
    mean_j_mswd = Float
    mean_j_valid_mswd = Bool

    min_j = Float
    max_j = Float
    variation_percent_j = Float

    model_kind = Str

    n = Int

    j = Float(enter_set=True, auto_set=False)
    jerr = Float(enter_set=True, auto_set=False)
    position_jerr = Float

    use = Bool(True)
    save = Bool(True)
    save_predicted = Bool(True)
    dev = Float
    mean_dev = Float

    percent_saved_error = Property
    percent_mean_error = Property
    percent_pred_error = Property
    percent_position_jerr = Property

    analyses = List
    error_kind = Str
    monitor_age = Float
    lambda_k = Float
    was_altered = Bool

    bracket_a = Int
    bracket_b = Int
    available_positions = List

    def set_mean_j(self, use_weights):

        ans = [a for a in self.analyses if not a.is_omitted()]
        if ans:
            j, mswd = mean_j(
                ans, use_weights, self.error_kind, self.monitor_age, self.lambda_k
            )
            self.mean_j = nominal_value(j)
            self.mean_jerr = std_dev(j)
            self.mean_j_mswd = mswd
            self.mean_j_valid_mswd = validate_mswd(mswd, len(ans))

        self.n = len(ans)

    def _get_percent_saved_error(self):
        return calc_percent_error(self.saved_j, self.saved_jerr)

    def _get_percent_mean_error(self):
        if self.mean_jerr and self.mean_jerr:
            return calc_percent_error(self.mean_j, self.mean_jerr)

    def _get_percent_pred_error(self):
        if self.j and self.jerr:
            return calc_percent_error(self.j, self.jerr)

    def _get_percent_position_jerr(self):
        if self.j and self.position_jerr:
            return calc_percent_error(self.j, self.position_jerr)

    def _save_changed(self, new):
        self.save_predicted = new

    def _save_predicted_changed(self, new):
        if new:
            self.save = new

    def to_row(self, keys=None):
        if keys is None:
            keys = HEADER_KEYS
        return [str(getattr(self, attr)) for attr in keys]


class FluxResultsEditor(BaseFluxVisualizationEditor, SelectionFigure):
    selected_monitors = List
    selected_unknowns = List
    toggle_use_button = Button("Toggle Use")
    toggle_save_button = Button("Toggle Save")
    toggle_save_unknowns_button = Button("Toggle Save")
    save_monitor_flux_csv_button = Button("Monitor Fluxes CSV")
    recalculate_button = Button("Calculate")
    suppress_metadata_change = Bool(False)
    _analyses = List

    @property
    def analyses(self):
        return self._analyses[0] if self._analyses else []

    def set_items(self, analyses):
        pass
        # if self.geometry:
        #     self.set_positions(analyses)
        #     self.predict_values()

    def set_positions(self, monitors, unk=None):
        self.debug(
            "setting positions mons={}, unks={}".format(
                len(monitors), len(unk) if unk else 0
            )
        )
        opt = self.plotter_options
        monage = opt.monitor_age * 1e6
        lk = nominal_value(opt.lambda_k)
        ek = opt.error_kind

        geom = self.geometry
        poss = []
        ans = []
        slope = True
        prev = None

        # calculate padding of the individuals analyses
        # by taking mean of the diffs between adjacent positions divided by 4
        if opt.model_kind in (LEAST_SQUARES_1D, WEIGHTED_MEAN_1D):
            idx = 0 if self.plotter_options.one_d_axis == "X" else 1
            vs = array([p[idx] for p in geom])
            vs = abs(diff(vs))
            vs = vs[vs.astype(bool)].mean()
        else:
            vs = [p[1] / p[0] if p[0] else Inf for p in geom]
            vs = arctan(vs)

            vs = abs(diff(vs))
            vs = mode(vs[vs.astype(bool)], axis=None)[0][0]

        padding = vs / 4.0

        for identifier, ais in groupby_key(monitors, "identifier"):

            ais = list(ais)
            n = len(ais)

            ref = ais[0]
            j = ref.j
            ip = ref.irradiation_position
            sample = ref.sample

            x, y, r, idx = geom[ip - 1]

            p = FluxPosition(
                identifier=identifier,
                irradiation=self.irradiation,
                level=self.level,
                sample=sample,
                hole_id=ip,
                saved_j=nominal_value(j),
                saved_jerr=std_dev(j),
                error_kind=ek,
                monitor_age=monage,
                analyses=ais,
                lambda_k=lk,
                x=x,
                y=y,
                r=r,
                n=n,
            )

            p.set_mean_j(self.plotter_options.use_weighted_fit)
            poss.append(p)
            if prev:
                slope = prev < p.j
            prev = p.j
            vs = self._sort_individuals(p, monage, lk, slope, padding)
            if ans:
                ans = [list(ans[i]) + list(v) for i, v in enumerate(vs)]
                # ans = [ans[0].extend(aa), ans[0].extend(xx), ans[0].extend(yy), ans[0].extend(es)]
            else:
                ans = list(vs)

        self._analyses = ans
        self.monitor_positions = sorted(poss, key=attrgetter("hole_id"))

        if unk is not None:
            ps = [p.hole_id for p in self.monitor_positions]
            for ui in unk:
                ui.available_positions = ps
            self.unknown_positions = sorted(unk, key=attrgetter("hole_id"))

    def _update_graph_metadata(self, obj, name, old, new):
        if not self.suppress_metadata_change:
            self._filter_metadata_changes(obj, self.analyses, self._recalculate_means)

    def _recalculate_means(self, sel, ans=None):
        if ans is None:
            ans = self.analyses

        if sel:
            idx = {ans[si].identifier for si in sel}
        else:
            idx = [None]

        for identifier in idx:
            # self.debug('sel:{} idx:{}'.format(sel, idx))
            for p in self.monitor_positions:
                if p.identifier == identifier:
                    # self.debug('recalculate position {} {}, {}'.format(sel, p.hole_id, p.identifier))
                    p.set_mean_j(self.plotter_options.use_weighted_fit)
                    p.was_altered = True
                elif p.was_altered:
                    # self.debug('was altered recalculate position {} {}, {}'.format(sel, p.hole_id, p.identifier))
                    p.set_mean_j(self.plotter_options.use_weighted_fit)
                    p.was_altered = False

        self.predict_values(refresh=True)

    def _save_monitor_flux_csv(self, p=None):
        if p is None:
            p = self.save_file_dialog(
                default_filename="{}{}_MonitorFluxes.csv".format(
                    self.irradiation, self.level
                ),
                default_directory=paths.data_dir,
            )

        if p:
            p = add_extension(p, ".csv")
            attrs = [
                "hole_id",
                "identifier",
                "sample",
                "n",
                "saved_j",
                "saved_jerr",
                "percent_saved_error",
                "mean_j",
                "mean_jerr",
                "percent_mean_error",
                "mean_j_mswd",
                "j",
                "jerr",
                "percent_pred_error",
                "dev",
                "position_jerr",
                "percent_position_jerr",
                "x",
                "y",
            ]

            with open(p, "w") as wfile:
                w = csv.writer(wfile, delimiter=",")
                w.writerow(attrs)
                rows = [
                    [str(getattr(p, a)) for a in attrs] for p in self.monitor_positions
                ]
                w.writerows(rows)
                w.writerow([])
                rows = [
                    [str(getattr(p, a)) for a in attrs] for p in self.unknown_positions
                ]
                w.writerows(rows)

            self.information_dialog("Fluxes saved to\n\n{}".format(p))

    # handlers
    def _recalculate_button_fired(self):
        self.predict_values()

    def _toggle_use_button_fired(self):
        self._suppress_predict = True
        for p in self.selected_monitors:
            p.use = not p.use

        self._suppress_predict = False
        self.predict_values()

    def _toggle_save_unknowns_button_fired(self):
        for p in self.selected_unknowns:
            p.save = not p.save

    def _toggle_save_button_fired(self):
        for p in self.selected_monitors:
            p.save = not p.save

    def _save_monitor_flux_csv_button_fired(self):
        self._save_monitor_flux_csv()

    def traits_view(self):
        unk_cols = [
            column(
                klass=CheckboxColumn, name="save", label="Save", editable=True, width=30
            ),
            column(name="hole_id", label="Hole"),
            column(name="identifier", label="Identifier"),
            column(name="sample", label="Sample", width=115),
            column(name="model_kind", label="Model"),
            column(name="saved_j", label="Saved J", format_func=sciformat),
            column(name="saved_jerr", label=PLUSMINUS_ONE_SIGMA, format_func=sciformat),
            column(name="percent_saved_error", label="%", format_func=ff),
            column(name="j", label="Pred. J", format_func=sciformat, width=75),
            column(
                name="jerr", format_func=sciformat, label=PLUSMINUS_ONE_SIGMA, width=75
            ),
            column(name="percent_pred_error", label="%", format_func=ff),
            column(name="dev", label="dev", format="%0.2f", width=70),
        ]

        unk_editor = TableEditor(
            columns=unk_cols,
            sortable=False,
            selected="selected_unknowns",
            selection_mode="rows",
            reorderable=False,
        )

        pgrp = VGroup(
            HGroup(
                UItem("toggle_use_button"),
                UItem("toggle_save_button"),
                UItem("save_monitor_flux_csv_button"),
            ),
            BorderHGroup(
                UItem("monitor_positions", editor=MONITOR_EDITOR), label="Monitors"
            ),
            BorderVGroup(
                UItem("toggle_save_unknowns_button"),
                UItem("unknown_positions", editor=unk_editor),
                label="Unknowns",
            ),
            label="Tables",
        )

        ggrp = UItem("graph", style="custom")
        tgrp = HGroup(
            UItem("recalculate_button"),
            Item("min_j", format_str="%0.4e", style="readonly", label="Min. J"),
            Item("max_j", style="readonly", format_str="%0.4e", label="Max. J"),
            Item(
                "percent_j_change",
                style="readonly",
                format_func=floatfmt,
                label="Delta J(%)",
            ),
            Readonly("holder", label="Tray"),
            # Item('j_gradient',
            #      style='readonly',
            #      format_func=floatfmt,
            #      label='Gradient J(%/cm)'),
            # spring, icon_button_editor('save_unknowns_button', 'dialog-ok-5',
            #                            tooltip='Toggle "save" for unknown positions'),
            # icon_button_editor('save_all_button', 'dialog-ok-apply-5',
            #                    tooltip='Toggle "save" for all positions')
        )

        v = View(VGroup(tgrp, Tabbed(ggrp, pgrp)))
        return v


class BracketingFluxResultsEditor(FluxResultsEditor):
    @on_trait_change("unknown_positions:[bracket_a, bracket_b]")
    def handle_bracket(self, obj, name, old, new):
        if obj.bracket_a and obj.bracket_b:
            a, b = [
                p
                for p in self.monitor_positions
                if p.hole_id in (obj.bracket_a, obj.bracket_b)
            ]

            ws = array([1 / a.mean_jerr**2, 1 / b.mean_jerr**2])
            vs = array([a.mean_j, b.mean_j])
            if self.plotter_options.use_weighted_fit:

                j = average(vs, weights=ws)
                je = sum(ws)

            else:
                j, je = vs.mean(), vs.std()

            oj = obj.saved_j
            obj.j = j
            obj.jerr = je
            obj.dev = (oj - j) / j * 100

    def traits_view(self):
        unk_cols = [
            column(
                klass=CheckboxColumn, name="save", label="Save", editable=True, width=30
            ),
            column(name="hole_id", label="Hole"),
            column(name="identifier", label="Identifier"),
            column(name="sample", label="Sample", width=115),
            column(
                name="bracket_a",
                editable=True,
                label="Bracket A",
                editor=EnumEditor(name="available_positions"),
            ),
            column(
                name="bracket_b",
                editable=True,
                label="Bracket B",
                editor=EnumEditor(name="available_positions"),
            ),
            column(name="saved_j", label="Saved J", format_func=sciformat),
            column(name="saved_jerr", label=PLUSMINUS_ONE_SIGMA, format_func=sciformat),
            column(name="percent_saved_error", label="%", format_func=ff),
            column(name="j", label="Pred. J", format_func=sciformat, width=75),
            column(
                name="jerr", format_func=sciformat, label=PLUSMINUS_ONE_SIGMA, width=75
            ),
            column(name="percent_pred_error", label="%", format_func=ff),
            column(name="dev", label="dev", format="%0.2f", width=70),
        ]

        unk_editor = TableEditor(columns=unk_cols, sortable=False, reorderable=False)

        pgrp = VGroup(
            HGroup(
                UItem("monitor_positions", editor=MONITOR_EDITOR),
                show_border=True,
                label="Monitors",
            ),
            HGroup(
                UItem("unknown_positions", editor=unk_editor),
                show_border=True,
                label="Unknowns",
            ),
            label="Tables",
        )

        tgrp = HGroup(
            UItem("recalculate_button"),
            Item("min_j", format_str="%0.4e", style="readonly", label="Min. J"),
            Item("max_j", style="readonly", format_str="%0.4e", label="Max. J"),
            Item(
                "percent_j_change",
                style="readonly",
                format_func=floatfmt,
                label="Delta J(%)",
            ),
            Readonly("holder", label="Tray"),
            # Item('j_gradient',
            #      style='readonly',
            #      format_func=floatfmt,
            #      label='Gradient J(%/cm)'),
            # spring, icon_button_editor('save_unknowns_button', 'dialog-ok-5',
            #                            tooltip='Toggle "save" for unknown positions'),
            # icon_button_editor('save_all_button', 'dialog-ok-apply-5',
            #                    tooltip='Toggle "save" for all positions')
        )

        ggrp = UItem("graph", style="custom")
        v = View(VGroup(tgrp, Tabbed(ggrp, pgrp)))
        return v


# ============= EOF =============================================
