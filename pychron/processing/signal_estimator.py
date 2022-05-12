# ===============================================================================
# Copyright 2022 ross
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
import math

from pychron.loggable import Loggable
from traits.api import Float, Instance, Enum, on_trait_change, Int
from traitsui.api import View, Item, TextEditor, VGroup, HGroup

K = 39.0983
O = 15.9994
K2O_MOLECULAR_WEIGHT = K * 2 + O
K40_KTOT = 1.167e-4
LAMBDA_EC = 5.543e-10  # 1/a
LAMBDA_T = 5.81e-11  # 1/a


class SignalEstimator(Loggable):
    radius = Int  # um
    height = Float  # um
    shape = Enum('sphere', 'cylinder')
    approx_age = Float(36)  # in ma
    k2o = Float(8.75)
    density = Float(2.52)  # g/cm3
    sensitivity = Float(0.00000000000000006)  # mols/fA

    rad40 = Float
    mass = Float
    volume = Float

    j = Float
    j_per_hour = Float(0.002)
    hours = Float

    target_ratio = Float(10)

    def get_volume(self):
        r = self.radius / 10000
        if self.shape == 'sphere':
            v = 4 / 3 * math.pi * r ** 3
        elif self.shape == 'cylinder':
            v = math.pi * r ** 2 * self.height / 10000
        self.volume = v
        return v

    def get_mass(self):
        return self.get_volume() * self.density

    @on_trait_change('radius,height,shape,k2o,density,approx_age,target_ratio,j_per_hour')
    def calculate(self):
        """
        given grain size, approximate age, k2o

        :return:
        """
        self.mass = mass = self.get_mass()
        mass_k2o = mass * self.k2o / 100
        mols_k2o = mass_k2o / K2O_MOLECULAR_WEIGHT
        mols_k = mols_k2o * 2
        mols_k40 = mols_k * K40_KTOT
        t = self.approx_age * 1e6
        rad40 = mols_k40 * LAMBDA_EC / LAMBDA_T * (math.exp(t * LAMBDA_T) - 1)
        self.rad40 = rad40 / self.sensitivity

        self.j = (math.exp(t * LAMBDA_T) - 1) / self.target_ratio
        self.hours = self.j / self.j_per_hour

    def traits_view(self):
        v = View(VGroup(
                        Item('shape'),
                        Item('radius', label='Radius (um)'),
                        Item('height', label='Height (um)', visible_when='shape=="cylinder"'),
                        Item('k2o', format_str='%0.2f', label='K2O (wt %)'),
                        Item('approx_age', format_str='%0.3f', label='Approx Age (ma)'),
                        show_border=True),
                 Item('sensitivity', format_str='%0.3e', label='Sensitivity (mol/fA)'),
                 VGroup(Item('j_per_hour'),
                        HGroup(Item('target_ratio'),
                               Item('hours', format_str='%0.2f', editor=TextEditor(read_only=True))),
                        show_border=True),
                 VGroup(
                     Item('volume', format_str='%0.3e', label='Volume (cm3)'),
                     Item('density', format_str='%0.2f', label='Density (g/cm3)'),
                     Item('mass', format_str='%0.3e', label='Mass (g)'),
                     show_border=True),
                 VGroup(Item('rad40',
                             label='40Ar* (fA)',
                             format_str='%0.3f', editor=TextEditor(read_only=True)),
                        show_border=True),
                 width=500,
                 resizable=True,
                 title='Signal Estimator',
                 buttons=['OK'])
        return v


if __name__ == '__main__':
    c = SignalEstimator()
    c.configure_traits()
# ============= EOF =============================================
