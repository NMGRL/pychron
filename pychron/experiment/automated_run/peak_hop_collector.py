# ===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import List, Int, Instance

from pychron.core.helpers.color_generators import colornames
from pychron.experiment.automated_run.data_collector import DataCollector
from pychron.experiment.automated_run.hop_util import generate_hops
from six.moves import zip


class PeakHopCollector(DataCollector):
    """
    Collector class for doing a peak hop measurement. Measure one or more intensities at given mass for ncounts then
    jump magnet to next new mass.
    """

    hops = List
    settling_time = 0
    ncycles = Int
    hop_generator = None

    _was_deflected = False
    _detectors = None

    def set_hops(self, hops):
        self.hops = hops
        self.debug("make new hop generatior")
        self.hop_generator = generate_hops(self.hops)

    def _pre_trigger_hook(self):
        args = self._do_hop()

        if args:
            is_baseline, dets, isos = args
            self._detectors = dets
            return True

    def _iter_hook(self, i):
        return self._iteration(i, detectors=self._detectors)

        # args = self._do_hop()
        #
        # if args:
        #     is_baseline, dets, isos = args
        #     if not is_baseline:
        #         return self._iteration(i, detectors=dets)

    def _do_hop(self):
        """
        is it time for a magnet move
        """
        # from pychron.core.ui.gui import invoke_in_main_thread

        hop = next(self.hop_generator)
        hop_idx = hop["idx"]
        cycle = hop["cycle"]
        is_baseline = hop["is_baseline"]
        dets = hop["detectors"]
        isos = hop["isotopes"]
        defls = hop["deflections"]
        settle = hop["settle"]
        count = hop["count"]
        pdets = hop["protect_detectors"]
        active_dets = hop["active_detectors"]

        current_color = colornames[hop_idx]

        use_dac = False
        positioning = hop["positioning"]
        if positioning:
            if "dac" in positioning:
                use_dac = True
                isotope = positioning["dac"]
                detector = ""
            else:
                detector = positioning["detector"]
                isotope = positioning["isotope"]
        else:
            detector = active_dets[0]
            isotope = isos[0]

        if count == 0:
            self.debug("$$$$$$$$$$$$$$$$$ SETTING is_baseline {}".format(is_baseline))

        arun = self.automated_run
        if is_baseline:
            arun.is_peak_hop = False
            # remember original settings. return to these values after baseline finished
            ocounts = self.measurement_script.ncounts
            arun.measurement_script.increment_series_count(2, 1)
            ocycles = self.plot_panel.ncycles
            pocounts = self.plot_panel.ncounts

            self.debug("START BASELINE MEASUREMENT {} {}".format(isotope, detector))
            arun.measurement_script.baselines(count, mass=isotope, detector=detector)
            self.debug("BASELINE MEASUREMENT COMPLETE")

            arun.measurement_script.increment_series_count(-2, -1)

            self._protect_detectors(pdets, True)
            change = arun.set_magnet_position(
                isotope,
                detector,
                use_dac=use_dac,
                update_detectors=False,
                update_labels=False,
                update_isotopes=True,
                remove_non_active=False,
            )
            if change:
                msg = "delaying {} for detectors to settle after peak hop".format(
                    settle
                )
                arun.wait(settle, msg)
                self.debug(msg)
            self._protect_detectors(pdets, False)

            self.plot_panel._ncounts = pocounts
            self.measurement_script.ncounts = ocounts
            self.plot_panel.ncycles = ocycles
            arun.plot_panel.is_peak_hop = True
            arun.is_peak_hop = True
        else:
            # self.debug('c={} pc={} nc={}'.format(cycle, self.plot_panel.ncycles, self.ncycles))
            if self.plot_panel.ncycles != self.ncycles:
                if cycle >= self.plot_panel.ncycles:
                    self.info(
                        "user termination. measurement iteration executed {}/{} cycles".format(
                            cycle, self.ncycles
                        )
                    )
                    self.stop()
                    return
            elif cycle >= self.ncycles:
                return

            if count == 0:
                zd = list(zip(dets, defls))
                self.debug("Peak hop Detectors={}".format(dets))
                self.debug("Peak hop Deflections={}".format(defls))
                self.debug("Peak hop DeflectionsPairs={}".format(zd))
                # set deflections
                # only set deflections deflections were changed or need changing
                deflect = len([d for d in defls if d is not None])
                if deflect or self._was_deflected:
                    self._was_deflected = False
                    for det, defl in zd:
                        # use the measurement script to set the deflections
                        # this way defaults from the config can be used
                        if defl is not None:
                            self._was_deflected = True
                            arun.set_deflection(det, defl)

                self._protect_detectors(pdets)
                self.debug(
                    "----------------------- HOP {} {}".format(isotope, detector)
                )
                change = arun.set_magnet_position(
                    isotope,
                    detector,
                    update_detectors=False,
                    update_labels=False,
                    update_isotopes=False,
                    # update_isotopes=not is_baseline,
                    remove_non_active=False,
                )

                self._protect_detectors(pdets, False)

                arun.update_detector_isotope_pairing(active_dets, isos)
                if change:
                    g = self.plot_panel.isotope_graph
                    if hop_idx:
                        for d in active_dets:
                            det = arun.get_detector(d)

                            plot = g.get_plot_by_ytitle(
                                "{}{}".format(det.isotope, det.name)
                            )
                            if not plot:
                                plot = g.get_plot_by_ytitle(det.isotope)

                            if plot:
                                scatter = plot.plots[
                                    "data{}".format(self.fit_series_idx)
                                ][0]
                                scatter.color = current_color
                                scatter.outline_color = current_color
                            else:
                                self.debug(
                                    "could not locate det={} iso={}".format(
                                        d, det.isotope
                                    )
                                )

                    try:
                        arun.plot_panel.counts += int(settle)
                    except AttributeError:
                        pass

                    msg = "delaying {} for detectors to settle after peak hop".format(
                        settle
                    )
                    arun.wait(settle, msg)
                    self.debug(msg)

            # self.debug('cycle {} count {} {}'.format(cycle, count, id(self)))
            if self.plot_panel.is_baseline:
                isotope = "{}bs".format(isotope)

            dac = arun.get_current_dac()
            # invoke_in_main_thread(self.plot_panel.trait_set,
            #                       current_cycle='{}({:0.6f}) - {} cyc={} cnt={}'.format(isotope, dac, detector,
            #                                                                             cycle + 1, count + 1),
            #                       current_color=current_color)
            self.plot_panel.trait_set(
                current_cycle="{}({:0.6f}) - {} cyc={} cnt={}".format(
                    isotope, dac, detector, cycle + 1, count + 1
                ),
                current_color=current_color,
            )
        return is_baseline, active_dets, isos

    def _protect_detectors(self, pdets, protect=True):
        for pd in pdets:
            self.automated_run.protect_detector(pd, protect)


# ============= EOF =============================================
