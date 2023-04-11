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
from __future__ import print_function

import os

import six.moves.cPickle as pickle
from traits.api import Range, Instance, Bool, Button, Any

from pychron.core.helpers.isotope_utils import sort_isotopes
from pychron.core.ui.thread import Thread
from pychron.graph.graph import Graph
from pychron.managers.manager import Manager
from pychron.paths import paths
from pychron.pychron_constants import NULL_STR
from pychron.spectrometer.base_detector import BaseDetector
from pychron.spectrometer.base_spectrometer import NoIntensityChange
from pychron.spectrometer.ion_optics.coincidence_config import CoincidenceConfig
from pychron.spectrometer.ion_optics.peak_center_config import PeakCenterConfigurer
from pychron.spectrometer.jobs.coincidence import Coincidence
from pychron.spectrometer.jobs.peak_center import PeakCenter, AccelVoltagePeakCenter


class MFTableCTX(object):
    def __init__(self, manager, mftable):
        self._manager = manager
        self._opath = manager.spectrometer.magnet.get_field_table_path()
        self._mftable = mftable

    def __enter__(self):
        self._manager.set_mftable(self._mftable)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._manager.set_mftable(self._opath)


class IonOpticsManager(Manager):
    reference_detector = Instance(BaseDetector)
    reference_isotope = Any

    magnet_dac = Range(0.0, 6.0)
    graph = Instance(Graph)
    peak_center_button = Button("Peak Center")
    stop_button = Button("Stop")

    alive = Bool(False)
    spectrometer = Any

    peak_center = Instance(PeakCenter)
    coincidence = Instance(Coincidence)
    peak_center_config = Instance(PeakCenterConfigurer)
    # coincidence_config = Instance(CoincidenceConfig)
    canceled = False

    peak_center_result = None

    _centering_thread = None

    def close(self):
        self.cancel_peak_center()

    def cancel_peak_center(self):
        self.alive = False
        self.canceled = True
        self.peak_center.canceled = True
        self.peak_center.stop()
        self.info("peak center canceled")

    def get_mass(self, isotope_key):
        spec = self.spectrometer
        molweights = spec.molecular_weights
        return molweights[isotope_key]

    def mftable_ctx(self, mftable):
        return MFTableCTX(self, mftable)

    def set_mftable(self, name=None):
        """
            if mt is None set to the default mftable located at setupfiles/spectrometer/mftable.csv
        :param mt:
        :return:
        """
        if name == "ic_mftable":
            self.spectrometer.use_deflection_correction = False
        else:
            self.spectrometer.use_deflection_correction = True

        self.spectrometer.magnet.set_mftable(name)

    def get_position(self, *args, **kw):
        kw["update_isotopes"] = False
        return self._get_position(*args, **kw)

    def av_position(self, pos, detector, *args, **kw):
        av = self._get_av_position(pos, detector)
        self.spectrometer.source.set_hv(av)
        self.info("positioning {} ({}) on {}".format(pos, av, detector))
        return av

    def position(self, pos, detector, use_af_demag=True, *args, **kw):
        dac = self._get_position(pos, detector, *args, **kw)
        mag = self.spectrometer.magnet

        self.info("positioning {} ({}) on {}".format(pos, dac, detector))
        return mag.set_dac(dac, use_af_demag=use_af_demag)

    def do_coincidence_scan(self, new_thread=True):
        if new_thread:
            t = Thread(name="ion_optics.coincidence", target=self._coincidence)
            t.start()
            self._centering_thread = t

    def setup_coincidence(self):
        pcc = self.coincidence_config
        pcc.dac = self.spectrometer.magnet.dac

        info = pcc.edit_traits()
        if not info.result:
            return

        detector = pcc.detector
        isotope = pcc.isotope
        detectors = [d for d in pcc.additional_detectors]
        # integration_time = pcc.integration_time

        if pcc.use_nominal_dac:
            center_dac = self.get_position(isotope, detector)
        elif pcc.use_current_dac:
            center_dac = self.spectrometer.magnet.dac
        else:
            center_dac = pcc.dac

        # self.spectrometer.save_integration()
        # self.spectrometer.set_integration(integration_time)

        cs = Coincidence(
            spectrometer=self.spectrometer,
            center_dac=center_dac,
            reference_detector=detector,
            reference_isotope=isotope,
            additional_detectors=detectors,
        )
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

    def do_peak_center(
        self,
        save=True,
        confirm_save=False,
        warn=False,
        new_thread=True,
        message="",
        on_end=None,
        timeout=None,
    ):
        self.debug("doing pc")

        self.canceled = False
        self.alive = True
        self.peak_center_result = None

        args = (save, confirm_save, warn, message, on_end, timeout)
        if new_thread:
            t = Thread(
                name="ion_optics.peak_center", target=self._peak_center, args=args
            )
            t.start()
            self._centering_thread = t
            return t
        else:
            self._peak_center(*args)

    def setup_peak_center(
        self,
        detector=None,
        isotope=None,
        integration_time=1.04,
        directions="Increase",
        center_dac=None,
        name="",
        show_label=False,
        window=0.015,
        step_width=0.0005,
        min_peak_height=1.0,
        percent=80,
        deconvolve=None,
        use_interpolation=False,
        interpolation_kind="linear",
        dac_offset=None,
        calculate_all_peaks=False,
        config_name=None,
        use_configuration_dac=True,
        new=False,
        update_others=True,
        plot_panel=None,
    ):
        if deconvolve is None:
            n_peaks, select_peak = 1, 1

        use_dac_offset = False
        if dac_offset is not None:
            use_dac_offset = True

        spec = self.spectrometer
        pcconfig = self.peak_center_config

        spec.save_integration()
        self.debug(
            "setup peak center. detector={}, isotope={}".format(detector, isotope)
        )

        pcc = None
        dataspace = "dac"
        use_accel_voltage = False
        use_extend = False
        self._setup_config()
        if config_name:
            pcconfig.load()
            pcconfig.active_name = config_name
            pcc = pcconfig.active_item

        elif detector is None or isotope is None:
            self.debug("ask user for peak center configuration")

            pcconfig.load()
            if config_name:
                pcconfig.active_name = config_name

            info = pcconfig.edit_traits()

            if not info.result:
                return
            else:
                pcc = pcconfig.active_item

        if pcc:
            if not detector:
                detector = pcc.active_detectors

            if not isotope:
                isotope = pcc.isotope

            directions = pcc.directions
            integration_time = pcc.integration_time

            dataspace = pcc.dataspace
            use_accel_voltage = pcc.use_accel_voltage
            use_extend = pcc.use_extend
            window = pcc.window
            min_peak_height = pcc.min_peak_height
            step_width = pcc.step_width
            percent = pcc.percent
            use_interpolation = pcc.use_interpolation
            interpolation_kind = pcc.interpolation_kind
            n_peaks = pcc.n_peaks
            select_peak = pcc.select_n_peak
            use_dac_offset = pcc.use_dac_offset
            dac_offset = pcc.dac_offset
            calculate_all_peaks = pcc.calculate_all_peaks
            update_others = pcc.update_others
            if not pcc.use_mftable_dac and center_dac is None and use_configuration_dac:
                center_dac = pcc.dac

        spec.set_integration_time(integration_time)
        period = int(integration_time * 1000 * 0.9)

        if not isinstance(detector, (tuple, list)):
            detector = (detector,)

        ref = spec.get_detector(detector[0])

        if center_dac is None:
            center_dac = self.get_center_dac(ref, isotope)

        # if mass:
        #     mag = spec.magnet
        #     center_dac = mag.map_mass_to_dac(mass, ref)
        #     low = mag.map_mass_to_dac(mass - window / 2., ref)
        #     high = mag.map_mass_to_dac(mass + window / 2., ref)
        #     window = high - low
        #     step_width = abs(mag.map_mass_to_dac(mass + step_width, ref) - center_dac)

        if len(detector) > 1:
            ad = detector[1:]
        else:
            ad = []

        pc = self.peak_center
        klass = AccelVoltagePeakCenter if use_accel_voltage else PeakCenter
        if (
            not pc
            or new
            or (use_accel_voltage and not isinstance(pc, AccelVoltagePeakCenter))
        ):
            pc = klass()

        pc.trait_set(
            center_dac=center_dac,
            dataspace=dataspace,
            use_accel_voltage=use_accel_voltage,
            use_extend=use_extend,
            period=period,
            window=window,
            percent=percent,
            min_peak_height=min_peak_height,
            step_width=step_width,
            directions=directions,
            reference_detector=ref,
            additional_detectors=ad,
            reference_isotope=isotope,
            spectrometer=spec,
            show_label=show_label,
            use_interpolation=use_interpolation,
            interpolation_kind=interpolation_kind,
            n_peaks=n_peaks,
            select_peak=select_peak,
            use_dac_offset=use_dac_offset,
            dac_offset=dac_offset,
            calculate_all_peaks=calculate_all_peaks,
            update_others=update_others,
        )

        graph = pc.graph
        graph.name = name
        if plot_panel:
            plot_panel.set_peak_center_graph(graph)

        self.peak_center = pc
        self.reference_detector = ref
        self.reference_isotope = isotope

        return self.peak_center

    def backup_mftable(self):
        self.spectrometer.magnet.field_table.backup()

    # private
    def _setup_config(self):
        config = self.peak_center_config
        config.detectors = self.spectrometer.detector_names
        keys = list(self.spectrometer.molecular_weights.keys())
        config.isotopes = sort_isotopes(keys)
        config.integration_times = self.spectrometer.integration_times

    # def _get_peak_center_config(self, config_name):
    #     if config_name is None:
    #         config_name = 'default'
    #
    #     config = self.peak_center_config.get(config_name)
    #
    #     config.detectors = self.spectrometer.detectors_names
    #     if config.detector_name:
    #         config.detector = next((di for di in config.detectors if di == config.detector_name), None)
    #
    #     if not config.detector:
    #         config.detector = config.detectors[0]
    #
    #     keys = self.spectrometer.molecular_weights.keys()
    #     config.isotopes = sort_isotopes(keys)
    #     config.integration_times = self.spectrometer.integration_times
    #     return config

    # def _timeout_func(self, timeout, evt):
    #     st = time.time()
    #     while not evt.is_set():
    #         if not self.alive:
    #             break
    #
    #         if time.time() - st > timeout:
    #             self.warning('Peak Centering timed out after {}s'.format(timeout))
    #             self.cancel_peak_center()
    #             break
    #
    #         time.sleep(0.01)

    def _peak_center(self, save, confirm_save, warn, message, on_end, timeout):
        pc = self.peak_center
        spec = self.spectrometer
        ref = self.reference_detector
        isotope = self.reference_isotope

        try:
            center_value = pc.get_peak_center()
        except NoIntensityChange as e:
            self.warning("Peak Centering failed. No Intensity change. {}".format(e))
            center_value = None

        self.peak_center_result = center_value
        if center_value:
            det = spec.get_detector(ref)

            if pc.use_accel_voltage:
                args = ref, isotope, center_value
            else:
                dac_a = spec.uncorrect_dac(det, center_value)
                self.info("dac uncorrected for HV and deflection {}".format(dac_a))
                args = ref, isotope, dac_a
                self.adjusted_peak_center_result = dac_a

            self.info("new center pos {} ({}) @ {}".format(*args))
            if save:
                if confirm_save:
                    msg = "Update Magnet Field Table with new peak center- {} ({}) @ RefDetUnits= {}".format(
                        *args
                    )
                    if pc.use_accel_voltage:
                        msg = "Update Accel Voltage Table with new peak center- {} ({}) @ RefDetUnits= {}".format(
                            *args
                        )

                    save = self.confirmation_dialog(msg)

                if save:
                    if pc.use_accel_voltage:
                        spec.source.update_field_table(
                            det, isotope, center_value, message
                        )
                    else:
                        spec.magnet.update_field_table(
                            det, isotope, dac_a, message, update_others=pc.update_others
                        )
                        spec.magnet.set_dac(dac_a)

        elif not self.canceled:
            msg = "centering failed"
            if warn:
                self.warning_dialog(msg)
            self.warning(msg)

            # needs to be called on the main thread to properly update
            # the menubar actions. alive=False enables IonOptics>Peak Center
        # d = lambda:self.trait_set(alive=False)
        # still necessary with qt? and tasks

        if on_end:
            on_end()

        self.trait_set(alive=False)

        self.spectrometer.restore_integration()

    def _get_av_position(self, pos, detector, update_isotopes=True):
        self.debug("AV POSITION {} {}".format(pos, detector))
        spec = self.spectrometer
        if not isinstance(detector, str):
            detector = detector.name

        if isinstance(pos, str):
            try:
                pos = float(pos)
            except ValueError:
                # pos is isotope
                if update_isotopes:
                    # if the pos is an isotope then update the detectors
                    spec.update_isotopes(pos, detector)
                pos = self.get_mass(pos)

        # pos is mass i.e 39.962
        av = spec.source.map_mass_to_hv(pos, detector)
        return av

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

        if isinstance(detector, str):
            det = spec.get_detector(detector)
        else:
            det = detector

        self.debug("detector {}".format(det))

        if use_dac:
            dac = pos
        else:
            self.debug("POSITION {} {}".format(pos, detector))
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
            print("det is", det)
            dac = mag.map_mass_to_dac(pos, det.name)

        dac = spec.correct_dac(det, dac)
        return dac

    def _coincidence(self):
        self.coincidence.get_peak_center()
        self.info("coincidence finished")
        self.spectrometer.restore_integration()

    # ===============================================================================
    # handler
    # ===============================================================================
    def _coincidence_config_default(self):
        config = None
        p = os.path.join(paths.hidden_dir, "coincidence_config.p")
        if os.path.isfile(p):
            try:
                with open(p) as rfile:
                    config = pickle.load(rfile)
                    config.detectors = dets = self.spectrometer.detectors
                    config.detector = next(
                        (di for di in dets if di.name == config.detector_name), None
                    )

            except Exception as e:
                print("coincidence config", e)

        if config is None:
            config = CoincidenceConfig()
            config.detectors = self.spectrometer.detectors
            config.detector = config.detectors[0]

        keys = list(self.spectrometer.molecular_weights.keys())
        config.isotopes = sort_isotopes(keys)

        return config

    def _peak_center_config_default(self):
        config = PeakCenterConfigurer()
        return config

        # def _peak_center_config_default(self):
        #     config = None
        #     p = os.path.join(paths.hidden_dir, 'peak_center_config.p')
        #     if os.path.isfile(p):
        #         try:
        #             with open(p) as rfile:
        #                 config = pickle.load(rfile)
        #                 config.detectors = dets = self.spectrometer.detectors
        #                 config.detector = next((di for di in dets if di.name == config.detector_name), None)
        #
        #         except Exception, e:
        #             print 'peak center config', e
        #
        #     if config is None:
        #         config = PeakCenterConfig()
        #         config.detectors = self.spectrometer.detectors
        #         config.detector = config.detectors[0]
        #
        #     keys = self.spectrometer.molecular_weights.keys()
        #     config.isotopes = sort_isotopes(keys)
        #
        #     return config


if __name__ == "__main__":
    io = IonOpticsManager()
    io.configure_traits()

# ============= EOF =============================================
# def _graph_factory(self):
# g = Graph(
# container_dict=dict(padding=5, bgcolor='gray'))
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
