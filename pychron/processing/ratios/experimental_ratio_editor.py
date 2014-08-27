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
from pychron.core.ui import set_qt

set_qt()


# ============= enthought library imports =======================
from traits.api import Float, on_trait_change, Property
from traitsui.api import View, Item, UItem, VGroup, HGroup
# ============= standard library imports ========================
from numpy import linspace
from numpy.random.mtrand import normal
from numpy import random
#============= local library imports  ==========================
from pychron.processing.isotope import Isotope
from pychron.processing.ratios.ratio_editor import RatioEditor


def gen_data(b, m, e, n=50):
    xs = linspace(15, 100, n)
    ys = m * xs + b
    if e:
        ys += normal(scale=e, size=n)

    # ys[6] = ys[6] + 10
    return xs, ys


def generate_test_data(nslope, nintercept, nnoise, dslope, dintercept, dnoise):
    random.seed(123456789)
    xs, ys = gen_data(nintercept, nslope, nnoise)
    a40 = Isotope(name='Ar40', xs=xs, ys=ys)

    xs, ys = gen_data(dintercept, dslope, dnoise)
    a39 = Isotope(name='Ar39', xs=xs, ys=ys)

    return dict(Ar40=a40, Ar39=a39)


class ExperimentalRatioEditor(RatioEditor):
    nslope = Float(-2)
    dslope = Float(0.25)

    nintercept = Float(500)
    dintercept = Float(10)

    nnoise = Float(0, enter_set=True, auto_set=False)
    dnoise = Float(0, enter_set=True, auto_set=False)

    percent_diff = Property(depends_on='ratio_intercept, intercept_ratio')

    def _get_percent_diff(self):
        try:
            r = (self.ratio_intercept - self.intercept_ratio) / self.intercept_ratio * 100
        except ZeroDivisionError:
            r = 'NaN'

        return r

    @on_trait_change('nslope, nintercept, nnoise, dslope, dintercept, dnoise')
    def update(self):
        self._gen_data()
        self.refresh_plot()

    def _gen_data(self):
        self.data = generate_test_data(self.nslope,
                                       self.nintercept,
                                       self.nnoise,
                                       self.dslope,
                                       self.dintercept,
                                       self.dnoise)

    def setup(self):
        self._gen_data()
        self.setup_graph()

    def traits_view(self):
        v = View(UItem('graph', style='custom'),
                 VGroup(

                     HGroup(Item('nslope'), Item('nintercept'), Item('nnoise')),
                     HGroup(Item('dslope'), Item('dintercept'), Item('dnoise')),

                     Item('time_zero_offset'),
                     Item('intercept_ratio', style='readonly'),
                     Item('ratio_intercept', style='readonly'),
                     Item('percent_diff', style='readonly')))
        return v


if __name__ == '__main__':
    re = ExperimentalRatioEditor()
    re.setup()
    re.configure_traits()
#============= EOF =============================================



