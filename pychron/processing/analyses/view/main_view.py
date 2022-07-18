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
from traits.api import (
    HasTraits,
    Str,
    List,
    Event,
    Instance,
    Any,
    cached_property,
    Unicode,
    Property,
)
from traitsui.api import View, UItem, VGroup, HGroup, TabularEditor
from uncertainties import std_dev, nominal_value, ufloat

from pychron.core.helpers.formatting import floatfmt, format_percent_error
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.processing.analyses.view.adapters import (
    ComputedValueTabularAdapter,
    DetectorRatioTabularAdapter,
    ExtractionTabularAdapter,
    MeasurementTabularAdapter,
)
from pychron.processing.analyses.view.values import (
    ExtractionValue,
    ComputedValue,
    MeasurementValue,
    DetectorRatio,
)

# class MainViewHandler(Handler):
#     def show_isotope_evolution(self, uiinfo, obj):
#         isos = obj.selected
#         obj.show_iso_evo_needed = isos
from pychron.pychron_constants import (
    PLUSMINUS,
    COCKTAIL,
    BLANK_TYPES,
    UNKNOWN,
    AIR,
    AR_AR,
    DATE_FORMAT,
)


class MainView(HasTraits):
    name = "Main"

    summary_str = Unicode

    analysis_id = Str
    analysis_type = Str

    isotopes = List
    refresh_needed = Event

    computed_values = List
    corrected_values = List
    extraction_values = List
    measurement_values = List

    _corrected_enabled = True

    measurement_adapter = Instance(MeasurementTabularAdapter, ())
    extraction_adapter = Instance(ExtractionTabularAdapter, ())
    computed_adapter = Property(depends_on="analysis_type")

    selected = Any
    show_iso_evo_needed = Event
    recall_options = None
    experiment_type = AR_AR

    def __init__(self, analysis=None, *args, **kw):
        super(MainView, self).__init__(*args, **kw)
        if analysis:
            self._load(analysis)

    def set_options(self, an, options):
        self.recall_options = options
        self.load(an, True)

    def load(self, an, refresh=False):
        self.experiment_type = an.experiment_type
        self._load(an)
        if refresh:
            self.refresh_needed = True

    def _load(self, an):
        self.isotopes = [an.isotopes[k] for k in an.isotope_keys]
        self.load_computed(an)
        self.load_extraction(an)
        self.load_measurement(an, an)

    def _get_irradiation(self, an):
        return an.irradiation_label

        # def _get_j(self, an):
        # return ufloat(an.j, an.j_err)

    def load_measurement(self, an, ar):

        # j = self._get_j(an)
        j = ar.j
        jf = "NaN"
        if j is not None:
            jj = floatfmt(nominal_value(j), n=7, s=5)
            pe = format_percent_error(
                nominal_value(j), std_dev(j), include_percent_sign=True
            )
            jf = "{} \u00b1{:0.2e}({})".format(jj, std_dev(j), pe)

        a39 = ar.ar39decayfactor
        a37 = ar.ar37decayfactor
        ms = [
            MeasurementValue(name="Branch", value=an.branch),
            MeasurementValue(name="DAQ Version", value=an.collection_version),
            MeasurementValue(name="UUID", value=an.uuid),
            MeasurementValue(name="RepositoryID", value=an.repository_identifier),
            MeasurementValue(name="Spectrometer", value=an.mass_spectrometer),
            MeasurementValue(name="Run Date", value=an.rundate.strftime(DATE_FORMAT)),
            MeasurementValue(name="Irradiation", value=self._get_irradiation(an)),
            MeasurementValue(name="J", value=jf),
            MeasurementValue(name="J History", value=an.flux_history),
            MeasurementValue(
                name="Position Error",
                value=floatfmt(an.position_jerr, use_scientific=True),
            ),
            MeasurementValue(
                name="Lambda K",
                value=nominal_value(ar.arar_constants.lambda_k),
                units="1/a",
            ),
            MeasurementValue(name="Project", value=an.project),
            MeasurementValue(name="Sample", value=an.sample),
            MeasurementValue(name="Material", value=an.material),
            MeasurementValue(name="Comment", value=an.comment),
            MeasurementValue(name="Ar39Decay", value=floatfmt(a39)),
            MeasurementValue(name="Ar37Decay", value=floatfmt(a37)),
            MeasurementValue(name="K3739 Mode", value=an.display_k3739_mode),
            MeasurementValue(
                name="Sens.",
                value=floatfmt(an.sensitivity, use_scientific=True),
                units=an.sensitivity_units,
            ),
        ]

        self.measurement_values = ms

    def load_extraction(self, an):

        ev = [
            ExtractionValue(name="Extract Script", value=an.extraction_script_name),
            ExtractionValue(name="Meas. Script", value=an.measurement_script_name),
            ExtractionValue(name="Device", value=an.extract_device),
            ExtractionValue(name="Load", value=an.load_name, units=an.load_holder),
            ExtractionValue(name="Position", value=an.position),
            ExtractionValue(name="Weight", value=an.weight, units="mg"),
            ExtractionValue(
                name="XYZ", value=an.xyz_position, conditional_visible=True
            ),
            ExtractionValue(
                name="Extract Value",
                value=an.extract_value,
                units=an.extract_units,
            ),
            ExtractionValue(name="Duration", value=an.extract_duration, units="s"),
            ExtractionValue(name="Cleanup", value=an.cleanup_duration, units="s"),
            ExtractionValue(
                name="Pre Cleanup", value=an.pre_cleanup_duration, units="s"
            ),
            ExtractionValue(
                name="Post Cleanup", value=an.post_cleanup_duration, units="s"
            ),
            ExtractionValue(name="Cryo Temp.", value=an.cryo_temperature, units="K"),
            ExtractionValue(
                name="T_o", value=an.collection_time_zero_offset, units="s"
            ),
            ExtractionValue(name="Light", value=an.light_value, units="%"),
            ExtractionValue(name="Lab Temp.", value=an.lab_temperature, units="F"),
            ExtractionValue(name="Lab Hum.", units="%", value=an.lab_humidity),
        ]

        if "UV" in an.extract_device:
            extra = [
                ExtractionValue(
                    name="Mask Pos.", value=an.mask_position, units="steps"
                ),
                ExtractionValue(name="Mask Name", value=an.mask_name),
                ExtractionValue(name="Reprate", value=an.reprate, units="1/s"),
            ]
        else:
            extra = [
                ExtractionValue(name="Beam Diam.", value=an.beam_diameter, units="mm"),
                ExtractionValue(name="Pattern", value=an.pattern),
                ExtractionValue(name="Ramp Dur.", value=an.ramp_duration, units="s"),
                ExtractionValue(name="Ramp Rate", value=an.ramp_rate, units="1/s"),
            ]

        ev.extend(extra)

        ev = [ei for ei in ev if not (ei.conditional_visible and not ei.value)]

        self.extraction_values = ev

    def load_computed(self, an, new_list=True):
        if self.analysis_type == UNKNOWN:
            self._load_unknown_computed(an, new_list)
            if self._corrected_enabled:
                self._load_corrected_values(an, new_list)
        elif self.analysis_type == AIR or self.analysis_type in BLANK_TYPES:
            self._load_air_computed(an, new_list)
        elif self.analysis_type == COCKTAIL:
            self._load_cocktail_computed(an, new_list)
            if self._corrected_enabled:
                self._load_corrected_values(an, new_list)

    # def _get_isotope(self, name):
    #     return next((iso for iso in self.isotopes if iso.name == name), None)

    def _make_ratios(self, ratios):
        cv = []
        for name, nd, ref in ratios:
            if nd is None:
                continue

            n, d = nd.split("/")
            ns = [i for i in self.isotopes if i.name == n]
            ds = [i for i in self.isotopes if i.name == d]
            tag = name
            add_det_names = len(ns) > 1 or len(ds) > 1
            for ni in ns:
                for di in ds:
                    if add_det_names:
                        nd = "{}_{}/{}_{}".format(
                            ni.name, ni.detector, di.name, di.detector
                        )
                        name = "{}({})/{}({})".format(
                            ni.name, ni.detector, di.name, di.detector
                        )

                    dr = DetectorRatio(
                        name=name,
                        tag=tag,
                        value="",
                        error="",
                        noncorrected_value=0,
                        noncorrected_error=0,
                        ic_factor="",
                        ref_ratio=ref,
                        detectors=nd,
                    )
                    cv.append(dr)
        return cv

    def _get_non_corrected_ratio(self, niso, diso):
        """
        niso: Isotope
        diso: Isotope
        return ufloat

        calculate non_corrected ratio as
        r = (Intensity_A-baseline_A-blank_A)/(Intensity_B-baseline_B-blank_B)

        """

        if niso and diso:
            try:
                return (
                    niso.get_non_detector_corrected_value()
                    / diso.get_non_detector_corrected_value()
                )
            except ZeroDivisionError:
                pass

        return ufloat(0, 0)

    def _get_corrected_ratio(self, niso, diso):
        """
        niso: Isotope
        diso: Isotope
        return ufloat, ufloat

        calculate corrected ratio as
        r = IC_A*(Intensity_A-baseline_A-blank_A)/(IC_B*(Intensity_B-baseline_B-blank_B))
        rr = IC_B/IC_A
        """

        if niso and diso:
            try:
                return (
                    niso.get_ic_corrected_value() / diso.get_ic_corrected_value(),
                    diso.ic_factor / niso.ic_factor,
                )
            except (ZeroDivisionError, TypeError):
                pass
        return ufloat(0, 0), 1

    def _get_ratio(self, tag):
        def get_iso(kk):
            if "_" in kk:
                iso, det = kk.split("_")

                def test(i):
                    return i.name == iso and i.detector == det

            else:

                def test(i):
                    return i.name == kk

            return next((v for v in self.isotopes if test(v)), None)

        n, d = tag.split("/")

        niso, diso = get_iso(n), get_iso(d)
        return niso, diso

    def _set_summary_str(self, s):
        invoke_in_main_thread(self.trait_set, summary_str=s)

    def _update_ratios(self):

        for ci in self.computed_values:
            if not isinstance(ci, DetectorRatio):
                continue

            nd = ci.detectors
            niso, diso = self._get_ratio(nd)
            if niso and diso:
                noncorrected = self._get_non_corrected_ratio(niso, diso)
                corrected, ic = self._get_corrected_ratio(niso, diso)

                ci.trait_set(
                    value=floatfmt(nominal_value(corrected)),
                    error=floatfmt(std_dev(corrected)),
                    sig_figs=self.sig_figs,
                    noncorrected_value=nominal_value(noncorrected),
                    noncorrected_error=std_dev(noncorrected),
                    ic_factor=nominal_value(ic),
                )

    def _computed_value_factory(self, *args, **kw):
        if "sig_figs" not in kw:
            kw["sig_figs"] = self.sig_figs

        return ComputedValue(*args, **kw)

    def _load_air_computed(self, an, new_list):
        if self.experiment_type == AR_AR:
            if new_list:
                c = an.arar_constants
                ratios = [
                    ("40Ar/36Ar", "Ar40/Ar36", nominal_value(c.atm4036)),
                    ("40Ar/38Ar", "Ar40/Ar38", nominal_value(c.atm4038)),
                ]
                cv = self._make_ratios(ratios)
                self.computed_values = cv

            self._update_ratios()

            try:
                # niso, diso = self._get_ratio('Ar40/Ar36')
                # if niso and diso:
                #     noncorrected = self._get_non_corrected_ratio(niso, diso)
                #     v, e = nominal_value(noncorrected), std_dev(noncorrected)
                ci = self.computed_values[0]
                v = ci.value
                e = ci.error
                ss = "Ar40/Ar36={} {}{}({}%) IC={:0.5f}".format(
                    floatfmt(v),
                    PLUSMINUS,
                    floatfmt(e),
                    format_percent_error(v, e),
                    ci.calc_ic,
                )

                self._set_summary_str(ss)
            except BaseException as exc:
                print("load air computed", exc)
        else:
            # todo add ratios for other isotopes. e.g Ne
            pass

    def _load_cocktail_computed(self, an, new_list):
        if new_list:
            c = an.arar_constants
            ratios = []
            refs = {
                "40Ar/38Ar": nominal_value(c.atm4038),
                "40Ar/36Ar": nominal_value(c.atm4036),
            }

            if self.recall_options:
                names = [r.tagname for r in self.recall_options.cocktail_options.ratios]
                ratios = [(name, name, refs.get(name, 1)) for name in names]

            cv = self._make_ratios(ratios)

            an.calculate_age()
            cv.append(self._computed_value_factory(name="F", tag="uf", uvalue=an.uF))

            cv.append(
                self._computed_value_factory(
                    name="40Ar*", tag="radiogenic_yield", uvalue=an.radiogenic_yield
                )
            )

            cv.append(
                self._computed_value_factory(name="Age", tag="uage", uvalue=an.uage)
            )

            self.computed_values = cv
            self._update_ratios()
        else:
            self._update_ratios()

    def _load_corrected_values(self, an, new_list):
        attrs = (
            ("40/39", "Ar40/Ar39_decay_corrected"),
            ("40/37", "Ar40/Ar37_decay_corrected"),
            ("40/36", "Ar40/Ar36"),
            ("40/38", "Ar40/Ar38"),
            ("(40/36)non_ic", "uAr40_Ar36"),
            ("(40/38)non_ic", "uAr40_Ar38"),
            ("38/39", "Ar38/Ar39_decay_corrected"),
            ("37/39", "Ar37_decay_corrected/Ar39_decay_corrected"),
            ("36/39", "Ar36/Ar39_decay_corrected"),
        )

        if new_list:

            def comp_factory(n, a, value=None, value_tag=None, error_tag=None):
                if value is None:
                    value = getattr(an, a)

                display_value = True
                if value_tag:
                    value = getattr(an, value_tag)
                    display_value = False

                if error_tag:
                    e = getattr(an, error_tag)
                else:
                    e = std_dev(value)

                return self._computed_value_factory(
                    name=n,
                    tag=a,
                    value=nominal_value(value or 0),
                    display_value=display_value,
                    error=e or 0,
                )

            cv = [comp_factory(*args) for args in attrs]

            self.corrected_values = cv
        else:
            for ci in self.corrected_values:
                attr = ci.tag
                v = getattr(an, attr)
                ci.value = nominal_value(v)
                ci.error = std_dev(v)
                ci.sig_figs = self.sig_figs

    @property
    def sig_figs(self):
        sig_figs = 5
        if self.recall_options:
            sig_figs = self.recall_options.computed_sig_figs
        return sig_figs

    def _load_unknown_computed(self, an, new_list):
        attrs = (
            ("Age", "uage_w_j_err"),
            ("w/o J", "wo_j", "", "uage", "age_err_wo_j"),
            ("K/Ca", "kca"),
            ("K/Cl", "kcl"),
            ("40Ar*", "radiogenic_yield"),
            ("F", "uF"),
            ("w/o Irrad", "wo_irrad", "", "uF", "F_err_wo_irrad"),
        )

        if new_list:

            def comp_factory(n, a, value=None, value_tag=None, error_tag=None):
                if value is None:
                    value = getattr(an, a)

                display_value = True
                if value_tag:
                    value = getattr(an, value_tag)
                    display_value = False

                if error_tag:
                    e = getattr(an, error_tag)
                else:
                    e = std_dev(value)

                return self._computed_value_factory(
                    name=n,
                    tag=a,
                    value=nominal_value(value) or 0,
                    value_tag=value_tag or "",
                    display_value=display_value,
                    error=e or 0,
                )

            cv = [comp_factory(*args) for args in attrs]

            self.computed_values = cv
        else:
            an.calculate_age(force=True)
            age = an.uage
            nage, sage = nominal_value(age), std_dev(age)
            try:
                ss = "Age={} {}{}({}%) {}".format(
                    floatfmt(nage),
                    PLUSMINUS,
                    floatfmt(sage),
                    format_percent_error(nage, sage),
                    an.arar_constants.age_units,
                )
                self._set_summary_str(ss)
            except:
                pass

            for ci in self.computed_values:
                ci.sig_figs = self.sig_figs
                attr = ci.tag
                if attr == "wo_j":
                    ci.error = an.age_err_wo_j or 0
                    ci.value = nominal_value(getattr(an, ci.value_tag))
                elif attr == "wo_irrad":
                    ci.error = an.F_err_wo_irrad or 0
                    ci.value = nominal_value(getattr(an, ci.value_tag))
                else:
                    v = getattr(an, attr)
                    if v is not None:
                        ci.value = nominal_value(v)
                        ci.error = std_dev(v)

    @cached_property
    def _get_computed_adapter(self):
        adapter = ComputedValueTabularAdapter
        if self.analysis_type in (
            "air",
            "cocktail",
            "blank_unknown",
            "blank_air",
            "blank_cocktail",
        ):
            adapter = DetectorRatioTabularAdapter
        return adapter()

    def _get_editors(self):

        ceditor = myTabularEditor(
            adapter=self.computed_adapter, editable=False, refresh="refresh_needed"
        )

        eeditor = myTabularEditor(
            adapter=self.extraction_adapter, editable=False, refresh="refresh_needed"
        )

        meditor = myTabularEditor(
            adapter=self.measurement_adapter, editable=False, refresh="refresh_needed"
        )

        return ceditor, eeditor, meditor

    def traits_view(self):
        ceditor, eeditor, meditor = self._get_editors()

        g1 = HGroup(
            UItem("measurement_values", editor=meditor, height=200, width=0.4),
            UItem("extraction_values", editor=eeditor, height=200, width=0.6),
        )
        g2 = HGroup(
            UItem(
                "computed_values",
                editor=ceditor,
            ),
            UItem("corrected_values", editor=ceditor),
        )
        v = View(VGroup(g1, g2))

        return v


# ============= EOF =============================================
