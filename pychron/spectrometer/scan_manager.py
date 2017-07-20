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
import os
import time
from Queue import Queue
from threading import Thread

import yaml
from pyface.timer.do_later import do_later
from traits.api import Instance, Any, DelegatesTo, List, Property, \
    Bool, Button, String, cached_property, \
    Str

from pychron.core.ui.preference_binding import bind_preference
from pychron.graph.tools.data_tool import DataTool, DataToolOverlay
from pychron.managers.data_managers.csv_data_manager import CSVDataManager
from pychron.managers.stream_graph_manager import StreamGraphManager
from pychron.paths import paths
from pychron.pychron_constants import NULL_STR
from pychron.spectrometer.base_detector import BaseDetector
from pychron.spectrometer.graph.spectrometer_scan_graph import SpectrometerScanGraph
from pychron.spectrometer.jobs.dac_scanner import DACScanner
from pychron.spectrometer.jobs.mass_scanner import MassScanner
from pychron.spectrometer.jobs.rise_rate import RiseRate
from pychron.spectrometer.readout_view import ReadoutView


class ScanManager(StreamGraphManager):
    spectrometer = Any
    ion_optics_manager = Instance(
        'pychron.spectrometer.ion_optics.ion_optics_manager.IonOpticsManager')

    readout_view = Instance(ReadoutView)

    integration_time = DelegatesTo('spectrometer')
    spectrometer_configurations = DelegatesTo('spectrometer')
    spectrometer_configuration = DelegatesTo('spectrometer')
    set_spectrometer_configuration = Button
    set_magnet_position_button = Button

    detectors = DelegatesTo('spectrometer')
    detector_names = DelegatesTo('spectrometer')

    detector = Property(Instance(BaseDetector), depends_on='_detector')
    _detector = Str

    magnet = DelegatesTo('spectrometer')
    source = DelegatesTo('spectrometer')
    dac_scanner = Instance(DACScanner)
    mass_scanner = Instance(MassScanner)
    rise_rate = Instance(RiseRate)
    isotope = String
    isotopes = Property

    scan_enabled = Bool(True)
    use_default_scan_settings = Bool
    default_isotope = Str
    default_detector = Str

    use_detector_safety = Bool(True)

    _consuming = False
    queue = None
    timer = None

    use_log_events = Bool
    log_events_enabled = False
    _valve_event_list = List
    _prev_signals = None
    _no_intensity_change_cnt = 0
    _suppress_isotope_change = False

    settings_name = 'scan_settings'

    def _bind_listeners(self, remove=False):
        self.on_trait_change(self._update_magnet, 'magnet:dac_changed',
                             remove=remove)
        self.on_trait_change(self._toggle_detector, 'detectors:active',
                             remove=remove)

    def prepare_destroy(self):
        self.stop_scan()
        self.log_events_enabled = False
        self._bind_listeners(remove=True)

        plot = self.graph.plots[0]
        plot.value_range.on_trait_change(self._update_graph_limits,
                                         '_low_value, _high_value', remove=True)
        self.readout_view.stop()

        self.mass_scanner.dump()
        self.dac_scanner.dump()

    def stop(self):
        self.prepare_destroy()

    def stop_scan(self):
        self.dump_settings()
        self._stop_timer()

        # clear our graph settings so on reopen events will fire
        # del self.graph_scale
        # del self._graph_ymax
        # del self._graph_ymin
        # del self.graph_y_auto
        # del self.graph_scan_width

    def activate(self):
        self.bind_preferences()

        self.load_event_marker_config()
        self.setup_scan()
        self.readout_view.start()

    def load_event_marker_config(self):
        if self.use_log_events:
            p = os.path.join(paths.spectrometer_dir, 'scan.yaml')
            if not os.path.isfile(p):
                if self.confirmation_dialog('No scan.yaml file found. '
                                            'Required to configure which valves trigger adding a marker.\n'
                                            'Would you like to add a blank scan.yaml file?'):
                    with open(p, 'w') as wfile:
                        yaml.dump({'valves': []}, wfile,
                                  default_flow_style=False)

            if os.path.isfile(p):
                with open(p, 'r') as rfile:
                    yd = yaml.load(rfile)
                    self._valve_event_list = yd['valves']

    def bind_preferences(self):
        pref_id = 'pychron.spectrometer'
        bind_preference(self, 'use_detector_safety',
                        '{}.use_detector_safety'.format(pref_id))
        bind_preference(self, 'use_log_events',
                        '{}.use_log_events'.format(pref_id))
        bind_preference(self, 'use_vertical_markers',
                        '{}.use_vertical_markers'.format(pref_id))

        bind_preference(self, 'use_default_scan_settings', '{}.use_default_scan_settings'.format(pref_id))
        bind_preference(self, 'default_detector', '{}.default_detector'.format(pref_id))
        bind_preference(self, 'default_isotope', '{}.default_isotope'.format(pref_id))

    def setup_scan(self):
        # force update
        self.load_settings()

        self._reset_graph()
        self._graph_scan_width_changed()

        self._detector_changed(None, self.detector)
        self._isotope_changed(None, self.isotope)

        # bind
        self._bind_listeners()

        # force position update
        self._set_position()
        self.log_events_enabled = True

    def add_spec_event_marker(self, msg, mode=None, extra=None, bgcolor='white'):
        if self.use_log_events and self.log_events_enabled:
            if mode == 'valve' and self._valve_event_list:
                # check valve name is configured to be displayed
                if extra not in self._valve_event_list:
                    return

            self.debug('add spec event marker. {}'.format(msg))
            self.graph.add_visual_marker(msg, bgcolor)

    def setup_populate_mftable(self):
        from pychron.spectrometer.mftable_config import MFTableConfig
        pcc = self.ion_optics_manager.peak_center_config
        pcc.view_name = 'mftable_view'
        pcc.load()
        cfg = MFTableConfig(detectors=self.detector_names,
                            available_detectors=self.detector_names,
                            isotopes=self.isotopes,
                            isotope=self.isotope,
                            peak_center_config=pcc)

        info = cfg.edit_traits()
        pcc.view_name = ''
        if info.result:
            return cfg

    # private
    def _load_settings(self, params):
        spec = self.spectrometer
        if self.use_default_scan_settings:
            dd = self.default_detector
            iso = self.default_isotope
        else:
            dd = params.get('detector')
            iso = params.get('isotope')

        if dd:
            det = spec.get_detector(dd)

        if det:
            self.detector = det
        if iso:
            self.isotope = iso

        self.integration_time = params.get('integration_time', 1.048576)

    def _dump_settings(self, d):
        iso = self.isotope
        if not iso:
            iso = self.isotopes[0]

        det = self.detector
        if not det:
            det = self.detectors[0]

        d['isotope'] = iso
        d['detector'] = det.name
        d['integration_time'] = self.integration_time
        return d

    def _toggle_detector(self, obj, name, old, new):
        self.graph.set_series_visibility(new, series=obj.name)

    def _update_magnet(self, obj, name, old, new):
        self.debug('update magnet {},{},{}'.format(name, old, new))

        def func():
            if new and self.magnet.detector:
                # convert dac into a mass
                # convert mass to isotope
                #            d = self.magnet.dac
                # print 'supre', self._suppress_isotope_change
                # if not self._suppress_isotope_change:
                #     iso = self.magnet.map_dac_to_isotope(current=False)
                # else:
                #     iso = self.isotope

                iso = self.isotope
                print iso, self.isotopes
                if iso is None or iso not in self.isotopes:
                    iso = NULL_STR

                if self.use_log_events:
                    if iso == NULL_STR:
                        self.add_spec_event_marker(
                            'DAC={:0.5f}'.format(self.magnet.dac),
                            bgcolor='red')
                    else:
                        self.add_spec_event_marker(
                            '{}:{} ({:0.5f})'.format(self.detector,
                                                     iso, self.magnet.dac))

                self.debug('setting isotope: {}'.format(iso))
                self._suppress_isotope_change = True
                self.trait_set(isotope=iso)
                self._suppress_isotope_change = False

        from pychron.core.ui.gui import invoke_in_main_thread
        invoke_in_main_thread(func)

    def _check_intensity_no_change(self, signals):
        if self.spectrometer.simulation:
            return

        if self._no_intensity_change_cnt > 4:
            self.warning_dialog('Something appears to be wrong.\n\n'
                                'The detector intensities have not changed in 5 iterations. '
                                'Check Qtegra and RemoteControlServer.\n\n'
                                'Scan is stopped! Close and reopen window to restart')
            self._stop_timer()
            self._no_intensity_change_cnt = 0
            self._prev_signals = None
            return True

        if signals is None:
            self._no_intensity_change_cnt += 1
        elif self._prev_signals is not None:
            try:
                test = (signals == self._prev_signals).all()
            except (AttributeError, TypeError):
                print 'signals', signals
                print 'prev_signals', self._prev_signals
                test = True

            if test:
                self._no_intensity_change_cnt += 1
            else:
                self._no_intensity_change_cnt = 0
                self._prev_signals = None

        self._prev_signals = signals

    def _update(self, data):
        keys, signals = data
        if keys:
            self._signal_failed_cnt = 0
            if self._check_intensity_no_change(signals):
                return

            series, idxs = zip(*((i, keys.index(d.name)) for i, d in enumerate(self.detectors) if d.name in keys))
            signals = [signals[idx] for idx in idxs]

            x = self.graph.record_multiple(signals,
                                           series=series,
                                           track_y=False)

            if self.graph_y_auto:
                mi, ma = self._get_graph_y_min_max()

                self.graph.set_y_limits(min_=mi, max_=ma, pad='0.1')

            if self._recording and self.queue:
                self.queue.put((x, keys, signals))
        else:
            self._signal_failed_cnt += 1
            if self._signal_failed_cnt > 3:
                self.warning_dialog('Something appears to be wrong.\n\n'
                                    'The detector intensities have not changed in 5 iterations. '
                                    'Check Qtegra and RemoteControlServer.\n\n'
                                    'Scan is stopped! Close and reopen window to restart')
                self._stop_timer()

    def _update_scan_graph(self):
        if self.scan_enabled:
            data = self.spectrometer.get_intensities()
            if data:
                self._update(data)

    def _stop_timer(self):
        self.info('stopping scan timer')
        self.timer.Stop()

    def _start_recording(self):
        #        self._first_recording = True
        self.queue = Queue()
        self.record_data_manager = dm = CSVDataManager()
        self.consumer = Thread(target=self._consume, args=(dm,))
        self.consumer.start()
        # #        root = paths.spectrometer_scans_dir
        # #        p, _c = unique_path(root, 'scan')
        dm.new_frame(directory=paths.spectrometer_scans_dir)

    def _stop_recording(self):
        self._consuming = False
        self.record_data_manager.close_file()

    def _check_detector_protection(self, prev, is_detector):
        """
            return True if magnet move should be aborted

            @todo: this should be more sophisticated. eg

            refdet=H1, refiso=Ar40
            H1  0
            AX  100
            L1  0
            L2  0
            CDD 1

            move H1,Ar40 to L2
            this would place the 100 on CDD but this algorithm would not catch this problem

        """
        if self.use_detector_safety and self.detector:
            threshold = self.detector.protection_threshold
            if threshold:
                # for di in self.detectors:
                #     print di, di.isotope

                # find detector that the desired isotope is being measured on
                det = next((di for di in self.detectors
                            if di.isotope == self.isotope), None)
                if det:
                    # check that the intensity is less than threshold
                    abort = det.intensity > threshold
                    if abort:
                        if not self.confirmation_dialog(
                                'Are you sure you want to make this move.\n'
                                'This will place {} fA on {}'.format(
                                    det.intensity,
                                    self.detector)):

                            self.debug(
                                'aborting magnet move {} intensity {} > {}'.format(
                                    det, det.intensity,
                                    threshold))
                            if is_detector:
                                do_later(self.trait_set, detector=prev)
                            else:
                                do_later(self.trait_set, isotope=prev)

                            return True

    def _set_position(self):
        if self.isotope and self.isotope != NULL_STR \
                and self.detector:
            self.info('set position {} on {}'.format(self.isotope, self.detector))
            self.ion_optics_manager.position(self.isotope, self.detector.name)

    @property
    def update_period(self):
        return self.integration_time

    # ===============================================================================
    # handlers
    # ===============================================================================
    def _set_magnet_position_button_fired(self):
        self.debug('user triggered set magnet position')
        self._set_position()

    def _set_spectrometer_configuration_fired(self):
        self.debug('user triggered send_configuration')
        self.spectrometer.send_configuration()

    def _graph_changed(self):
        self.rise_rate.graph = self.graph

        plot = self.graph.plots[0]
        plot.value_range.on_trait_change(self._update_graph_limits,
                                         '_low_value, _high_value')

    def _isotope_changed(self, old, new):
        if self._suppress_isotope_change:
            return

        self.debug('isotope changed {}'.format(self.isotope))
        if self.isotope != NULL_STR and not self._check_detector_protection(old,
                                                                            False):
            def func():
                self._suppress_isotope_change = True
                self._set_position()
                self._suppress_isotope_change = False

            t = Thread(target=func)
            t.start()

    def _detector_changed(self, old, new):
        self.debug('detector changed {}'.format(self.detector))
        self.magnet.detector = self.detector
        self.rise_rate.detector = self.detector

        if self.isotope not in ('', NULL_STR, None):
            self.debug('isotope not set isotope={}. Not setting magnet'.format(self.isotope))
            return

        if self.detector and not self._check_detector_protection(old, True):
            # self.scanner.detector = self.detector
            nominal_width = 1
            emphasize_width = 2
            for name, plot in self.graph.plots[0].plots.iteritems():
                plot = plot[0]
                plot.line_width = emphasize_width if name == self.detector.name else nominal_width

            mass = self.magnet.mass
            if abs(mass) > 1e-5:
                molweights = self.spectrometer.molecular_weights
                if self.isotope in molweights:
                    mw = molweights[self.isotope]
                    if abs(mw - mass) > 0.1:
                        self.isotope = NULL_STR
                    else:
                        mass = self.isotope

                self.info('set position {} on {}'.format(mass, self.detector))

                def func():
                    self._suppress_isotope_change = True
                    self.ion_optics_manager.position(mass, self.detector)
                    self._suppress_isotope_change = False

                # thread not super necessary
                # simple allows gui to update while the magnet is delaying for settling_time
                # t = Thread(target=self.ion_optics_manager.position,
                #            args=(mass, self.detector))
                t = Thread(target=func)
                t.start()

    def _integration_time_changed(self):
        if self.integration_time:
            self.debug('setting integration time={}'.format(self.integration_time))
            self.spectrometer.set_integration_time(self.integration_time, force=True)
            self.reset_scan_timer()

    def _consume(self, dm):
        self._consuming = True
        _first_recording = True
        while self._consuming:
            time.sleep(0.0001)
            c = self.queue.get()
            try:
                x, keys, signals = c
            except ValueError:
                continue

            if dm:
                if _first_recording:
                    dm.write_to_frame(('time',) + tuple(keys))
                    _first_recording = False

                dm.write_to_frame((x,) + tuple(signals))

    # ===============================================================================
    # factories
    # ===============================================================================
    def _graph_factory(self):
        # g = TimeSeriesStreamGraph(container_dict=dict(bgcolor='lightgray',
        #                                               padding=5))

        name = 'Stream'
        if self.spectrometer.simulation:
            name = '{} (Simulation)'.format(name)
        g = SpectrometerScanGraph(container_dict=dict(bgcolor='lightgray',
                                                      padding=5),
                                  use_vertical_markers=self.use_vertical_markers,
                                  name=name)

        n = self.graph_scan_width * 60
        bottom_pad = 50
        if self.use_vertical_markers:
            bottom_pad = 120

        plot = g.new_plot(padding=[55, 5, 5, bottom_pad],
                          data_limit=n,
                          xtitle='Time',
                          ytitle='Signal',
                          scale=self.graph_scale,
                          bgcolor='lightgoldenrodyellow',
                          zoom=False)

        plot.x_grid.visible = False

        for i, det in enumerate(self.detectors):
            print 'adding det {} {}'.format(i, det.name)
            g.new_series(visible=det.active,
                         color=det.color)
            g.set_series_label(det.name)
            det.series_id = i

        if plot.plots:
            cp = plot.plots[det.name][0]
            dt = DataTool(plot=cp, component=plot,
                          normalize_time=True,
                          use_date_str=False)
            dto = DataToolOverlay(
                component=plot,
                tool=dt)
            plot.tools.append(dt)
            plot.overlays.append(dto)

            n = self.graph_scan_width
            n = max(n, 1 / 60.)
            mins = n * 60
            g.data_limits[0] = 1.8 * mins

        return g

    # ===============================================================================
    # property get/set
    # ===============================================================================
    def _get_detector(self):
        return self.spectrometer.get_detector(self._detector)

    def _set_detector(self, v):
        if isinstance(v, BaseDetector):
            v = v.name
        self._detector = v

    @cached_property
    def _get_isotopes(self):
        return [NULL_STR] + self.spectrometer.isotopes

    # ===============================================================================
    # defaults
    # ===============================================================================
    def _rise_rate_default(self):
        r = RiseRate(spectrometer=self.spectrometer,
                     graph=self.graph)
        return r

    def _dac_scanner_default(self):
        s = DACScanner(spectrometer=self.spectrometer)
        s.load()
        return s

    def _readout_view_default(self):
        rd = ReadoutView(spectrometer=self.spectrometer)
        return rd

    def _mass_scanner_default(self):
        ms = MassScanner(spectrometer=self.spectrometer)
        ms.load()
        return ms

# ============= EOF =====================================
