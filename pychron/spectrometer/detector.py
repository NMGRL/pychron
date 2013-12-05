#===============================================================================
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
    Int, on_trait_change, Array
from traitsui.api import View, Item, VGroup, HGroup, \
    spring, Spring
#============= standard library imports ========================
import os
from numpy import loadtxt, polyfit, polyval, hstack, poly1d
from scipy import optimize
#============= local library imports  ==========================
from pychron.spectrometer.spectrometer_device import SpectrometerDevice
from pychron.paths import paths
from pychron.pychron_constants import NULL_STR
from pychron.ui.qt.color_square_editor import ColorSquareEditor


charge = 1.6021764874e-19


class Detector(SpectrometerDevice):
    name = Str
    relative_position = Float(1)

    kind = Str

    deflection = Property(Float(enter_set=True, auto_set=False), depends_on='_deflection')
    _deflection = Float

    deflection_correction_sign=Int(1)

    _deflection_correction_factors = None
    #    intensity = Property(depends_on='spectrometer:intensity_dirty')
    #    intensity = Float
    #    std = Float
    intensity = Str
    std = Str
    intensities = Array
    nstd = Int(10)
    active = Bool(True)

    color = Color
    series_id = Int
    isotope = Str

    isotopes = Property
    color_square = None
    #    @cached_property
    #    def _get_intensity(self):
    #        return self.spectrometer.get_intensity(self.name)
    @on_trait_change('spectrometer:intensity_dirty')
    def _intensity_changed(self, new):
        if new:
            n = self.nstd
            try:
                intensity = new[self.name]
                self.intensities = hstack((self.intensities[-n:], [intensity]))
                self.std = '{:0.5f}'.format(self.intensities.std())

                self.intensity = '{:0.5f}'.format(intensity)
            except KeyError:
                self.intensity = NULL_STR
                self.std = NULL_STR

    def _get_isotopes(self):
        molweights = self.spectrometer.molecular_weights
        return sorted(molweights.keys(), key=lambda x: int(x[2:]))

    def __repr__(self):
        return self.name

    def load(self):
        self.read_deflection()

    def load_deflection_coefficients(self):
        # load deflection correction table
        p = os.path.join(paths.spectrometer_dir,
                         'deflections', self.name)

        x, y = loadtxt(p, delimiter=',', unpack=True)
        y -= y[0]
        coeffs = polyfit(x, y, 1)
        self._deflection_correction_factors = coeffs

    def _set_deflection(self, v):
        self._deflection = v
        self.ask('SetDeflection {},{}'.format(self.name, v))

    def _get_deflection(self):
        return self._deflection

    def read_deflection(self):
        r = self.ask('GetDeflection {}'.format(self.name))
        try:
            self._deflection = float(r)
        except (ValueError, TypeError):
            self._deflection = 0

    def get_deflection_correction(self, current=False):
        if current:
            self.read_deflection()

        de = self._deflection
        dev = polyval(self._deflection_correction_factors, [de])[0]

        return self.deflection_correction_sign*dev

    def map_dac_to_deflection(self, dac):
        c = self._deflection_correction_factors[:]
        c[-1] -= dac
        return optimize.newton(poly1d(c), 1)

    #    def color_square_factory(self, width=10, height=10):
    #        def color_factory(window, editor):
    # #            panel = wx.Panel(window,
    # #                           - 1,
    # #                           size=(width, height)
    # #                           )
    # #            panel.SetBackgroundColour(self.color)
    #            from PySide.QtGui import QWidget, QPalette, QLabel
    #            panel = QLabel()
    #
    #            panel.setFixedWidth(width)
    #            panel.setFixedHeight(height)
    # #            panel.setGeometry(0, 0, width, height)
    #            p = QPalette()
    #            p.setColor(QPalette.Base, self.color)
    #            panel.setPalette(p)
    #            print self.color
    #            return panel
    #
    #        return color_factory

    def intensity_view(self):
        v = View(HGroup(
            Item('color',
                 editor=ColorSquareEditor(),
                 #                             editor=CustomEditor(factory=self.color_square_factory()),
                 width=20,
            ),
            Item('name', style='readonly'),
            #                         Spring(width=25, springy=False),
            spring,
            Item('intensity', style='readonly',
            ),
            Spring(springy=False, width=150),
            Item('std', style='readonly',
            ),
            #                        spring,
            Spring(springy=False, width=100),
            show_labels=False
        )
        )
        return v

    def traits_view(self):
        v = View(VGroup(
            HGroup(
                Item('color',
                     width=40,
                     editor=ColorSquareEditor(),
                     #                                     editor=CustomEditor(factory=self.color_square_factory(width=30))
                ),
                Item('name', style='readonly'),
                spring,

                #                                Item('isotope', width= -75,
                #                                     editor=EnumEditor(name='isotopes')
                #                                     ),
                Item('active', ),
                Item('deflection'),
                show_labels=False
            )
        )
        )

        return v


if __name__ == '__main__':
    d = Detector()


#============= EOF =============================================
#    def calc_deflection(self, ht):
#        ht *= 1000 #accelerating voltage V
#        mass = 39.962
#        L = 1
#        velocity = math.sqrt(2 * charge * ht / mass)
#        flight_time = L / velocity
#        d = 0.1
#        E = -self._deflection / d
#        F = charge * E
#        delta = 0.5 * math.sqrt(F / mass) * flight_time ** 2
