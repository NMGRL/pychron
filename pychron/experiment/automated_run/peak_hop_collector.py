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


def parse_hops(hops, ret=None):
    """
        ret: comma-delimited str. valid values are ``iso``, ``det``, ``defl``
             eg. "iso,det"
    """
    for hopstr, cnt, s in hops:
        for iso, det, defl in split_hopstr(hopstr):
            if ret:
                loc = locals()
                r = [loc[ri.strip()] for ri in ret.split(',')]
                yield r
            else:
                yield iso, det, defl, cnt, s


def split_hopstr(hop):
    for hi in hop.split(','):
        args = map(str.strip, hi.split(':'))
        defl = None
        if len(args) == 3:
            iso, det, defl = args
        else:
            iso, det = args
        yield iso, det, defl


class PeakHopCollector(DataCollector):
    hops = List
    settling_time = 0
    ncycles = Int
    parent = Instance('pychron.experiment.automated_run.automated_run.AutomatedRun')
    _was_deflected = False

    def set_hops(self, hops):
        self.hops = hops
        self.debug('make new hop generatior')
        self.hop_generator = self._generator_hops()

    def _iter_hook(self, con, i):
        if i % 50 == 0:
            self.info('collecting point {}'.format(i))

        args = self._do_hop()
        if args:
            dets, isos = args
            # get the data
            data = self._get_data(dets)

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
        cycle, dets, isos, defls, settle, count = self.hop_generator.next()
        # except StopIteration:
        #     return

        #update the iso/det in plotpanel
        # self.plot_panel.set_detectors(isos, dets)

        detector = dets[0]
        isotope = isos[0]
        # self.debug('c={} pc={} nc={}'.format(cycle, self.plot_panel.ncycles, self.ncycles))
        if self.plot_panel.ncycles!=self.ncycles:
            if cycle >= self.plot_panel.ncycles:
                self.info('user termination. measurement iteration executed {}/{} cycles'.format(cycle, self.ncycles))
                self.stop()
                return
        elif cycle>=self.ncycles:
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
                                            update_isotopes=True,
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

        return dets, isos

    def _generator_hops(self):
        # for c in xrange(self.ncycles):
        c=0
        while 1:
            for hopstr, counts, settle in self.hops:
                isos, dets, defls = zip(*split_hopstr(hopstr))
                for i in xrange(int(counts)):
                    yield c, dets, isos, defls, settle, i
            c+=1




#============= EOF =============================================
