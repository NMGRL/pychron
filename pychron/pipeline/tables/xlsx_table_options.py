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
import json
import os

from traits.api import Enum, Bool, Str, Int, Float, Color, List, Directory
from traitsui.api import VGroup, HGroup, Tabbed, Item, UItem, EnumEditor
from traitsui.item import UCustom, spring

from pychron.core.helpers.filetools import unique_path2, add_extension
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.persistence_options import BasePersistenceOptions
from pychron.core.pychron_traits import SingleStr, BorderHGroup, BorderVGroup
from pychron.core.ui.combobox_editor import ComboboxEditor
from pychron.core.yaml import yload
from pychron.options.options import BaseOptions
from pychron.paths import paths
from pychron.persistence_loggable import dumpable
from pychron.pychron_constants import SIGMA, AGE_SORT_KEYS


class XLSXAnalysisTableWriterOptions(BaseOptions):
    sig_figs = dumpable(Int(6))
    j_sig_figs = dumpable(Int(6))
    ic_sig_figs = dumpable(Int(6))
    disc_sig_figs = dumpable(Int(6))

    age_sig_figs = dumpable(Int(6))
    summary_age_sig_figs = dumpable(Int(6))

    kca_sig_figs = dumpable(Int(6))
    kcl_sig_figs = dumpable(Int(6))
    summary_kca_sig_figs = dumpable(Int(6))
    summary_kcl_sig_figs = dumpable(Int(6))

    radiogenic_yield_sig_figs = dumpable(Int(6))
    cumulative_ar39_sig_figs = dumpable(Int(6))

    signal_sig_figs = dumpable(Int(6))
    decay_sig_figs = dumpable(Int(6))
    correction_sig_figs = dumpable(Int(6))
    sens_sig_figs = dumpable(Int(2))
    k2o_sig_figs = dumpable(Int(3))

    use_standard_sigfigs = dumpable(Bool(True))
    ensure_trailing_zeros = dumpable(Bool(False))

    power_units = dumpable(Enum("W", "C", "%"))
    intensity_units = dumpable(Enum("fA", "cps", "Volts"))
    age_units = dumpable(Enum("Ma", "Ga", "ka", "a"))
    hide_gridlines = dumpable(Bool(False))

    include_meta_weight = dumpable(Bool(True))
    include_meta_location = dumpable(Bool(True))

    include_F = dumpable(Bool(True))
    include_radiogenic_yield = dumpable(Bool(True))
    include_production_ratios = dumpable(Bool(True))
    include_plateau_age = dumpable(Bool(True))
    include_integrated_age = dumpable(Bool(True))
    include_isochron_age = dumpable(Bool(True))
    include_trapped_ratio = dumpable(Bool(True))

    include_kca = dumpable(Bool(True))
    include_kcl = dumpable(Bool(True))
    invert_kca_kcl = dumpable(Bool(False))
    include_rundate = dumpable(Bool(True))
    include_time_delta = dumpable(Bool(True))
    include_k2o = dumpable(Bool(True))
    include_isochron_ratios = dumpable(Bool(False))
    include_sensitivity = dumpable(Bool(True))
    sensitivity_units = dumpable(Str("mol/fA"))

    include_blanks = dumpable(Bool(True))
    include_intercepts = dumpable(Bool(True))
    include_corrected_intensities = dumpable(Bool(True))
    include_percent_ar39 = dumpable(Bool(True))
    include_icfactors = dumpable(Bool(True))
    include_discrimination = dumpable(Bool(True))
    include_decay_factors = dumpable(Bool(True))
    include_j = dumpable(Bool(True))
    include_lambda_k = dumpable(Bool(True))
    include_monitor_age = dumpable(Bool(True))
    include_monitor_name = dumpable(Bool(True))
    include_monitor_material = dumpable(Bool(True))
    # use_weighted_kca = dumpable(Bool(True))
    # kca_error_kind = dumpable(Enum(*ERROR_TYPES))
    repeat_header = dumpable(Bool(False))
    highlight_non_plateau = dumpable(Bool(True))
    highlight_color = dumpable(Color)

    root_name = dumpable(Str)
    root_names = List
    root_directory = dumpable(Directory)
    name = dumpable(Str("Untitled"))
    auto_view = dumpable(Bool(False))

    unknown_note_name = dumpable(Str("Default"))
    available_unknown_note_names = List

    unknown_notes = dumpable(
        Str(
            """Errors quoted for individual analyses include analytical error only, without interfering reaction or J uncertainties.
Integrated age calculated by summing isotopic measurements of all steps.
Plateau age is inverse-variance-weighted mean of selected steps.
Plateau age error is inverse-variance-weighted mean error (Taylor, 1982) times root MSWD where MSWD>1.
Plateau error is weighted error of Taylor (1982).
Decay constants and isotopic abundances after {decay_ref:}
Ages calculated relative to FC-2 Fish Canyon Tuff sanidine interlaboratory standard at {monitor_age:} Ma"""
        )
    )

    unknown_corrected_note = dumpable(
        Str(
            """Corrected: Isotopic intensities corrected for blank, baseline, 
    radioactivity decay and detector intercalibration, not for interfering reactions."""
        )
    )
    unknown_intercept_note = dumpable(
        Str("""Intercepts: t-zero intercept corrected for detector baseline.""")
    )
    unknown_time_note = dumpable(
        Str(
            """Time interval (days) between end of irradiation and beginning of analysis."""
        )
    )

    unknown_x_note = dumpable(
        Str(
            """X symbol preceding sample ID denotes analyses 
    excluded from weighted-mean age calculations."""
        )
    )
    unknown_px_note = dumpable(
        Str(
            """pX symbol preceding sample ID denotes analyses
    excluded plateau age calculations."""
        )
    )

    unknown_title = dumpable(Str("Ar/Ar analytical data."))
    air_notes = dumpable(Str(""))
    air_title = dumpable(Str(""))
    blank_notes = dumpable(Str(""))
    blank_title = dumpable(Str(""))
    monitor_notes = dumpable(Str(""))
    monitor_title = dumpable(Str(""))
    summary_notes = dumpable(Str(""))
    summary_title = dumpable(Str(""))
    machine_title = dumpable(Str("Non-formatted Table"))

    include_summary_sheet = dumpable(Bool(True))
    include_summary_age = dumpable(Bool(True))
    include_summary_age_type = dumpable(Bool(True))
    include_summary_material = dumpable(Bool(True))
    include_summary_sample = dumpable(Bool(True))
    include_summary_j = dumpable(Bool(True))

    include_summary_aliquot = dumpable(Bool(False))
    include_summary_identifier = dumpable(Bool(True))
    include_summary_unit = dumpable(Bool(True))
    include_summary_location = dumpable(Bool(True))
    include_summary_irradiation = dumpable(Bool(True))
    include_summary_n = dumpable(Bool(True))
    include_summary_percent_ar39 = dumpable(Bool(True))
    include_summary_mswd = dumpable(Bool(True))
    include_summary_kca = dumpable(Bool(True))
    include_summary_comments = dumpable(Bool(True))
    include_summary_trapped = dumpable(Bool(True))

    summary_age_nsigma = dumpable(Enum(1, 2, 3))
    summary_kca_nsigma = dumpable(Enum(1, 2, 3))
    summary_trapped_ratio_nsigma = dumpable(Enum(1, 2, 3))
    summary_mswd_sig_figs = dumpable(Int(2))
    summary_percent_ar39_sig_figs = dumpable(Int(1))
    summary_trapped_ratio_sig_figs = dumpable(Int(4))

    # a for analysis. i.e analysis summary. This controls the summary of an individual group of analyses
    asummary_kca_nsigma = dumpable(Enum(1, 2, 3))
    asummary_age_nsigma = dumpable(Enum(1, 2, 3))
    asummary_trapped_ratio_nsigma = dumpable(Enum(1, 2, 3))
    asummary_age_sig_figs = dumpable(Int(3))
    asummary_mswd_sig_figs = dumpable(Int(3))
    asummary_kca_sig_figs = dumpable(Int(3))
    asummary_kcl_sig_figs = dumpable(Int(3))
    asummary_trapped_ratio_sig_figs = dumpable(Int(3))

    plateau_nsteps = dumpable(Int(3))
    plateau_gas_fraction = dumpable(Float(50))

    group_age_sorting = dumpable(Enum(*AGE_SORT_KEYS))
    subgroup_age_sorting = dumpable(Enum(*AGE_SORT_KEYS))
    individual_age_sorting = dumpable(Enum(*AGE_SORT_KEYS))

    status_enabled = dumpable(Bool(True))
    identifier_enabled = dumpable(Bool(True))
    tag_enabled = dumpable(Bool(True))
    analysis_label_enabled = dumpable(Bool(True))

    use_sample_metadata_saved_with_run = dumpable(Bool(True))
    _persistence_name = "xlsx_table_options"

    # include_j_error_in_individual_analyses = dumpable(Bool(False))
    # include_j_error_in_mean = dumpable(Bool(True))
    # _suppress = False

    include_decay_error = dumpable(Bool(False))

    human_sheet_name = dumpable(Str("Unknowns"))
    machine_sheet_name = dumpable(Str("Nonformatted"))
    summary_sheet_name = dumpable(Str("Summary"))

    exclude_hidden_columns = dumpable(Bool(False))
    include_notes_border = dumpable(Bool(True))

    overwrite = Bool(False)

    def __init__(self, *args, **kw):
        # self._persistence_name = name

        super(XLSXAnalysisTableWriterOptions, self).__init__(*args, **kw)
        # self.load_notes()
        # self._load_note_names()

        self._load_notes()
        self._unknown_note_name_changed(self.unknown_note_name)

    # def dump(self, wfile):
    #     state = self.make_state()
    #     json.dump(state, wfile, indent=4, sort_keys=True)
    def _get_state_hook(self, state):
        d = {k: getattr(self, k) for k in self.traits(dump=True).keys()}

        state.update(**d)

    def _load_notes(self):
        p = os.path.join(paths.user_pipeline_dir, "table_notes.yaml")
        if os.path.isfile(p):
            obj = yload(p)

            setattr(self, "summary_notes", obj.get("summary_notes", ""))

            for grpname in ("unknown",):
                grp = obj.get("{}_notes".format(grpname))
                if grp:
                    try:
                        setattr(
                            self,
                            "available_{}_note_names".format(grpname),
                            list(grp.keys()),
                        )
                    except AttributeError:
                        pass

    def _unknown_note_name_changed(self, new):
        grp = self._load_note("unknown_notes")
        if grp is not None:
            sgrp = grp.get(new)
            if sgrp:
                self.unknown_notes = sgrp.get("main", "")
                for k in ("corrected", "x", "px", "intercept", "time"):
                    v = sgrp.get(k)
                    if v is not None:
                        setattr(self, "unknown_{}_note".format(k), v)

    def _load_note(self, group):
        p = os.path.join(paths.user_pipeline_dir, "table_notes.yaml")
        if os.path.isfile(p):
            obj = yload(p)
            return obj.get(group)

    # @property
    # def age_scalar(self):
    #     return AGE_MA_SCALARS[self.age_units]

    @property
    def path(self):
        return self.get_path(check_exists=True)

    def get_path(self, check_exists=False):
        name = self.name
        root = paths.table_dir

        if self.root_directory:
            root = self.root_directory
        elif self.root_name:
            root = os.path.join(root, self.root_name)

        if not name or name == "Untitled":
            path, _ = unique_path2(root, "Untitled", extension=".xlsx")
        else:
            path = os.path.join(root, add_extension(name, ext=".xlsx"))
            if check_exists:
                if os.path.isfile(path) and not self.overwrite:
                    path, _ = unique_path2(root, name, extension=".xlsx")
        return path

    def traits_view(self):
        class VBorder(VGroup):
            show_border = True

        class UUItem(UCustom):
            height = -50

        unknown_grp = VGroup(
            Item("unknown_title", label="Table Title", springy=True),
            VBorder(
                VBorder(
                    UItem(
                        "unknown_note_name",
                        editor=EnumEditor(name="available_unknown_note_names"),
                    ),
                    UItem("unknown_notes", style="custom"),
                    label="Main",
                ),
                VBorder(UUItem("unknown_corrected_note"), label="Corrected"),
                VBorder(UUItem("unknown_intercept_note"), label="Intercept"),
                VBorder(UUItem("unknown_time_note"), label="Time"),
                VBorder(UUItem("unknown_x_note"), label="X"),
                VBorder(UUItem("unknown_px_note"), label="pX"),
                label="Notes",
            ),
            label="Unknowns Cont.",
        )
        sheet_grp = BorderVGroup(
            Item("human_sheet_name", label="Formatted"),
            Item("machine_sheet_name", label="Machine"),
            Item("summary_sheet_name", label="Summary"),
            label="Sheet Names",
        )
        behavior_grp = BorderVGroup(
            Item("exclude_hidden_columns"),
            Item("include_notes_border"),
            label="Behavior",
        )

        def note(name):
            tag = "{}s".format(name.capitalize())
            return VGroup(
                Item("{}_title".format(name), label="Table Title"),
                VBorder(UItem("{}_notes".format(name), style="custom"), label="Notes"),
                label=tag,
            )

        air_grp = note("air")
        blank_grp = note("blank")
        monitor_grp = note("monitor")

        grp = BorderVGroup(
            Item("name", label="Filename"),
            Item("root_directory"),
            Item(
                "root_name",
                editor=ComboboxEditor(name="root_names"),
                enabled_when="not root_directory",
            ),
            Item("auto_view", label="Open in Excel"),
            label="Save",
        )

        units_grp = BorderVGroup(
            HGroup(
                Item("power_units", label="Power Units"),
                Item("age_units", label="Age Units"),
            ),
            HGroup(
                Item("intensity_units", label="Intensity Units"),
                Item("sensitivity_units", label="Sensitivity Units"),
            ),
            label="Units",
        )

        def asummary(k, label, **kw):
            return Item("asummary_{}_nsigma".format(k), label=label, **kw)

        sigma_grp = BorderHGroup(
            asummary("kca", "K/Ca"),
            asummary("age", "Age"),
            asummary("trapped_ratio", "Trapped"),
            label="N. Sigma",
        )

        sort_grp = BorderVGroup(
            HGroup(
                Item("group_age_sorting", label="Group"),
                Item("subgroup_age_sorting", label="SubGroup"),
            ),
            Item("individual_age_sorting", label="Individual"),
            label="Sorting",
        )
        appearence_grp = BorderVGroup(
            HGroup(
                Item("hide_gridlines", label="Hide Gridlines"),
                Item("repeat_header", label="Repeat Header"),
            ),
            units_grp,
            sigma_grp,
            sort_grp,
            HGroup(
                Item("highlight_non_plateau"),
                UItem("highlight_color", enabled_when="highlight_non_plateau"),
            ),
            label="Appearance",
        )

        def sigfig(k):
            return "{}_sig_figs".format(k)

        def isigfig(k, label, **kw):
            return Item(sigfig(k), width=-40, label=label, **kw)

        sig_figs_grp = BorderVGroup(
            Item("use_standard_sigfigs"),
            VGroup(
                Item("sig_figs", label="Default"),
                HGroup(isigfig("age", "Age"), isigfig("asummary_age", "Summary Age")),
                HGroup(isigfig("kca", "K/Ca"), isigfig("asummary_kca", "Summary K/Ca")),
                HGroup(isigfig("kcl", "K/Cl"), isigfig("asummary_kcl", "Summary K/Cl")),
                HGroup(
                    isigfig("asummary_trapped_ratio", "Trapped 40/36"),
                    isigfig("asummary_mswd", "Summary MSWD"),
                ),
                HGroup(
                    isigfig("radiogenic_yield", "%40Ar*"),
                    isigfig("cumulative_ar39", "Cum. %39Ar"),
                ),
                HGroup(isigfig("signal", "Signal"), isigfig("j", "Flux")),
                HGroup(isigfig("ic", "IC"), isigfig("disc", "Disc.")),
                HGroup(
                    isigfig("decay", "Decay"),
                    isigfig("correction", "Correction Factors"),
                ),
                HGroup(isigfig("sens", "Sensitivity"), isigfig("k2o", "K2O")),
                enabled_when="not use_standard_sigfigs",
            ),
            label="Significant Figures",
        )

        def inc(k):
            return "include_{}".format(k)

        def iinc(k, label, **kw):
            return Item(inc(k), label=label, **kw)

        arar_col_grp = VGroup(
            iinc("F", "40Ar*/39ArK"),
            iinc("percent_ar39", "Cumulative %39Ar"),
            iinc("radiogenic_yield", "%40Ar*"),
            iinc("sensitivity", "Sensitivity"),
            iinc("k2o", "K2O wt. %"),
            iinc("production_ratios", "Production Ratios"),
            iinc("isochron_ratios", "Isochron Ratios"),
            iinc("time_delta", "Time since Irradiation"),
            iinc("kca", "K/Ca"),
            iinc("kcl", "K/Cl"),
            Item("invert_kca_kcl", label="Invert K/Ca,K/Cl"),
            VGroup(
                iinc("lambda_k", "Lambda K"),
                iinc("monitor_age", "Age"),
                iinc("monitor_name", "Name"),
                iinc("monitor_material", "Material"),
                label="Flux Monitor",
            ),
            label="Ar/Ar",
        )

        general_col_grp = VGroup(
            Item("status_enabled", label="Status"),
            Item("analysis_label_enabled", label="Analysis Label"),
            Item("identifier_enabled", label="Identifier"),
            Item("tag_enabled", label="Tag"),
            iinc("rundate", "Analysis RunDate"),
            iinc("blanks", "Applied Blank"),
            iinc("corrected_intensities", "Corrected Intensities"),
            iinc("intercepts", "Intercepts"),
            iinc("icfactors", "ICFactors"),
            iinc("discrimination", "Discrimination"),
            iinc("decay_factors", "Decay Factors"),
            iinc("j", "J"),
            Item(
                "use_sample_metadata_saved_with_run",
                label="Use Sample Metadata Saved with Run",
                tooltip="If checked use the sample metadata saved with the run at the time of "
                "analysis otherwise query the database to sync metadata",
            ),
            label="General",
        )

        summary_rows_grp = BorderVGroup(
            iinc("summary_kca", "Integrated K/Ca"),
            iinc("plateau_age", "Plateau Age"),
            iinc("integrated_age", "Total Integrated Age"),
            iinc("isochron_age", "Isochron Age"),
            iinc("trapped_ratio", "Trapped 40/36"),
            label="Summary Rows",
        )

        meta_grp = BorderVGroup(
            iinc("meta_weight", "Weight"),
            iinc("meta_location", "Location"),
            label="Meta Data",
        )

        columns_grp = BorderHGroup(general_col_grp, arar_col_grp, label="Columns")
        unk_columns_grp = VGroup(
            HGroup(columns_grp, sig_figs_grp),
            HGroup(summary_rows_grp, meta_grp),
            label="Unknowns",
        )
        g1 = VGroup(
            HGroup(grp, appearence_grp), HGroup(sheet_grp, behavior_grp), label="Main"
        )

        def isum(k):
            return inc("summary_{}".format(k))

        def iisum(k, label, **kw):
            return Item(isum(k), label=label, **kw)

        summary_columns = BorderVGroup(
            iisum("sample", "Sample"),
            iisum("identifier", "Identifier"),
            iisum("aliquot", "Aliquot"),
            iisum("unit", "Unit"),
            iisum("location", "Location"),
            iisum("material", "Material"),
            iisum("irradiation", "Irradiation"),
            iisum("j", "J"),
            iisum("age_type", "Age Type"),
            iisum("n", "N"),
            iisum("percent_ar39", "%39Ar"),
            iisum("mswd", "MSWD"),
            HGroup(iisum("kca", "KCA"), Item("summary_kca_nsigma", label=SIGMA)),
            HGroup(iisum("age", "Age"), Item("summary_age_nsigma", label=SIGMA)),
            iisum("comments", "Comments"),
            HGroup(
                iisum("trapped", "Trapped 40/36"),
                Item("summary_trapped_ratio_nsigma", label=SIGMA),
            ),
            enabled_when=isum("sheet"),
            label="Columns",
        )
        summary_sigfigs = BorderVGroup(
            Item("summary_mswd_sig_figs", label="MSWD"),
            Item("summary_percent_ar39_sig_figs", label="%39Ar"),
            Item("summary_age_sig_figs", label="Age"),
            Item("summary_kca_sig_figs", label="K/Ca"),
            # Item("summary_kcl_sig_figs", label="Age"),
            label="Sig Figs",
        )

        summary_grp = VGroup(
            HGroup(
                iisum("sheet", "Summary Sheet"),
                Item("summary_title", label="Table Title"),
            ),
            HGroup(summary_columns, summary_sigfigs),
            BorderVGroup(UItem("summary_notes", style="custom"), label="Notes"),
            label="Summary",
        )

        # calc_grp = VGroup(J_ERROR_GROUP,
        #                   Item('include_decay_error', label='Include Decay Error in Wt. Mean'),
        #                   label='Calc.')

        v = okcancel_view(
            Tabbed(
                g1,
                unk_columns_grp,
                unknown_grp,
                blank_grp,
                air_grp,
                monitor_grp,
                summary_grp,
            ),
            resizable=True,
            width=775,
            height=0.75,
            title="XLSX Analysis Table Options",
            scrollable=True,
        )
        return v


if __name__ == "__main__":
    # from pychron.paths import paths
    paths.build("~/PychronDev")
    e = XLSXAnalysisTableWriterOptions()
    e.configure_traits()
# ============= EOF =============================================
