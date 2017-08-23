# ===============================================================================
# Copyright 2011 Jake Ross
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

# ============= standard library imports ========================
import os

from numpy import loadtxt, polyfit, polyval, poly1d
from scipy import optimize
# ============= enthought library imports =======================
from traits.api import Float, Property, Int
from traitsui.api import View, Item, HGroup, \
    spring

from pychron.paths import paths
# ============= local library imports  ==========================
from pychron.spectrometer.base_detector import BaseDetector
from pychron.spectrometer.spectrometer_device import SpectrometerDevice


class ThermoDetector(BaseDetector, SpectrometerDevice):
    use_deflection = True
    protection_threshold = None
    deflection = Property(Float(enter_set=True, auto_set=False),
                          depends_on='_deflection')
    _deflection = Float(0)

    deflection_correction_sign = Int(1)
    _deflection_correction_factors = None
    deflection_name = None

    def load(self):
        self.read_deflection()


    def load_deflection_coefficients(self):
        if self.use_deflection:
            # load deflection correction table
            p = os.path.join(paths.spectrometer_dir,
                             'deflections', self.name)
            if os.path.isfile(p):
                x, y = loadtxt(p, delimiter=',', unpack=True)
                y -= y[0]
                coeffs = polyfit(x, y, 1)
                self._deflection_correction_factors = coeffs
            else:
                self.warning('no deflection data for {}'.format(self.name))

    def read_deflection(self):
        if self.use_deflection or self.kind in ('IonCounter',):
            r = self.ask('GetDeflection {}'.format(self.deflection_name))
            try:
                if r is None:
                    self.warning('Failed reading {} deflection. Error=No response. '
                                 'Using previous value {}'.format(self.name,
                                                                  self._deflection))
                else:
                    self._deflection = float(r)

            except (ValueError, TypeError), e:
                self.warning('Failed reading {} deflection. Error={}. '
                             'Using previous value {}'.format(self.name, e,
                                                              self._deflection))
        return self._deflection

    def get_deflection_correction(self, current=False):
        corr = 0
        if self.use_deflection:
            if current:
                self.read_deflection()

            if self._deflection_correction_factors is not None:
                corr = polyval(self._deflection_correction_factors, [self._deflection])[0]

            corr *= self.deflection_correction_sign

        return corr

    def map_dac_to_deflection(self, dac):
        defl = 0
        if self.use_deflection:
            c = self._deflection_correction_factors[:]
            c[-1] -= dac
            defl = optimize.newton(poly1d(c), 1)
        return defl

    # private
    def _set_gain(self):
        self.ask('SetGain {},{}'.format(self.name, self.gain))

    def _read_gain(self):
        v = self.ask('GetGain {}'.format(self.name))

    def _set_deflection(self, v):
        if self.use_deflection:
            if self._deflection != v:
                self.spectrometer.update_config(Deflections=[(self.name, v)])

            self._deflection = v
            self.ask('SetDeflection {},{}'.format(self.deflection_name, v))

    def _get_deflection(self):
        return self._deflection

    def _active_changed(self, new):
        self.debug('active changed {}'.format(new))
        if self.name == 'CDD':
            self.debug(
                    '{} Ion Counter'.format(
                            'Activate' if new else 'Deactivate'))
            self.info('De/Activating CDD disabled')
            # self.ask('ActivateIonCounter' if new else 'DeactivateIonCounter')

    # def intensity_view(self):
    #    v = View(HGroup(
    #        Item('color',
    #             editor=ColorSquareEditor(),
    #             width=20),
    #        Item('name', style='readonly'),
    #        spring,
    #        Item('intensity', style='readonly'),
    #        Spring(springy=False, width=150),
    #        Item('std', style='readonly'),
    #        Spring(springy=False, width=100),
    #        show_labels=False))
    #    return v

    def traits_view(self):
        from pychron.core.ui.qt.color_square_editor import ColorSquareEditor

        v = View(HGroup(Item('active'),
                        Item('color', width=25, editor=ColorSquareEditor()),
                        Item('name', style='readonly'),
                        spring,
                        Item('deflection', visible_when='use_deflection'),
                        show_labels=False))
        return v

# ============= EOF =============================================
