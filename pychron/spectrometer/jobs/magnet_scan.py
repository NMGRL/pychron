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
from __future__ import absolute_import
from pyface.timer.do_later import do_after
from traits.api import Any, Float, DelegatesTo, List, Bool, Property
from traitsui.api import View, Item, EnumEditor, Group, HGroup, spring, ButtonEditor

# ============= standard library imports ========================
from numpy import linspace, hstack, array, Inf
from numpy.core.umath import exp
import random
import time
from threading import Event

# ============= local library imports  ==========================
from .spectrometer_task import SpectrometerTask
from pychron.core.ui.gui import invoke_in_main_thread


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


def psuedo_peak(center, start, stop, step, magnitude=500, peak_width=0.008):
    x = linspace(start, stop, step)
    gaussian = lambda x: magnitude * exp(-(((center - x) / peak_width) ** 2))

    for i, d in enumerate(gaussian(x)):
        if abs(center - x[i]) < peak_width:
            #            d = magnitude
            d = magnitude + magnitude / 50.0 * random.random()
        yield d


class MagnetScan(SpectrometerTask):
    #    graph = Any
    detectors = DelegatesTo("spectrometer")
    integration_time = DelegatesTo("spectrometer")

    reference_detector = Any
    additional_detectors = List
    active_detectors = Property

    start_mass = Float(36)
    stop_mass = Float(40)
    step_mass = Float(1)
    normalize = Bool(True)
    _peak_generator = None
    verbose = False

    def _scan_dac(self, values):
        self.graph.set_x_limits(values[0], values[-1])
        if self.spectrometer.simulation:
            self._peak_generator = psuedo_peak(
                values[len(values) / 2] + 0.001, values[0], values[-1], len(values)
            )
            # self._peak_generator = multi_peak_generator(values)
            self.integration_time = 0.065536

        gen = (vi for vi in values)
        evt = Event()
        intensities = []

        invoke_in_main_thread(self._iter_dac, next(gen), gen, evt, intensities)

        while not evt.isSet():
            time.sleep(0.01)

        # self.integration_time = QTEGRA_INTEGRATION_TIMES[4]
        return True

    def _get_active_detectors(self):
        return [self.reference_detector] + self.additional_detectors

    def _iter_dac(self, di, gen, evt, intensities):
        # self.debug('iter dac {}'.format(di))
        mag = self.spectrometer.magnet
        mag.set_dac(di, verbose=self.verbose, settling_time=self.integration_time * 2)

        d = self._magnet_step_hook()

        self._graph_hook(di, d)
        intensities.append(d)

        try:
            di = next(gen)
        except StopIteration:
            di = None

        if di is not None and self.isAlive():
            p = int(self.integration_time * 1000 * 0.9)
            do_after(p, self._iter_dac, di, gen, evt, intensities)
        else:
            evt.set()

    def _update_graph_data(self, plot, di, intensity, **kw):
        """
        add and scale scans
        """

        def set_data(k, v):
            plot.data.set_data(k, v)

        def get_data(k):
            return plot.data.get_data(k)

        R = None
        r = None
        mi, ma = Inf, -Inf
        for i, v in enumerate(intensity):
            oys = None
            k = "odata{}".format(i)
            if hasattr(plot, k):
                oys = getattr(plot, k)

            oys = array([v]) if oys is None else hstack((oys, v))
            setattr(plot, k, oys)

            if self.normalize:
                if i == 0:
                    # calculate ref range
                    miR = min(oys)
                    maR = max(oys)
                    R = maR - miR
                else:
                    mir = min(oys)
                    mar = max(oys)
                    r = mar - mir

                if r and R:
                    oys = (oys - mir) * R / r + miR

            xs = get_data("x{}".format(i))
            xs = hstack((xs, di))
            set_data("x{}".format(i), xs)
            set_data("y{}".format(i), oys)
            mi, ma = min(mi, min(oys)), max(ma, max(oys))

        self.graph.set_y_limits(min_=mi, max_=ma, pad="0.05", pad_style="upper")

    def _graph_hook(self, di, intensity, **kw):
        graph = self.graph
        if graph:
            plot = graph.plots[0]
            self._update_graph_data(plot, di, intensity)

    def _magnet_step_hook(self):
        spec = self.spectrometer
        ds = [str(self.reference_detector)] + self.additional_detectors
        intensity = spec.get_intensity(ds)
        # print ds,intensity
        # intensity = intensity[1]
        # print self._peak_generator
        # if self._peak_generator:
        #     # print 'asdfas', intensity
        #     v = self._peak_generator.next()
        #     intensity = [v+random.random() for i in range(len(ds))]

        # debug
        # if globalv.experiment_debug:
        # from numpy import array, ones
        #
        # v = self._peak_generator.next()
        # v = array([v])
        #
        # r = ones(len(ds))
        # r = r * v
        # if len(r) > 1:
        #     r[1] *= 0.5
        #     if len(r) > 2:
        #         r[2] *= 0.1
        #
        # intensity = r
        # intensity=[random.random()]
        return intensity

    def _execute(self):
        sm = self.start_mass
        em = self.stop_mass
        stm = self.step_mass

        self.verbose = True
        if abs(sm - em) > stm:
            self._do_scan(sm, em, stm)
            self._alive = False
            self._post_execute()

        self.verbose = False

    def _do_scan(self, sm, em, stm, directions=None, map_mass=True):
        self.debug("_do_scan")
        # default to forward scan
        if directions is None:
            directions = [1]
        elif isinstance(directions, str):
            if directions == "Decrease":
                directions = [-1]
            elif directions == "Oscillate":

                def oscillate():
                    i = 0
                    while 1:
                        if i % 2 == 0:
                            yield 1
                        else:
                            yield -1
                        i += 1

                directions = oscillate()
            else:
                directions = [1]

        spec = self.spectrometer
        mag = spec.magnet
        if map_mass:
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

        for di in directions:
            if not self._alive:
                return

            if di == -1:
                sm, em = em, sm
            values = self._calc_step_values(sm, em, stm)
            if not self._scan_dac(values):
                return

        return True

    def _post_execute(self):
        self.debug("scan finished")

    def _reference_detector_default(self):
        return self.detectors[0]

    def edit_view(self):
        # v = self.traits_view()
        v = View(
            Group(
                Item("reference_detector", editor=EnumEditor(name="detectors")),
                Item("integration_time", label="Integration (s)"),
                label="Magnet Scan",
                show_border=True,
            )
        )

        v.title = self.title
        v.buttons = ["OK", "Cancel"]
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
