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

import random

# ============= standard library imports ========================
from numpy import linspace
from numpy.core.umath import exp

# ============= enthought library imports =======================
from traitsui.api import View, Item, EnumEditor, Group, HGroup, spring, ButtonEditor

# ============= local library imports  ==========================
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
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


def pseudo_peak(center, start, stop, step, magnitude=500, peak_width=0.004, channels=1):
    x = linspace(start, stop, step)
    gaussian = lambda x: magnitude * exp(-(((center - x) / peak_width) ** 2))

    for i, d in enumerate(gaussian(x)):
        if abs(center - x[i]) < peak_width:
            #            d = magnitude
            # for j in xrange(channels):
            d = magnitude + magnitude / 50.0 * random.random()

        yield [d * (j + 1) for j in range(channels)]


class AccelVoltageSweep(BaseSweep):
    def _step(self, v):
        self.spectrometer.source.nominal_hv = v


class MagnetSweep(BaseSweep):
    _peak_generator = None

    def _make_pseudo(self, values, channels):
        self._peak_generator = pseudo_peak(
            values[len(values) // 2] + 0.001,
            values[0],
            values[-1],
            len(values),
            channels,
        )

    def _step_intensity(self):
        if self._peak_generator:
            resp = next(self._peak_generator)
        else:
            resp = super(MagnetSweep, self)._step_intensity()
        return resp

    def _step(self, v):
        self.spectrometer.magnet.set_dac(
            v,
            verbose=self.verbose,
            settling_time=0,
            # settling_time=self.integration_time * 2,
            use_dac_changed=False,
        )

        if hasattr(self.spectrometer, "trigger_acq"):
            self.spectrometer.trigger_acq()

        self.spectrometer.settle()

    def _do_sweep(self, sm, em, stm, directions=None, map_mass=True):
        if map_mass:
            spec = self.spectrometer
            mag = spec.magnet
            detname = self.reference_detector.name
            ds = spec.correct_dac(
                self.reference_detector, mag.map_mass_to_dac(sm, detname)
            )
            de = spec.correct_dac(
                self.reference_detector, mag.map_mass_to_dac(em, detname)
            )

            massdev = abs(sm - em)
            dacdev = abs(ds - de)

            stm = stm / float(massdev) * dacdev
            sm, em = ds, de

        return super(MagnetSweep, self)._do_sweep(sm, em, stm, directions)

    def edit_view(self):
        v = okcancel_view(
            Group(
                Item("reference_detector", editor=EnumEditor(name="detectors")),
                Item("integration_time", label="Integration (s)"),
                label="Magnet Scan",
                show_border=True,
            ),
            title=self.title,
        )

        return v

    def traits_view(self):
        v = View(
            Group(
                Item("reference_detector", editor=EnumEditor(name="detectors")),
                Item(
                    "start_value", label="Start Mass", tooltip="Start scan at this mass"
                ),
                Item(
                    "stop_value",
                    label="Stop Mass",
                    tooltip="Stop scan when magnet reaches this mass",
                ),
                Item(
                    "step_value",
                    label="Step Mass",
                    tooltip="Step from Start to Stop by this amount",
                ),
                Item("integration_time", label="Integration (s)"),
                HGroup(
                    spring,
                    Item(
                        "execute_button",
                        editor=ButtonEditor(label_value="execute_label"),
                        show_label=False,
                    ),
                ),
                label="Magnet Scan",
                show_border=True,
            )
        )

        return v


# ============= EOF =============================================
