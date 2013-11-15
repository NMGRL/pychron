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
from traits.api import HasTraits, List, Str, Property, Event, Either, Int, Float
from traitsui.api import View, UItem, HGroup, Group

#============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter
from uncertainties import ufloat, std_dev, nominal_value
from pychron.helpers.formatting import floatfmt, calc_percent_error
from pychron.ui.tabular_editor import myTabularEditor

SIGMA_1 = u'\u00b11\u03c3'
TABLE_FONT = 'arial 11'

vwidth = Int(60)
ewidth = Int(50)
pwidth = Int(40)


class BaseTabularAdapter(TabularAdapter):
    default_bg_color = '#F7F6D0'
    font = TABLE_FONT


class IsotopeTabularAdapter(BaseTabularAdapter):
    columns = [('Iso.', 'name'),
               ('Det.', 'detector'),
               ('Fit', 'fit_abbreviation'),
               ('Int.', 'value'),
               (SIGMA_1, 'error'),
               ('%', 'value_percent_error'),
               ('Fit', 'baseline_fit_abbreviation'),
               ('Base.', 'base_value'),
               (SIGMA_1, 'base_error'),
               ('%', 'baseline_percent_error'),
               ('Blank', 'blank_value'),
               (SIGMA_1, 'blank_error'),
               ('%', 'blank_percent_error'),
               ('IC', 'ic_factor'),
               ('Error Comp.', 'age_error_component')]

    value_text = Property
    error_text = Property
    base_value_text = Property
    base_error_text = Property
    blank_value_text = Property
    blank_error_text = Property

    value_percent_error_text = Property
    blank_percent_error_text = Property
    baseline_percent_error_text = Property
    age_error_component_text = Property

    name_width = Int(40)
    fit_abbreviation_width = Int(25)
    baseline_fit_abbreviation_width = Int(25)
    detector_width = Int(40)

    value_width = vwidth
    error_width = ewidth

    base_value_width = vwidth
    base_error_width = ewidth
    blank_value_width = vwidth
    blank_error_width = ewidth

    value_percent_error_width = pwidth
    blank_percent_error_width = pwidth
    baseline_percent_error_width = pwidth

    def _get_value_text(self, *args, **kw):
        v = self.item.get_corrected_value()
        return floatfmt(v.nominal_value)

    def _get_error_text(self, *args, **kw):
        v = self.item.get_corrected_value()
        return floatfmt(v.std_dev)

    def _get_base_value_text(self, *args, **kw):
        return floatfmt(self.item.baseline.value)

    def _get_base_error_text(self, *args, **kw):
        return floatfmt(self.item.baseline.error)

    def _get_blank_value_text(self, *args, **kw):
        return floatfmt(self.item.blank.value)

    def _get_blank_error_text(self, *args, **kw):
        return floatfmt(self.item.blank.error)

    def _get_baseline_percent_error_text(self, *args):
        b = self.item.baseline
        return calc_percent_error(b.value, b.error)

    def _get_blank_percent_error_text(self, *args):
        b = self.item.blank
        return calc_percent_error(b.value, b.error)

    def _get_value_percent_error_text(self, *args):
        cv = self.item.get_corrected_value()
        return calc_percent_error(cv.nominal_value, cv.std_dev)

    def _get_age_error_component_text(self):
        return floatfmt(self.item.age_error_component, n=1)


class CompuatedValueTabularAdapter(BaseTabularAdapter):
    columns = [('Name', 'name'),
               ('Value', 'value'),
               (SIGMA_1, 'error'),
    ]
    name_width = Int(80)
    value_width = Int(80)
    units_width = Int(40)


class DetectorRatioTabularAdapter(BaseTabularAdapter):
    columns = [('Name', 'name'),
               ('Value', 'value'),
               (SIGMA_1, 'error'),
               ('Calc. IC', 'calc_ic'),
               ('ICFactor', 'ic_factor'),
               ('Ref. Ratio', 'ref_ratio'),

               ('Non IC Corrected', 'noncorrected_value'),
               (SIGMA_1, 'noncorrected_error'),
    ]
    calc_ic_text = Property

    noncorrected_value_text = Property
    noncorrected_error_text = Property

    def _get_calc_ic_text(self):
        return floatfmt(self.item.calc_ic)

    def _get_noncorrected_value_text(self):
        return floatfmt(self.item.noncorrected_value)

    def _get_noncorrected_error_text(self):
        return floatfmt(self.item.noncorrected_error)


class ExtractionTabularAdapter(BaseTabularAdapter):
    columns = [('Name', 'name'),
               ('Value', 'value'),
               ('Units', 'units')]

    name_width = Int(80)
    value_width = Int(90)
    units_width = Int(40)


class MeasurementTabularAdapter(BaseTabularAdapter):
    columns = [('Name', 'name'),
               ('Value', 'value'), ]
    name_width = Int(80)
    value_width = Int(80)


class NamedValue(HasTraits):
    name = Str
    value = Either(Str, Float, Int)


class ComputedValue(NamedValue):
    error = Either(Str, Float, Int)
    tag = Str


class DetectorRatio(ComputedValue):
    ic_factor = Either(Float, Str)
    detectors = Str
    noncorrected_value = Float
    noncorrected_error = Float
    calc_ic = Property(depends_on='value')
    ref_ratio = Float

    def _get_calc_ic(self):
        return self.noncorrected_value / self.ref_ratio


class ExtractionValue(NamedValue):
    units = Str


class MeasurementValue(NamedValue):
    pass


class AnalysisView(HasTraits):
    analysis_id = Str
    analysis_type = Str

    isotopes = List
    refresh_needed = Event

    computed_values = List
    extraction_values = List
    measurement_values = List

    def load(self, an):
        self.isotopes = [an.isotopes[k] for k in an.isotope_keys]

        self.load_computed(an)
        self.load_extraction(an)
        self.load_measurement(an, an)

    def _get_irradiation(self, an):
        return an.irradiation_label

    def _get_j(self, an):
        return an.j

    def load_measurement(self, an, ar):

        j = self._get_j(an)
        jf = 'NaN'
        if j is not None:
            jj = floatfmt(j.nominal_value, n=3, s=3)
            jf = u'{} \u00b1{:0.2e}'.format(jj, j.std_dev)

        a39 = ar.ar39decayfactor
        a37 = ar.ar37decayfactor
        #print ar, a39
        ms = [
            MeasurementValue(name='AnalysisID',
                             value=self.analysis_id),
            MeasurementValue(name='Spectrometer',
                             value=an.mass_spectrometer),
            MeasurementValue(name='Run Date',
                             value=an.rundate.strftime('%Y-%m-%d %H:%M:%S')),
            MeasurementValue(name='Irradiation',
                             value=self._get_irradiation(an)),
            MeasurementValue(name='J',
                             value=jf),
            MeasurementValue(name='Sample',
                             value=an.sample),
            MeasurementValue(name='Material',
                             value=an.material),

            MeasurementValue(name='Ar39Decay',
                             value=floatfmt(a39)),
            MeasurementValue(name='Ar37Decay',
                             value=floatfmt(a37)),

        ]
        self.measurement_values = ms

    def load_extraction(self, an):

        ev = [
            ExtractionValue(name='Device',
                            value=an.extract_device),
            ExtractionValue(name='Position',
                            value=an.position,
            ),
            ExtractionValue(name='Extract Value',
                            value=an.extract_value,
                            units=an.extract_units,
            ),
            ExtractionValue(name='Duration',
                            value=an.duration,
                            units='s'
            ),
            ExtractionValue(name='Cleanup',
                            value=an.cleanup,
                            units='s'
            ),
        ]

        self.extraction_values = ev

    def load_computed(self, an, new_list=True):
        if self.analysis_type == 'unknown':
            self._load_unknown_computed(an, new_list)
        elif self.analysis_type in ('air', 'blank_air', 'blank_unknown', 'blank_cocktail'):
            self._load_air_computed(an, new_list)
        elif self.analysis_type == 'cocktail':
            self._load_cocktail_computed(an, new_list)

    def _get_isotope(self, name):
        return next((iso for iso in self.isotopes if iso.name == name), None)

    def _make_ratios(self, an, ratios):
        cv = []
        for name, nd, ref in ratios:
        #            n, d = nd.split('/')
        #            r = self._get_non_corrected_ratio(nd)
        #            if r is not None:
        #            d_iso = self._get_isotope(d)
        #            n_iso = self._get_isotope(n)
        #            ic = d_iso.ic_factor / n_iso.ic_factor
        #                try:
        #                    rr = n_iso.ic_corrected_value() / d_iso.ic_corrected_value()
        #                except ZeroDivisionError:
        #                    rr=ufloat(0,1e-20)

            dr = DetectorRatio(name=name,
                               value='', #floatfmt(rr.nominal_value),
                               error='', #floatfmt(rr.std_dev),
                               noncorrected_value=0, #floatfmt(r.nominal_value),
                               noncorrected_error=0, #floatfmt(r.std_dev),
                               ic_factor='',
                               ref_ratio=ref,
                               detectors=nd)
            cv.append(dr)

        return cv

    def _get_non_corrected_ratio(self, nd):
        n, d = nd.split('/')
        niso, diso = self._get_isotope(n), self._get_isotope(d)
        if niso and diso:
            try:
                return niso / diso
            except ZeroDivisionError:
                return ufloat(0, 1e-20)

    def _get_corrected_ratio(self, nd):
        n, d = nd.split('/')
        niso, diso = self._get_isotope(n), self._get_isotope(d)
        if niso and diso:
            try:
                return niso.ic_corrected_value() / diso.ic_corrected_value(), diso.ic_factor / niso.ic_factor
            except ZeroDivisionError:
                return ufloat(0, 1e-20), 1

    def _update_ratios(self, an):
        for ci in self.computed_values:
            nd = ci.detectors
            r = self._get_non_corrected_ratio(nd)
            rr, ic = self._get_corrected_ratio(nd)

            ci.trait_set(value=floatfmt(rr.nominal_value),
                         error=floatfmt(rr.std_dev),
                         noncorrected_value=r.nominal_value,
                         noncorrected_error=r.std_dev,
                         ic_factor=ic)

    def _load_air_computed(self, an, new_list):
        if new_list:
            ratios = [('40Ar/36Ar', 'Ar40/Ar36', 295.5), ('40Ar/38Ar', 'Ar40/Ar38', 1)]
            cv = self._make_ratios(an, ratios)
            self.computed_values = cv
        else:
            self._update_ratios(an)

    def _load_cocktail_computed(self, an, new_list):
        if new_list:
            ratios = [('40Ar/36Ar', 'Ar40/Ar36', 295.5), ('40Ar/39Ar', 'Ar40/Ar39', 1)]
            cv = self._make_ratios(an, ratios)
            self.computed_values = cv
        else:
            self._update_ratios(an)

    def _load_unknown_computed(self, an, new_list):

        attrs = (('Age', 'age', None, 'age_err'),
                 ('w/o J', 'wo_j', '', 'age_err_wo_j'),
                 ('K/Ca', 'kca'),
                 ('K/Cl', 'kcl'),
                 ('40Ar*', 'rad40_percent'),
                 ('R', 'R', None, 'R_err'))
        if new_list:
            def comp_factory(n, a, value=None, error_tag=None):
                if value is None:
                    aa = getattr(an, a)
                    value = floatfmt(nominal_value(aa))

                if error_tag:
                    e = getattr(an, error_tag)
                else:
                    e = std_dev(aa)

                return ComputedValue(name=n,
                                     tag=a,
                                     value=value,
                                     error=floatfmt(e))

            cv = [comp_factory(*args)
                  for args in attrs]

            #insert error w/o j
            #cv.insert(1, ComputedValue(name='w/o J',
            #                           tag='wo_j',
            #                           value='',
            #                           error=floatfmt(an.age_error_wo_j)))
            self.computed_values = cv
        else:
            for ci in self.computed_values:
                attr = ci.tag
                if attr == 'wo_j':
                    ci.error = an.age_error_wo_j
                else:
                    ci.value = floatfmt(getattr(an, attr).nominal_value)
                    ci.error = floatfmt(getattr(an, attr).std_dev)

    def _get_editors(self):
        teditor = myTabularEditor(adapter=IsotopeTabularAdapter(),
                                  editable=False,
                                  refresh='refresh_needed')

        adapter = CompuatedValueTabularAdapter
        if self.analysis_type in ('air', 'cocktail',
                                  'blank_unknown', 'blank_air',
                                  'blank_cocktail'):
            adapter = DetectorRatioTabularAdapter
        ceditor = myTabularEditor(adapter=adapter(),
                                  editable=False,
                                  refresh='refresh_needed')

        eeditor = myTabularEditor(adapter=ExtractionTabularAdapter(),
                                  editable=False,
        )
        meditor = myTabularEditor(adapter=MeasurementTabularAdapter(),
                                  editable=False)

        return teditor, ceditor, eeditor, meditor


    def traits_view(self):
        teditor, ceditor, eeditor, meditor = self._get_editors()

        v = View(
            HGroup(
                UItem('measurement_values',
                      editor=meditor),
                UItem('extraction_values',
                      editor=eeditor),
            ),
            UItem('isotopes',
                  editor=teditor),
            UItem('computed_values',
                  editor=ceditor
            )
        )
        return v


class DBAnalysisView(AnalysisView):
    pass


class AutomatedRunAnalysisView(AnalysisView):
    def update_values(self, arar_age):
        for ci in self.computed_values:
            v = getattr(arar_age, ci)

    def load(self, ar):
        an = ar.arar_age
        self.isotopes = [an.isotopes[k] for k in an.isotope_keys]

        #for iso in self.isotopes:
        #    print iso, iso.name, 'det', iso.detector

        self._irradiation_str = ar.spec.irradiation
        self._j = an.j

        self.load_computed(an)
        self.load_extraction(ar.spec)
        self.load_measurement(ar.spec, an)

    def _get_irradiation(self, an):
        return self._irradiation_str

    def _get_j(self, an):
        return self._j

    def traits_view(self):
        teditor, ceditor, eeditor, meditor = es = self._get_editors()
        for ei in es:
            ei.adapter.font = 'arial 10'

        isotopes = UItem('isotopes', editor=teditor, label='Isotopes')

        ratios = UItem('computed_values', editor=ceditor, label='Ratios')

        meas = UItem('measurement_values',
                     editor=meditor, label='General')

        extract = UItem('extraction_values',
                        editor=eeditor,
                        label='Extraction')

        v = View(
            Group(isotopes, ratios, extract, meas, layout='tabbed'))
        return v

#============= EOF =============================================
