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
from traits.api import HasTraits, Str, List, Event
from traitsui.api import View, UItem, HGroup, HSplit, VSplit

#============= standard library imports ========================
#============= local library imports  ==========================
from uncertainties import std_dev, nominal_value, ufloat
from pychron.core.helpers.formatting import floatfmt
from pychron.processing.analyses.view.adapters import IsotopeTabularAdapter, ComputedValueTabularAdapter, \
    DetectorRatioTabularAdapter, ExtractionTabularAdapter, MeasurementTabularAdapter, IntermediateTabularAdapter
from pychron.processing.analyses.view.values import ExtractionValue, ComputedValue, MeasurementValue, DetectorRatio
from pychron.core.ui.tabular_editor import myTabularEditor


class MainView(HasTraits):
    name = 'Main'

    analysis_id = Str
    analysis_type = Str

    isotopes = List
    refresh_needed = Event

    computed_values = List
    corrected_values = List
    extraction_values = List
    measurement_values = List

    def __init__(self, analysis=None, *args, **kw):
        super(MainView, self).__init__(*args, **kw)
        if analysis:
            self._load(analysis)

    def load(self, an):
        self._load(an)

    def _load(self, an):
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
            jj = floatfmt(j.nominal_value, n=7, s=5)
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

            MeasurementValue(name='Project',
                             value=an.project),
            MeasurementValue(name='Sample',
                             value=an.sample),
            MeasurementValue(name='Material',
                             value=an.material),
            MeasurementValue(name='Comment',
                             value=an.comment),
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
                            value=an.position, ),
            ExtractionValue(name='Extract Value',
                            value=an.extract_value,
                            units=an.extract_units, ),
            ExtractionValue(name='Duration',
                            value=an.duration,
                            units='s'),
            ExtractionValue(name='Cleanup',
                            value=an.cleanup,
                            units='s')]

        if 'UV' in an.extract_device:
            extra = [ExtractionValue(name='Mask Pos.',
                                     value=an.mask_position,
                                     units='steps'),
                     ExtractionValue(name='Mask Name',
                                     value=an.mask_name),
                     ExtractionValue(name='Reprate',
                                     value=an.reprate,
                                     units='1/s')]
        else:
            extra = [ExtractionValue(name='Beam Diam.',
                                     value=an.beam_diameter,
                                     units='mm'),
                     ExtractionValue(name='Pattern',
                                     value=an.pattern),
                     ExtractionValue(name='Ramp Dur.',
                                     value=an.ramp_duration,
                                     units='s'),
                     ExtractionValue(name='Ramp Rate',
                                     value=an.ramp_rate,
                                     units='1/s')]

        ev.extend(extra)

        self.extraction_values = ev

    def load_computed(self, an, new_list=True):

        if self.analysis_type == 'unknown':
            self._load_unknown_computed(an, new_list)
            self._load_corrected_values(an, new_list)
        elif self.analysis_type in ('air', 'blank_air', 'blank_unknown', 'blank_cocktail'):
            self._load_air_computed(an, new_list)
        elif self.analysis_type == 'cocktail':
            self._load_cocktail_computed(an, new_list)

    def _get_isotope(self, name):
        return next((iso for iso in self.isotopes if iso.name == name), None)

    def _make_ratios(self, an, ratios):
        cv = []
        for name, nd, ref in ratios:
            dr = DetectorRatio(name=name,
                               value='',
                               error='',
                               noncorrected_value=0,
                               noncorrected_error=0,
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
                pass

        return ufloat(0, 1e-20)

    def _get_corrected_ratio(self, nd):
        n, d = nd.split('/')
        niso, diso = self._get_isotope(n), self._get_isotope(d)
        if niso and diso:
            try:
                return niso.get_ic_corrected_value() / diso.get_ic_corrected_value(), diso.ic_factor / niso.ic_factor
            except (ZeroDivisionError, TypeError):
                pass
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
                         ic_factor=nominal_value(ic))

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

    def _load_corrected_values(self, an, new_list):
        attrs = (('40/39', 'Ar40/Ar39_decay_corrected'),
                 ('40/37', 'Ar40/Ar37_decay_corrected'),
                 ('40/36', 'Ar40/Ar36'),
                 ('38/39', 'Ar38/Ar39_decay_corrected'),
                 ('37/39', 'Ar37_decay_corrected/Ar39_decay_corrected'),
                 ('36/39', 'Ar36/Ar39_decay_corrected'),
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

                return ComputedValue(name=n,
                                     tag=a,
                                     value=nominal_value(value) or 0,
                                     display_value=display_value,
                                     error=e or 0)

            cv = [comp_factory(*args)
                  for args in attrs]

            self.corrected_values = cv
        else:
            for ci in self.corrected_values:
                attr = ci.tag
                v = getattr(an, attr)
                ci.value = nominal_value(v)
                ci.error = std_dev(v)

    def _load_unknown_computed(self, an, new_list):

        attrs = (('Age', 'uage'),
                 # ('Age', 'age', None, None, 'age_err'),
                 ('w/o J', 'wo_j', '', 'uage', 'age_err_wo_j'),
                 ('K/Ca', 'kca'),
                 ('K/Cl', 'kcl'),
                 ('40Ar*', 'rad40_percent'),
                 ('F', 'uF'),
                 ('w/o Irrad', 'wo_irrad', '', 'uF', 'F_err_wo_irrad')
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

                return ComputedValue(name=n,
                                     tag=a,
                                     value=nominal_value(value) or 0,
                                     display_value=display_value,
                                     error=e or 0)

            cv = [comp_factory(*args)
                  for args in attrs]

            self.computed_values = cv
        else:
            for ci in self.computed_values:
                attr = ci.tag
                if attr == 'wo_j':
                    ci.error = an.age_err_wo_j
                elif attr == 'wo_irrad':
                    ci.error = an.F_err_wo_irrad
                else:
                    v = getattr(an, attr)
                    ci.value = nominal_value(v)
                    ci.error = std_dev(v)

    def _get_editors(self):
        teditor = myTabularEditor(adapter=IsotopeTabularAdapter(),
                                  editable=False,
                                  refresh='refresh_needed')

        adapter = ComputedValueTabularAdapter
        if self.analysis_type in ('air', 'cocktail',
                                  'blank_unknown', 'blank_air',
                                  'blank_cocktail'):
            adapter = DetectorRatioTabularAdapter
        ceditor = myTabularEditor(adapter=adapter(),
                                  editable=False,
                                  refresh='refresh_needed')

        ieditor = myTabularEditor(adapter=IntermediateTabularAdapter(),
                                  editable=False,
                                  refresh='refresh_needed')

        eeditor = myTabularEditor(adapter=ExtractionTabularAdapter(),
                                  editable=False, )
        meditor = myTabularEditor(adapter=MeasurementTabularAdapter(),
                                  editable=False)

        return teditor, ieditor, ceditor, eeditor, meditor


    def traits_view(self):
        teditor, ieditor, ceditor, eeditor, meditor = self._get_editors()

        v = View(
            VSplit(
                HGroup(
                    UItem('measurement_values',
                          editor=meditor),
                    UItem('extraction_values',
                          editor=eeditor)),
                UItem('isotopes',
                      editor=teditor),
                UItem('isotopes',
                      editor=ieditor),
                HSplit(UItem('computed_values',
                             editor=ceditor),
                       UItem('corrected_values', editor=ceditor))))
        return v


#============= EOF =============================================
