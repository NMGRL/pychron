# ===============================================================================
# Copyright 2014 Jake Ross
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
import csv
import os
from traits.api import HasTraits, List, Float, Str, Button
from traitsui.api import View, UItem, TabularEditor, VGroup, HGroup, spring
from traitsui.tabular_adapter import TabularAdapter
# ============= standard library imports ========================
# ============= local library imports  ==========================
from uncertainties import std_dev, nominal_value, ufloat
from pychron.core.helpers.filetools import unique_path2, add_extension
from pychron.core.helpers.formatting import floatfmt
from pychron.paths import paths
from pychron.pychron_constants import PLUSMINUS_SIGMA, DETECTOR_ORDER


class DetectorICTabularAdapter(TabularAdapter):
    font = 'arial 12'


class RatioItem(HasTraits):
    name = Str
    refvalue = 1.0
    intensity = Str
    intensity_err = Str

    def add_ratio(self, x):
        v = x.get_non_detector_corrected_value() / self.refvalue

        self.add_trait(x.detector, Float(round(nominal_value(v), 5)))
        self.add_trait('{}_err'.format(x.detector), Float(round(std_dev(v), 5)))

    def to_row(self):
        vs = [self.name, self.intensity, self.intensity_err]
        for det in DETECTOR_ORDER:
            try:
                v = getattr(self, det)
                vs.append(v)
            except AttributeError:
                vs.append(0)
        return vs
        # return [for det in DETECTOR_ORDER if hasattr(self, det)]


class DetectorICView(HasTraits):
    name = 'DetectorIC'
    items = List
    helpstr = """Values are COL/ROW ratios"""
    export_button = Button
    _isotope_key = 'Ar40'

    def __init__(self, an):
        self.tabular_adapter = DetectorICTabularAdapter()
        self.record_id = an.record_id
        isotopes = [an.isotopes[k] for k in an.isotope_keys if k.startswith(self._isotope_key)]

        detcols = list(self._get_columns(isotopes))

        self.tabular_adapter.columns = [('', 'name'),
                                        ('Intensity', 'intensity'),
                                        (PLUSMINUS_SIGMA, 'intensity_err')] + detcols

        items = []
        for det in DETECTOR_ORDER:
            ai = next((ai for ai in isotopes if ai.detector.upper() == det), None)
            if ai:
                rv = ai.get_non_detector_corrected_value()
                r = RatioItem(name=ai.detector,
                              refvalue=rv,
                              intensity=floatfmt(nominal_value(rv)),
                              intensity_err=floatfmt(std_dev(rv)))
                r.add_ratio(ai)
                for bi in isotopes:
                    r.add_ratio(bi)

                items.append(r)

        self.items = items

    def _get_columns(self, isos):

        for det in DETECTOR_ORDER:
            iso = next((iso for iso in isos if iso.detector.upper() == det), None)
            if iso:
                yield det, iso.detector
                # for iso in isos:
                # det=iso.detector.upper()
                # yield det, iso.detector
                # yield PLUSMINUS_SIGMA, '{}_err'.format(iso.detector)

    def _export_button_fired(self):
        path = os.path.join(paths.data_det_ic_dir, add_extension(self.record_id,'.csv'))
        # path, _ = unique_path2(paths.data_dir, 'det_ic')
        with open(path, 'w') as fp:
            wrt = csv.writer(fp, delimiter='\t')
            wrt.writerow(['#det','intensity','err']+DETECTOR_ORDER)
            for i in self.items:
                wrt.writerow(i.to_row())


    def traits_view(self):
        v = View(VGroup(HGroup(spring,UItem('export_button')),
                        UItem('items', editor=TabularEditor(adapter=self.tabular_adapter)),
                        VGroup(
                            UItem('helpstr', style='readonly'), show_border=True, label='Info.')),
                 width=700)
        return v


if __name__ == '__main__':
    class MockIsotope():
        def __init__(self, n, d, i):
            self.name = n
            self.detector = d
            self.value = i

        def get_corrected_value(self):
            return ufloat(self.value, 0.1)

    class MockAnalysis():
        isotopes = {k: MockIsotope(k, d, i + 1.0) for i, (k, d) in
                    enumerate([('Ar40H1', 'H1'), ('Ar40AX', 'AX'), ('Ar40L1', 'L1'), ('Ar39', 'CDD')])}

        @property
        def isotope_keys(self):
            return [i for i in self.isotopes]

    an = MockAnalysis()

    d = DetectorICView(an)
    d.configure_traits()
# ============= EOF =============================================
