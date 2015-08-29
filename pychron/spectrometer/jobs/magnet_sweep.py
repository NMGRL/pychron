# ===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Any, Float, DelegatesTo, List, Bool, Property
from traitsui.api import View, Item, EnumEditor, Group, HGroup, spring, ButtonEditor
from pyface.timer.do_later import do_after
# ============= standard library imports ========================
from numpy import linspace, hstack, array, Inf
from numpy.core.umath import exp
import random
import time
# ============= local library imports  ==========================
from pychron.spectrometer.jobs.sweep import BaseSweep


def multi_peak_generator(values):
    for v in values:
        m = 0.1
        if 4.8 <= v <= 5.2:
            m = 3
        elif 5.5 <= v <= 5.8:
            m = 9
        elif 6.1 <= v <= 7:
            m = 6

        yield m + random.random() / 5.0


def pseudo_peak(center, start, stop, step, magnitude=500, peak_width=0.008):
    x = linspace(start, stop, step)
    gaussian = lambda x: magnitude * exp(-((center - x) / peak_width) ** 2)

    for i, d in enumerate(gaussian(x)):
        if abs(center - x[i]) < peak_width:
            #            d = magnitude
            d = magnitude + magnitude / 50.0 * random.random()
        yield d


class MagnetSweep(BaseSweep):
    start_mass = Float(36)
    stop_mass = Float(40)
    step_mass = Float(1)

    # _peak_generator = None
    def _make_pseudo(self, values):
        self._peak_generator = pseudo_peak(values[len(values) / 2] + 0.001, values[0], values[-1], len(values))

    def _step(self, v):
        self.spectrometer.magnet.set_dac(v, verbose=self.verbose)

    def _execute(self):
        sm = self.start_mass
        em = self.stop_mass
        stm = self.step_mass

        self.verbose = True
        if abs(sm - em) > stm:
            self._do_sweep(sm, em, stm)
            self._alive = False
            self._post_execute()

        self.verbose = False

    def _do_sweep(self, sm, em, stm, directions=None, map_mass=True):
        if map_mass:
            spec = self.spectrometer
            mag = spec.magnet
            detname = self.reference_detector.name
            ds = spec.correct_dac(self.reference_detector,
                                  mag.map_mass_to_dac(sm, detname))
            de = spec.correct_dac(self.reference_detector,
                                  mag.map_mass_to_dac(em, detname))

            massdev = abs(sm - em)
            dacdev = abs(ds - de)

            stm = stm / float(massdev) * dacdev
            sm, em = ds, de

        return super(MagnetSweep, self)._do_sweep(sm, em, stm, directions)

    def edit_view(self):
        v = View(Group(Item('reference_detector', editor=EnumEditor(name='detectors')),
                       Item('integration_time', label='Integration (s)'),
                       label='Magnet Scan',
                       show_border=True),
                 title=self.title,
                 buttons=['OK', 'Cancel'], )

        return v

    def traits_view(self):
        v = View(
            Group(
                Item('reference_detector', editor=EnumEditor(name='detectors')),
                Item('start_mass', label='Start Mass', tooltip='Start scan at this mass'),
                Item('stop_mass', label='Stop Mass', tooltip='Stop scan when magnet reaches this mass'),
                Item('step_mass', label='Step Mass', tooltip='Step from Start to Stop by this amount'),
                Item('integration_time', label='Integration (s)'),
                HGroup(spring, Item('execute_button', editor=ButtonEditor(label_value='execute_label'),
                                    show_label=False)),
                label='Magnet Scan',
                show_border=True))

        return v

# ============= EOF =============================================
