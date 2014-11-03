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
import time

from traits.api import List, Int, Instance


#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.experiment.automated_run.data_collector import DataCollector
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.experiment.automated_run.hop_util import generate_hops


class PeakHopCollector(DataCollector):
    hops = List
    settling_time = 0
    ncycles = Int
    parent = Instance('pychron.experiment.automated_run.automated_run.AutomatedRun')
    _was_deflected = False

    def set_hops(self, hops):
        self.hops = hops
        self.debug('make new hop generatior')
        self.hop_generator = generate_hops(self.hops)

    def _iter_hook(self, con, i):
        if i % 50 == 0:
            self.info('collecting point {}'.format(i))

        args = self._do_hop()

        if args:
            is_baseline, dets, isos = args
            if not is_baseline:
                try:
                    data = self._get_data(dets)
                except (AttributeError, TypeError, ValueError), e:
                    self.debug('failed getting data {}'.format(e))
                    return

                con.add_consumable((time.time() - self.starttime,
                                    data, dets, isos, i))
            return True

    def _iter_step(self, data):
        x, k_s, dets, isos, i = data
        self._save_data(x, *k_s)
        self.plot_data(i, x, *k_s)

    def _do_hop(self):
        """
            is it time for a magnet move
        """
        # try:
        cycle, is_baselines, dets, isos, defls, settle, count = self.hop_generator.next()

        # except StopIteration:
        #     return

        #update the iso/det in plotpanel
        # self.plot_panel.set_detectors(isos, dets)

        detector = dets[0]
        isotope = isos[0]
        is_baseline = is_baselines[0]
        if count==0:
            self.debug('$$$$$$$$$$$$$$$$$ SETTING is_baseline {}'.format(is_baseline))

        if is_baseline:
            self.parent.is_peak_hop = False
            #remember original settings. return to these values after baseline finished
            ocounts = self.measurement_script.ncounts
            self.parent.measurement_script._series_count += 2
            self.parent.measurement_script._fit_series_count += 1
            ocycles = self.plot_panel.ncycles
            pocounts = self.plot_panel.ncounts

            self.debug('START BASELINE MEASUREMENT {} {}'.format(isotope, detector))
            self.parent.measurement_script.baselines(count, mass=isotope, detector=detector)
            self.debug('BASELINE MEASUREMENT COMPLETE')

            self.parent.measurement_script._series_count -= 2
            self.parent.measurement_script._fit_series_count -= 1

            change = self.parent.set_magnet_position(isotope, detector,
                                                     update_detectors=False, update_labels=False,
                                            update_isotopes=True,
                                            remove_non_active=False)
            if change:
                msg = 'delaying {} for detectors to settle after peak hop'.format(settle)
                self.parent.wait(settle, msg)
                self.debug(msg)
            self.plot_panel._ncounts = pocounts
            self.measurement_script.ncounts = ocounts
            self.plot_panel.ncycles = ocycles
            self.parent.plot_panel.is_peak_hop = True
            self.parent.is_peak_hop = True


        else:
            # self.debug('c={} pc={} nc={}'.format(cycle, self.plot_panel.ncycles, self.ncycles))
            if self.plot_panel.ncycles != self.ncycles:
                if cycle >= self.plot_panel.ncycles:
                    self.info(
                        'user termination. measurement iteration executed {}/{} cycles'.format(cycle, self.ncycles))
                    self.stop()
                    return
            elif cycle >= self.ncycles:
                return

            if count == 0:
                #set deflections
                # only set deflections deflections were changed or need changing
                deflect = len([d for d in defls if d is not None])
                if deflect or self._was_deflected:
                    self._was_deflected = False
                    for det, defl in zip(dets, defls):
                        #use the measurement script to set the deflections
                        #this way defaults from the config can be used
                        if defl is None:
                            defl = ''
                        else:
                            self._was_deflected = True

                        self.measurement_script.set_deflection(det, defl)

                change = self.parent.set_magnet_position(isotope, detector,
                                                         update_detectors=False, update_labels=False,
                                                update_isotopes=not is_baseline,
                                                remove_non_active=False)
                if change:
                    msg = 'delaying {} for detectors to settle after peak hop'.format(settle)
                    self.parent.wait(settle, msg)
                    self.debug(msg)

            d = self.parent.get_detector(detector)
            # self.debug('cycle {} count {} {}'.format(cycle, count, id(self)))
            if self.plot_panel.is_baseline:
                isotope = '{}bs'.format(isotope)

            invoke_in_main_thread(self.plot_panel.trait_set,
                                  current_cycle='{} cycle={} count={}'.format(isotope, cycle + 1, count + 1),
                                  current_color=d.color)
        return is_baseline, dets, isos

        # def _generator_hops(self):
        #     # for c in xrange(self.ncycles):
        #     c=0
        #     while 1:
        #         for hopstr, counts, settle in self.hops:
        #             is_baselines, isos, dets, defls = zip(*split_hopstr(hopstr))
        #             for i in xrange(int(counts)):
        #                 yield c, is_baselines, dets, isos, defls, settle, i
        #         c+=1


#============= EOF =============================================
