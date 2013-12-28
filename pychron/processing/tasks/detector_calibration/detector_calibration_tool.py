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
from traits.api import HasTraits, Instance, Str, List, Property, DelegatesTo, Float, \
    Enum, on_trait_change
from traitsui.api import View, Item, UItem, EnumEditor, VGroup

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.processing.fits.fit import Fit
from pychron.processing.fits.interpolation_fit_selector import InterpolationFitSelector


class DetectorCalibrationTool(HasTraits):
    fit_selector = Instance(InterpolationFitSelector, ())
    reference_detector = Str
    detectors = List
    target_detector = Str
    target_detectors = Property(depends_on='reference_detector')
    analysis_type = Str
    analysis_types = List

    fits = DelegatesTo('fit_selector')
    update_needed = DelegatesTo('fit_selector')

    standard_ratio = Float(enter_set=True, auto_set=False)
    error_calc = Enum('SD', 'SEM')

    def _get_dump_tool(self):
        return self.fits

    @on_trait_change('standard_ratio, error_calc')
    def _handle_change(self, name, new):
        self.update_needed = True

    def _analysis_type_changed(self, new):
        if new:
            self._set_default_detector_selection(new)
            self._set_default_fits(new)

    def _set_default_detector_selection(self, atype):
        atype = atype.lower()
        if atype == 'air':
            self.reference_detector = 'H1'
            self.target_detector = 'CDD'
            self.standard_ratio = 295.5
        elif atype == 'cocktail':
            self.reference_detector = 'H1'
            self.target_detector = 'AX'
            self.standard_ratio = 15

    def _set_default_fits(self, atype):
        atype = atype.lower()
        self.fits = [Fit(name='{}/{}'.format(self.reference_detector,
                                             self.target_detector))]


    def _get_target_detectors(self):
        return [ri for ri in self.detectors if ri != self.reference_detector]

    def traits_view(self):
        v = View(
            VGroup(Item('analysis_type',
                        editor=EnumEditor(name='analysis_types')),
                   Item('standard_ratio', label='Ratio'),
                   Item('error_calc', label='Error Calc.'),
                   Item('reference_detector',
                        label='Ref. Detector',
                        editor=EnumEditor(name='detectors')),
                   Item('target_detector', editor=EnumEditor(name='target_detectors'),
                        label='Target Detector')),
            UItem('fit_selector', style='custom')

        )
        return v

#============= EOF =============================================
