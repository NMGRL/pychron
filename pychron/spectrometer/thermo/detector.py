# ===============================================================================
# Copyright 2011 Jake Ross
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
from traits.api import Float, Str, Bool, Property, Color, \
    Int, Array
from traitsui.api import View, Item, HGroup, \
    spring
#============= standard library imports ========================
import os
from numpy import loadtxt, polyfit, polyval, hstack, poly1d
from scipy import optimize
#============= local library imports  ==========================
from pychron.spectrometer.thermo.spectrometer_device import SpectrometerDevice
from pychron.paths import paths
from pychron.core.ui.qt.color_square_editor import ColorSquareEditor


charge = 1.6021764874e-19


class Detector(SpectrometerDevice):
    name = Str

    kind = Str

    protection_threshold = None
    deflection = Property(Float(enter_set=True, auto_set=False), depends_on='_deflection')
    _deflection = Float(0)

    deflection_correction_sign = Int(1)

    _deflection_correction_factors = None
    #    intensity = Property(depends_on='spectrometer:intensity_dirty')
    #    intensity = Float
    #    std = Float
    intensity = Str
    std = Str
    intensities = Array
    nstd = Int(10)
    active = Bool(True)
    gain = Float

    color = Color
    series_id = Int
    isotope = Str

    isotopes = Property
    #color_square = None

    def load(self):
        self.read_deflection()

    def load_deflection_coefficients(self):
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
        r = self.ask('GetDeflection {}'.format(self.name))
        try:
            if r is None:
                self.warning(
                    'Failed reading {} deflection. Error=No response. Using previous value {}'.format(self.name,
                                                                                                      self._deflection))
            else:
                self._deflection = float(r)

        except (ValueError, TypeError), e:
            self.warning('Failed reading {} deflection. Error={}. Using previous value {}'.format(self.name, e,
                                                                                                  self._deflection))

    def get_deflection_correction(self, current=False):
        if current:
            self.read_deflection()

        de = self._deflection
        dev = polyval(self._deflection_correction_factors, [de])[0]

        return self.deflection_correction_sign * dev

    def map_dac_to_deflection(self, dac):
        c = self._deflection_correction_factors[:]
        c[-1] -= dac
        return optimize.newton(poly1d(c), 1)

    @property
    def gain_outdated(self):
        return abs(self.get_gain()-self.gain)<1e-7

    def get_gain(self):
        v = self.ask('GetGain {}'.format(self.name))
        try:
            v = float(v)
        except (TypeError, ValueError):
            v = 0
        self.gain=v
        return v

    def set_gain(self):
        self.ask('SetGain {},{}'.format(self.name, self.gain))

    def _get_isotopes(self):
        molweights = self.spectrometer.molecular_weights
        return sorted(molweights.keys(), key=lambda x: int(x[2:]))

    def _set_deflection(self, v):
        self._deflection = v
        self.ask('SetDeflection {},{}'.format(self.name, v))

    def _get_deflection(self):
        return self._deflection

    def set_intensity(self, v):
        if v is not None:
            n = self.nstd
            self.intensities = hstack((self.intensities[-n:], [v]))
            self.std = '{:0.5f}'.format(self.intensities.std())
            self.intensity = '{:0.5f}'.format(v)

    #def intensity_view(self):
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
        v = View(HGroup(Item('active'),
                        Item('color', width=25, editor=ColorSquareEditor()),
                        Item('name', style='readonly'),
                        spring,
                        Item('deflection'),
                        show_labels=False))
        return v

    def __repr__(self):
        return self.name
        #============= EOF =============================================