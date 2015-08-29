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
from pyface.timer.do_later import do_later
from traits.api import Instance, Enum, Any, DelegatesTo, List, Property, \
    Bool, Button, String, cached_property, \
    Float, Event
# ============= standard library imports ========================
import os
import pickle
import time
from numpy import Inf
from threading import Thread
from Queue import Queue
import yaml
# ============= local library imports  ==========================
from pychron.core.ui.preference_binding import bind_preference
from pychron.managers.manager import Manager
from pychron.graph.time_series_graph import TimeSeriesStreamGraph
from pychron.spectrometer.graph.spectrometer_scan_graph import SpectrometerScanGraph
from pychron.spectrometer.jobs.scanner import Scanner
from pychron.spectrometer.thermo.detector import Detector
from pychron.spectrometer.jobs.rise_rate import RiseRate
from pychron.paths import paths
from pychron.managers.data_managers.csv_data_manager import CSVDataManager
from pychron.core.helpers.timer import Timer
from pychron.pychron_constants import NULL_STR
from pychron.spectrometer.readout_view import ReadoutView
from pychron.graph.tools.data_tool import DataTool, DataToolOverlay


class ScanManager(Manager):
    spectrometer = Any
    ion_optics_manager = Instance('pychron.spectrometer.ion_optics.ion_optics_manager.IonOpticsManager')

    graph = Instance(TimeSeriesStreamGraph)
    # graphs = List

    readout_view = Instance(ReadoutView)

    integration_time = DelegatesTo('spectrometer')

    detectors = DelegatesTo('spectrometer')
    detector = Instance(Detector)
    magnet = DelegatesTo('spectrometer')
    source = DelegatesTo('spectrometer')
    scanner = Instance(Scanner)
    rise_rate = Instance(RiseRate)
    isotope = String
    isotopes = Property

    graph_scale = Enum('linear', 'log')

    graph_y_auto = Bool

    graph_ymin = Property(Float, depends_on='_graph_ymin')
    graph_ymax = Property(Float, depends_on='_graph_ymax')
    _graph_ymin = Float
    _graph_ymax = Float
    graph_scan_width = Float(enter_set=True, auto_set=False)  # in minutes
    clear_button = Event

    scan_enabled = Bool(True)
    # record_button = Event
    # record_button = ToggleButton(image_on=icon('media-record'),
    # image_off=icon('media-playback-stop'),
    # tooltip_on='Start recording scan',
    #                              tooltip_off='Stop recording scan',
    #                              # height=22,
    #                              # width=45
    #                             )

    start_record_button = Button
    stop_record_button = Button

    snapshot_button = Button
    snapshot_output = Enum('png', 'pdf')

    # add_visual_marker_button = Button('Add Visual Marker')
    # marker_text = Str
    add_marker_button = Button('Add Marker')
    clear_all_markers_button = Button
    use_vertical_markers = Bool

    record_label = Property(depends_on='_recording')
    _recording = Bool(False)
    record_data_manager = Any

    use_detector_safety = Bool(True)

    _consuming = False
    queue = None
    timer = None

    use_log_events = Bool
    log_events_enabled = False
    _valve_event_list = List
    _prev_signals = None
    _no_intensity_change_cnt = 0

    def _bind_listeners(self, remove=False):
        self.on_trait_change(self._update_magnet, 'magnet:dac_changed', remove=remove)
        self.on_trait_change(self._toggle_detector, 'detectors:active', remove=remove)

    def prepare_destroy(self):
        self.stop_scan()
        self.log_events_enabled = False
        self._bind_listeners(remove=True)

        plot = self.graph.plots[0]
        plot.value_range.on_trait_change(self._update_graph_limits,
                                         '_low_value, _high_value', remove=True)
        self.readout_view.stop()

    def stop_scan(self):
        self.dump_settings()
        self._stop_timer()

        # clear our graph settings so on reopen events will fire
        del self.graph_scale
        del self._graph_ymax
        del self._graph_ymin
        del self.graph_y_auto
        del self.graph_scan_width

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
        bind_preference(self, 'use_detector_safety', '{}.use_detector_safety'.format(pref_id))
        bind_preference(self, 'use_log_events', '{}.use_log_events'.format(pref_id))
        bind_preference(self, 'use_vertical_markers', '{}.use_vertical_markers'.format(pref_id))

    def setup_scan(self):
        self._reset_graph()

        # bind
        self._bind_listeners()
        # # listen to detector for enabling
        # self.on_trait_change(self._toggle_detector, 'detectors:active')
        # self.on_trait_change(self._update_magnet, 'magnet:dac_changed')

        # force update
        self.load_settings()

        # force position update
        self._set_position()
        self.log_events_enabled = True

    def load_settings(self):
        self.info('load scan settings')
        spec = self.spectrometer

        p = os.path.join(paths.hidden_dir, 'scan_settings.p')
        if os.path.isfile(p):
            with open(p, 'rb') as f:
                try:
                    params = pickle.load(f)

                    det = spec.get_detector(params['detector'])
                    if det.kind == 'Faraday':
                        self.detector = det
                        self.isotope = params['isotope']

                    for pi in self.graph_attr_keys:
                        try:
                            setattr(self, pi, params[pi])
                        except KeyError, e:
                            print 'sm load settings', pi, e

                except (pickle.PickleError, EOFError, KeyError):
                    self.detector = self.detectors[-1]
                    self.isotope = self.isotopes[-1]
                    self.warning('Failed unpickling scan settings file {}'.format(p))
        else:
            self.warning('No scan settings file {}'.format(p))

    def dump_settings(self):
        self.info('dump scan settings')
        p = os.path.join(paths.hidden_dir, 'scan_settings.p')
        with open(p, 'wb') as f:
            iso = self.isotope
            if not iso:
                iso = self.isotopes[0]

            det = self.detector
            if not det:
                det = self.detectors[0]

            d = dict(isotope=iso,
                     detector=det.name)

            for ki in self.graph_attr_keys:
                d[ki] = getattr(self, ki)

            pickle.dump(d, f)

    def reset_scan_timer(self):
        self.info('reset scan timer')
        self.timer = self._timer_factory()

    def add_spec_event_marker(self, msg, mode=None, extra=None, bgcolor='white'):
        if self.use_log_events and self.log_events_enabled:
            if mode == 'valve' and self._valve_event_list:
                # check valve name is configured to be displayed
                if extra not in self._valve_event_list:
                    return

            self.debug('add spec event marker. {}'.format(msg))
            self.graph.add_visual_marker(msg, bgcolor)

    # private
    def _reset_graph(self):
        self.graph = self._graph_factory()
        # if len(self.graphs):
        #     self.graphs.pop(0)
        # self.graphs.insert(0, self.graph)

        # trigger a timer reset. set to 0 then default
        self.reset_scan_timer()

    def _update_graph_limits(self, name, new):
        if 'high' in name:
            self._graph_ymax = max(new, self._graph_ymin)
        else:
            self._graph_ymin = min(new, self._graph_ymax)

    def _toggle_detector(self, obj, name, old, new):
        self.graph.set_series_visiblity(new, series=obj.name)

    def _update_magnet(self, obj, name, old, new):
        # print obj, name, old, new
        if new and self.magnet.detector:
            # covnert dac into a mass
            # convert mass to isotope
            #            d = self.magnet.dac
            iso = self.magnet.map_dac_to_isotope(current=False)
            if not iso in self.isotopes:
                iso = NULL_STR

            if self.use_log_events:
                if iso == NULL_STR:
                    self.add_spec_event_marker('DAC={:0.5f}'.format(self.magnet.dac), bgcolor='red')
                else:
                    self.add_spec_event_marker('{}:{} ({:0.5f})'.format(self.detector,
                                                                        iso, self.magnet.dac))

            self.trait_setq(isotope=iso)

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

        if self._prev_signals is not None:

            if (signals == self._prev_signals).all():
                self._no_intensity_change_cnt += 1
            else:
                self._no_intensity_change_cnt = 0
                self._prev_signals = None

        self._prev_signals = signals

    def _update(self, data):
        keys, signals = data
        if keys:
            if self._check_intensity_no_change(signals):
                return

            x = self.graph.record_multiple(signals,
                                           track_y=False)

            if self.graph_y_auto:
                mi, ma = Inf, -Inf
                for k, plot in self.graph.plots[0].plots.iteritems():
                    plot = plot[0]
                    if plot.visible:
                        ys = plot.value.get_data()
                        ma = max(ma, max(ys))
                        mi = min(mi, min(ys))

                self.graph.set_y_limits(min_=mi, max_=ma, pad='0.1')

            if self._recording and self.queue:
                self.queue.put((x, keys, signals))

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
                        if not self.confirmation_dialog('Are you sure you want to make this move.\n'
                                                        'This will place {} fA on {}'.format(det.intensity,
                                                                                             self.detector)):

                            self.debug('aborting magnet move {} intensity {} > {}'.format(det, det.intensity,
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

    # ===============================================================================
    # handlers
    # ===============================================================================
    def _clear_button_fired(self):
        self._reset_graph()

    def _graph_changed(self):
        self.rise_rate.graph = self.graph

        plot = self.graph.plots[0]
        plot.value_range.on_trait_change(self._update_graph_limits, '_low_value, _high_value')

    def _isotope_changed(self, old, new):
        self.debug('isotope changed {}'.format(self.isotope))
        if self.isotope != NULL_STR and not self._check_detector_protection(old, False):
            t = Thread(target=self._set_position)
            t.start()

    def _detector_changed(self, old, new):
        self.debug('detector changed {}'.format(self.detector))
        if self.detector and not self._check_detector_protection(old, True):
            self.scanner.detector = self.detector
            self.rise_rate.detector = self.detector
            self.magnet.detector = self.detector
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

                # thread not super necessary
                # simple allows gui to update while the magnet is delaying for settling_time
                t = Thread(target=self.ion_optics_manager.position, args=(mass, self.detector))
                t.start()

    def _graph_y_auto_changed(self, new):
        p = self.graph.plots[0]
        if not new:
            p.value_range.low_setting = self.graph_ymin
            p.value_range.high_setting = self.graph_ymax
        self.graph.redraw()

    def _graph_scale_changed(self, new):
        p = self.graph.plots[0]
        p.value_scale = new
        self.graph.redraw()

    def _graph_scan_width_changed(self):
        g = self.graph
        n = self.graph_scan_width
        n = max(n, 1 / 60.)
        mins = n * 60
        g.data_limits[0] = 1.8 * mins
        g.scan_widths[0] = mins

    def _clear_all_markers_button_fired(self):
        self.graph.clear_markers()

    def _start_record_button_fired(self):
        # if self._recording:
        #     self._stop_recording()
        #     self._recording = False
        # else:
        self._start_recording()
        self._recording = True

    def _stop_record_button_fired(self):
        self._stop_recording()
        self._recording = False

    def _snapshot_button_fired(self):
        self.debug('snapshot button fired')
        self.graph.save()

    # def _add_visual_marker_button_fired(self):
    #     if self.marker_label_with_intensity:
    #     self.graph.add_visual_marker()
    #
    # def _marker_text_changed(self, new):
    #     self.graph.marker_text = new

    def _add_marker_button_fired(self):
        xs = self.graph.plots[0].data.get_data('x0')

        self.record_data_manager.write_to_frame(tuple(' '))
        self.graph.add_vertical_rule(xs[-1])

    def _integration_time_changed(self):
        if self.integration_time:
            self.spectrometer.set_integration_time(self.integration_time)
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
    def _timer_factory(self, func=None):

        if func is None:
            func = self._update_scan_graph

        if self.timer:
            self.timer.Stop()
            self.timer.wait_for_completion()

        mult = 1000
        return Timer(self.integration_time * mult, func)

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
    @cached_property
    def _get_isotopes(self):
        # molweights = self.spectrometer.molecular_weights
        return [NULL_STR] + self.spectrometer.isotopes  #sorted(molweights.keys(), key=lambda x: int(x[2:]))

    def _validate_graph_ymin(self, v):
        try:
            v = float(v)
            if v < self.graph_ymax:
                return v
        except ValueError:
            pass

    def _validate_graph_ymax(self, v):
        try:
            v = float(v)
            if v > self.graph_ymin:
                return v
        except ValueError:
            pass

    def _get_graph_ymin(self):
        return self._graph_ymin

    def _get_graph_ymax(self):
        return self._graph_ymax

    def _set_graph_ymin(self, v):
        if v is not None:
            self._graph_ymin = v
            p = self.graph.plots[0]
            p.value_range.low_setting = v
            self.graph.redraw()

    def _set_graph_ymax(self, v):
        if v is not None:
            self._graph_ymax = v
            p = self.graph.plots[0]
            p.value_range.high_setting = v
            self.graph.redraw()

    def _get_record_label(self):
        return 'Record' if not self._recording else 'Stop'

    @property
    def graph_attr_keys(self):
        return ['graph_scale',
                'graph_ymin',
                'graph_ymax',
                'graph_y_auto',
                'graph_scan_width']

    # ===============================================================================
    # defaults
    # ===============================================================================
    def _graph_default(self):
        g = self._graph_factory()
        # self.graphs.append(g)
        return g

    def _rise_rate_default(self):
        r = RiseRate(spectrometer=self.spectrometer,
                     graph=self.graph)
        return r

    def _scanner_default(self):
        s = Scanner(spectrometer=self.spectrometer)
        return s

    def _readout_view_default(self):
        rd = ReadoutView(spectrometer=self.spectrometer)
        return rd


        # if __name__ == '__main__':
        # from pychron.spectrometer.molecular_weights import MOLECULAR_WEIGHTS
        #
        #     class Magnet(HasTraits):
        #         dac = Range(0.0, 6.0)
        #
        #         def map_mass_to_dac(self, d):
        #             return d
        #
        #     class Source(HasTraits):
        #         y_symmetry = Float
        #
        #     class DummySpectrometer(HasTraits):
        #         detectors = List
        #         magnet = Instance(Magnet, ())
        #         source = Instance(Source, ())
        #         molecular_weights = MOLECULAR_WEIGHTS
        #
        #         def get_intensities(self):
        #             return [d.name for d in self.detectors], [random.random() + (i * 12.3) for i in range(len(self.detectors))]
        #
        #         def get_intensity(self, *args, **kw):
        #             return 1
        #
        #     detectors = [
        #         Detector(name='H2',
        #                  color='black',
        #                  isheader=True
        #         ),
        #         Detector(name='H1',
        #                  color='red'
        #         ),
        #         Detector(name='AX',
        #                  color='violet'
        #         ),
        #         Detector(name='L1',
        #                  color='maroon'
        #         ),
        #         Detector(name='L2',
        #                  color='yellow'
        #         ),
        #         Detector(name='CDD',
        #                  color='lime green',
        #                  active=False
        #         ),
        #
        #     ]
        #     sm = ScanManager(
        #         # detectors=detectors,
        #         spectrometer=DummySpectrometer(detectors=detectors))
        #     # sm.load_detectors()
        #     sm.configure_traits()
    # ============= EOF =============================================
    # def _check_detector_protection1(self, prev):
    # """
    # used when detector changes
    # return True if magnet move should be aborted
    #     """
    #     return self._check_detector_protection(prev, True)
    #
    # def _check_detector_protection2(self, prev):
    #     """
    #         used when isotope changes
    #         return True if magnet move should be aborted
    #     """
    #     return self._check_detector_protection(prev, False)
    #    def _graph_ymin_auto_changed(self, new):
    #        p = self.graph.plots[0]
    #        if new:
    #            p.value_range.low_setting = 'auto'
    #        else:
    #            p.value_range.low_setting = self.graph_ymin
    #        self.graph.redraw()
    #
    #    def _graph_ymax_auto_changed(self, new):
    #        p = self.graph.plots[0]
    #        if new:
    #            p.value_range.high_setting = 'auto'
    #        else:
    #            p.value_range.high_setting = self.graph_ymax
    #        self.graph.redraw()