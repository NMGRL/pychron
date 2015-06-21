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
from traits.api import Range, Instance, Bool, \
    Button, Any
# ============= standard library imports ========================
from threading import Event
import cPickle as pickle
import os
import time
# ============= local library imports  ==========================
from pychron.envisage.view_util import open_view
from pychron.managers.manager import Manager
from pychron.graph.graph import Graph
from pychron.spectrometer.ion_optics.coincidence_config import CoincidenceConfig
from pychron.spectrometer.ion_optics.peak_center_config import PeakCenterConfig
from pychron.spectrometer.jobs.coincidence_scan import CoincidenceScan
from pychron.spectrometer.jobs.peak_center import PeakCenter
from pychron.pychron_constants import NULL_STR
from pychron.core.ui.thread import Thread
from pychron.paths import paths
from pychron.core.helpers.isotope_utils import sort_isotopes


class IonOpticsManager(Manager):
    magnet_dac = Range(0.0, 6.0)
    graph = Instance(Graph)
    peak_center_button = Button('Peak Center')
    stop_button = Button('Stop')

    alive = Bool(False)
    spectrometer = Any

    peak_center = Instance(PeakCenter)
    coincidence = Instance(CoincidenceScan)
    peak_center_config = Instance(PeakCenterConfig)
    coincidence_config = Instance(CoincidenceConfig)
    canceled = False

    peak_center_result = None

    def get_mass(self, isotope_key):
        spec = self.spectrometer
        molweights = spec.molecular_weights
        return molweights[isotope_key]

    def set_mftable(self, name=None):
        """
            if mt is None set to the default mftable located at setupfiles/spectrometer/mftable.csv
        :param mt:
        :return:
        """
        if name and name != os.path.splitext(os.path.basename(paths.mftable))[0]:
            self.spectrometer.use_deflection_correction = False
        else:
            self.spectrometer.use_deflection_correction = True

        self.spectrometer.magnet.set_mftable(name)

    def _get_position(self, pos, detector, use_dac=False, update_isotopes=True):
        """
            pos can be str or float
            "Ar40", "39.962", 39.962

            to set in DAC space set use_dac=True
        """
        if pos == NULL_STR:
            return

        spec = self.spectrometer
        mag = spec.magnet

        det = spec.get_detector(detector)
        self.debug('detector {}'.format(det))

        if use_dac:
            dac = pos
        else:
            self.debug('POSITION {} {}'.format(pos, detector))
            if isinstance(pos, str):
                try:
                    pos = float(pos)
                except ValueError:
                    # pos is isotope
                    if update_isotopes:
                        # if the pos is an isotope then update the detectors
                        spec.update_isotopes(pos, detector)
                    pos = self.get_mass(pos)

                mag.mass_change(pos)

            # pos is mass i.e 39.962
            dac = mag.map_mass_to_dac(pos, det.name)

        dac = spec.correct_dac(det, dac)
        return dac

    def get_position(self, *args, **kw):
        kw['update_isotopes'] = False
        return self._get_position(*args, **kw)

    def position(self, pos, detector, *args, **kw):
        dac = self._get_position(pos, detector, *args, **kw)
        mag = self.spectrometer.magnet

        self.info('positioning {} ({}) on {}'.format(pos, dac, detector))
        return mag.set_dac(dac)

    def do_coincidence_scan(self, new_thread=True):

        if new_thread:
            t = Thread(name='ion_optics.coincidence', target=self._coincidence)
            t.start()
            self._thread = t

    def _coincidence(self):
        self.coincidence.get_peak_center()
        self.info('coincidence finished')
        self.spectrometer.restore_integration()

    def setup_coincidence(self):
        pcc = self.coincidence_config
        pcc.dac = self.spectrometer.magnet.dac

        info = pcc.edit_traits()
        if not info.result:
            return

        detector = pcc.detector.name
        isotope = pcc.isotope
        detectors = [d for d in pcc.additional_detectors]
        integration_time = pcc.integration_time

        if pcc.use_nominal_dac:
            center_dac = self.get_position(isotope, detector)
        elif pcc.use_current_dac:
            center_dac = self.spectrometer.magnet.dac
        else:
            center_dac = pcc.dac

        # self.spectrometer.save_integration()
        # self.spectrometer.set_integration(integration_time)

        cs = CoincidenceScan(spectrometer=self.spectrometer,
                             center_dac=center_dac,
                             reference_detector=detector,
                             reference_isotope=isotope,
                             additional_detectors=detectors)
        self.coincidence = cs
        return cs

    def get_center_dac(self, det, iso):
        spec = self.spectrometer
        det = spec.get_detector(det)

        molweights = spec.molecular_weights
        mass = molweights[iso]
        dac = spec.magnet.map_mass_to_dac(mass, det.name)

        # correct for deflection
        return spec.correct_dac(det, dac)

    def do_peak_center(self,
                       save=True,
                       confirm_save=False,
                       warn=False,
                       new_thread=True,
                       message='',
                       on_end=None,
                       timeout=None):
        self.debug('doing pc')

        self.canceled = False
        self.alive = True
        self.peak_center_result = None

        args = (save, confirm_save, warn, message, on_end, timeout)
        if new_thread:
            t = Thread(name='ion_optics.peak_center', target=self._peak_center,
                       args=args)
            t.start()
            self._thread = t
            return t
        else:
            self._peak_center(*args)

    def setup_peak_center(self, detector=None, isotope=None,
                          integration_time=1.04,
                          directions='Increase',
                          center_dac=None, plot_panel=None, new=False,
                          standalone_graph=True, name='', show_label=False):

        self.spectrometer.save_integration()
        self.debug('setup peak center. detector={}, isotope={}'.format(detector, isotope))
        if detector is None or isotope is None:
            self.debug('ask user for peak center configuration')

            pcc = self.peak_center_config
            pcc.dac = self.spectrometer.magnet.dac

            info = pcc.edit_traits()
            if not info.result:
                return
            else:

                detector = pcc.detector.name
                isotope = pcc.isotope
                directions = pcc.directions
                integration_time = pcc.integration_time

                if not pcc.use_current_dac:
                    center_dac = pcc.dac

        self.spectrometer.set_integration_time(integration_time)
        period = int(integration_time * 1000 * 0.9)

        if isinstance(detector, (tuple, list)):
            ref = detector[0]
            detectors = detector
        else:
            ref = detector
            detectors = (ref,)

        if center_dac is None:
            center_dac = self.get_center_dac(ref, isotope)

        self._setup_peak_center(detectors, isotope, period,
                                center_dac, directions, plot_panel, new,
                                standalone_graph, name, show_label)
        return self.peak_center

    def _setup_peak_center(self, detectors, isotope, period,
                           center_dac, directions, plot_panel, new,
                           standalone_graph, name, show_label):

        spec = self.spectrometer

        ref = detectors[0]
        self.reference_detector = ref
        self.reference_isotope = isotope

        if len(detectors) > 1:
            ad = detectors[1:]
        else:
            ad = []

        pc = self.peak_center
        if not pc or new:
            pc = PeakCenter()

        pc.trait_set(center_dac=center_dac,
                     period=period,
                     directions=directions,
                     reference_detector=ref,
                     additional_detectors=ad,
                     reference_isotope=isotope,
                     spectrometer=spec,
                     show_label=show_label)

        self.peak_center = pc
        graph = pc.graph
        graph.name = name
        if plot_panel:
            plot_panel.set_peak_center_graph(graph)
        else:
            graph.close_func = self.close
            if standalone_graph:
                # bind to the graphs close_func
                # self.close is called when graph window is closed
                # use so we can stop the timer
                # set graph window attributes
                graph.window_title = 'Peak Center {}({}) @ {:0.3f}'.format(ref, isotope, center_dac)
                graph.window_width = 300
                graph.window_height = 250
                open_view(graph)

    def _timeout_func(self, timeout, evt):
        st = time.time()
        while not evt.is_set():
            if not self.alive:
                break

            if time.time() - st > timeout:
                self.warning('Peak Centering timed out after {}s'.format(timeout))
                self.cancel_peak_center()
                break

            time.sleep(0.01)

    def _peak_center(self, save, confirm_save, warn, message, on_end, timeout):

        pc = self.peak_center
        spec = self.spectrometer
        ref = self.reference_detector
        isotope = self.reference_isotope

        if timeout:
            evt = Event()
            self.timeout_thread = Thread(target=self._timeout_func, args=(timeout, evt))
            self.timeout_thread.start()

        dac_d = pc.get_peak_center()

        self.peak_center_result = dac_d
        if dac_d:
            args = ref, isotope, dac_d
            self.info('new center pos {} ({}) @ {}'.format(*args))

            det = spec.get_detector(ref)

            dac_a = spec.uncorrect_dac(det, dac_d)
            self.info('converted to axial units {}'.format(dac_a))

            if save:
                save = True
                if confirm_save:
                    msg = 'Update Magnet Field Table with new peak center- {} ({}) @ RefDetUnits= {}'.format(*args)
                    save = self.confirmation_dialog(msg)
                if save:
                    spec.magnet.update_field_table(det, isotope, dac_a, message)
                    spec.magnet.set_dac(dac_d)

        elif not self.canceled:
            msg = 'centering failed'
            if warn:
                self.warning_dialog(msg)
            self.warning(msg)

            # needs to be called on the main thread to properly update
            # the menubar actions. alive=False enables IonOptics>Peak Center
        #        d = lambda:self.trait_set(alive=False)
        # still necessary with qt? and tasks

        if on_end:
            on_end()

        self.trait_set(alive=False)

        if timeout:
            evt.set()

        self.spectrometer.restore_integration()

    def close(self):
        self.cancel_peak_center()

    def cancel_peak_center(self):
        self.alive = False
        self.canceled = True
        self.peak_center.canceled = True
        self.peak_center.stop()
        self.info('peak center canceled')

    # ===============================================================================
    # handler
    # ===============================================================================
    def _coincidence_config_default(self):
        config = None
        p = os.path.join(paths.hidden_dir, 'coincidence_config.p')
        if os.path.isfile(p):
            try:
                with open(p) as rfile:
                    config = pickle.load(rfile)
                    config.detectors = dets = self.spectrometer.detectors
                    config.detector = next((di for di in dets if di.name == config.detector_name), None)

            except Exception, e:
                print 'coincidence config', e

        if config is None:
            config = CoincidenceConfig()
            config.detectors = self.spectrometer.detectors
            config.detector = config.detectors[0]

        keys = self.spectrometer.molecular_weights.keys()
        config.isotopes = sort_isotopes(keys)

        return config

    def _peak_center_config_default(self):
        config = None
        p = os.path.join(paths.hidden_dir, 'peak_center_config.p')
        if os.path.isfile(p):
            try:
                with open(p) as rfile:
                    config = pickle.load(rfile)
                    config.detectors = dets = self.spectrometer.detectors
                    config.detector = next((di for di in dets if di.name == config.detector), None)

            except Exception, e:
                print 'peak center config', e

        if config is None:
            config = PeakCenterConfig()
            config.detectors = self.spectrometer.detectors
            config.detector = config.detectors[0]

        keys = self.spectrometer.molecular_weights.keys()
        config.isotopes = sort_isotopes(keys)

        return config


if __name__ == '__main__':
    io = IonOpticsManager()
    io.configure_traits()

# ============= EOF =============================================
# def _graph_factory(self):
# g = Graph(
#                  container_dict=dict(padding=5, bgcolor='gray'))
#        g.new_plot()
#        return g
#
#    def _graph_default(self):
#        return self._graph_factory()

#     def _detector_default(self):
#         return self.detectors[0]
#     def peak_center_config_view(self):
#         v = View(Item('detector', editor=EnumEditor(name='detectors')),
#                Item('isotope'),
#                Item('dac'),
#                Item('directions'),
#                buttons=['OK', 'Cancel'],
#                kind='livemodal',
#                title='Peak Center'
#                )
#         return v
#    def graph_view(self):
#        v = View(Item('graph', show_label=False, style='custom'),
#                 width=300,
#                 height=500
#                 )
#        return v
#    def peak_center_view(self):
#        v = View(Item('graph', show_label=False, style='custom'),
#                 width=300,
#                 height=500,
#                 handler=self.handler_klass
#                 )
#        return v

#    def traits_view(self):
#        v = View(Item('magnet_dac'),
#                 Item('peak_center_button',
#                      enabled_when='not alive',
#                      show_label=False),
#                 Item('stop_button', enabled_when='alive',
#                       show_label=False),
#
#                 Item('graph', show_label=False, style='custom'),
#
#
#                  resizable=True)
#        return v
#    def _correct_dac(self, det, dac):
#        #        dac is in axial units
#
# #        convert to detector
#        dac *= det.relative_position
#
#        '''
#        convert to axial detector
#        dac_a=  dac_d / relpos
#
#        relpos==dac_detA/dac_axial
#
#        '''
#        #correct for deflection
#        dev = det.get_deflection_correction()
#
#        dac += dev
#
# #        #correct for hv
#        dac *= self.spectrometer.get_hv_correction(current=True)
#        return dac
