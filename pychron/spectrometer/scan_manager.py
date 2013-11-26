#===============================================================================
# Copyright 2012 Jake Ross
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
from numpy import Inf
from traits.api import Instance, Enum, Any, DelegatesTo, List, Property, \
    Bool, Int, Button, Event, String, cached_property, \
    HasTraits, Range, Float
# from pyface.timer.api import Timer
#============= standard library imports ========================
import random
import os
import pickle
#============= local library imports  ==========================
from pychron.managers.manager import Manager
from pychron.graph.time_series_graph import TimeSeriesStreamGraph
from pychron.spectrometer.detector import Detector
from pychron.spectrometer.jobs.magnet_scan import MagnetScan
from pychron.spectrometer.jobs.rise_rate import RiseRate
from pychron.paths import paths
# from pychron.graph.tools.data_tool import DataTool, DataToolOverlay
# import csv
# from pychron.helpers.filetools import unique_path
from pychron.managers.data_managers.csv_data_manager import CSVDataManager
# import time

import time
from threading import Thread
from Queue import Queue
from pychron.helpers.timer import Timer
from pychron.pychron_constants import NULL_STR
from pychron.spectrometer.readout_view import ReadoutView
from pychron.graph.tools.data_tool import DataTool, DataToolOverlay
# class CSVDataManager(HasTraits):
#    def new_file(self, p, mode='w'):
#        self._file = open(p, mode)
#        self._writer = csv.writer(self._file)
#
#    def add_datum(self, *datum_tuple):
#        self._writer.writerow(datum_tuple)
#
#    def close(self):
# #        self._writer.close()
#        self._file.close()


class ScanManager(Manager):
    spectrometer = Any

    graph = Instance(TimeSeriesStreamGraph)
    readout_view = Instance(ReadoutView)

    integration_time = Enum(0, 0.065536, 0.131072, 0.262144, 0.524288,
                            1.048576, 2.097152, 4.194304, 8.388608,
                            16.777216, 33.554432, 67.108864)

    detectors = DelegatesTo('spectrometer')
    detector = Instance(Detector)
    magnet = DelegatesTo('spectrometer')
    source = DelegatesTo('spectrometer')
    scanner = Instance(MagnetScan)
    rise_rate = Instance(RiseRate)
    isotope = String
    isotopes = Property

    graph_scale = Enum('linear', 'log')

    graph_y_auto = Bool

    graph_ymin = Property(Float, depends_on='_graph_ymin')
    graph_ymax = Property(Float, depends_on='_graph_ymax')
    _graph_ymin = Float
    _graph_ymax = Float
    graph_scan_width = Int  # in minutes

    record_button = Event
    add_marker_button = Button('Add Marker')
    record_label = Property(depends_on='_recording')
    _recording = Bool(False)
    record_data_manager = Any
    _consuming = False
    queue = None

    timer = None

    def _update_graph_limits(self, name, new):
        if 'high' in name:
            self._graph_ymax = max(new, self._graph_ymin)
        else:
            self._graph_ymin = min(new, self._graph_ymax)


    def _toggle_detector(self, obj, name, old, new):
        self.graph.set_series_visiblity(new, series=obj.name)

    def _update_magnet(self, obj, name, old, new):
        if new:
        # covnert dac into a mass
        # convert mass to isotope
        #            d = self.magnet.dac
            iso = self.magnet.map_dac_to_isotope()
            if not iso in self.isotopes:
                iso = NULL_STR

            self.trait_set(isotope=iso, trait_change_notify=False)

    #@deprecated
    #def close(self, isok):
    #    self.stop_scan()
    #
    #@deprecated
    #def opened(self, ui):
    #    self.setup_scan()

    def stop_scan(self):
        self.dump_settings()
        self._stop_timer()

        # clear our graph settings so on reopen events will fire
        del self.graph_scale
        del self._graph_ymax
        del self._graph_ymin
        del self.graph_y_auto
        del self.graph_scan_width

    def setup_scan(self):
        self.graph = self._graph_factory()

        #trigger a timer reset. set to 0 then default
        self.integration_time = 0
        self.integration_time = 1.048576

        # listen to detector for enabling
        self.on_trait_change(self._toggle_detector, 'detectors:active')

        # force update
        self.load_settings()

        # bind
        self.on_trait_change(self._update_magnet, 'magnet:dac_changed')

        # force position update
        self._set_position()

    def load_settings(self):
        self.info('load scan settings')
        spec = self.spectrometer
        p = os.path.join(paths.hidden_dir, 'scan_settings')
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
                            print pi, e

                except (pickle.PickleError, EOFError, KeyError):
                    self.detector = self.detectors[-1]
                    self.isotope = self.isotopes[-1]

    def dump_settings(self):
        self.info('dump scan settings')
        p = os.path.join(paths.hidden_dir, 'scan_settings')
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

    @property
    def graph_attr_keys(self):
        return ['graph_scale',
                'graph_ymin',
                'graph_ymax',
                'graph_y_auto',
                'graph_scan_width']


    def _update(self, data):
        keys, signals = data
        if signals:
            x = self.graph.record_multiple(signals,
                                           track_y=False)

            if self.graph_y_auto:
                mi,ma=Inf,-Inf
                for k,plot in self.graph.plots[0].plots.iteritems():
                    plot=plot[0]
                    if plot.visible:
                        ys=plot.value.get_data()
                        ma=max(ma, max(ys))
                        mi=min(ma, min(ys))

                self.graph.set_y_limits(min_=mi,max_=ma, pad='0.1')

            if self._recording and self.queue:
                self.queue.put((x, keys, signals))

    def _update_scan_graph(self):
        data = self.spectrometer.get_intensities()
        if data:
            self._update(data)

    def reset_scan_timer(self):
        self.info('reset scan timer')
        self.timer = self._timer_factory()

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

    #===============================================================================
    # handlers
    #===============================================================================
    def _set_position(self):
        if self.isotope and self.isotope != NULL_STR \
            and self.detector:
            self.info('set position {} on {}'.format(self.isotope, self.detector))
            self.ion_optics_manager.position(self.isotope, self.detector.name)

    def _isotope_changed(self):
        if self.isotope != NULL_STR:
            self._set_position()

    def _graph_changed(self):
        self.rise_rate.graph = self.graph

        plot = self.graph.plots[0]
        plot.value_range.on_trait_change(self._update_graph_limits, '_low_value, _high_value')

    #        plot.value_range.on_trait_change(self._update_graph_limits, '_high_value')

    def _detector_changed(self):
        if self.detector:
            self.scanner.detector = self.detector
            self.rise_rate.detector = self.detector
            self.magnet.detector = self.detector
            nominal_width = 1
            emphasize_width = 2
            for name, plot in self.graph.plots[0].plots.iteritems():
                plot = plot[0]
                plot.line_width = emphasize_width if name == self.detector.name else nominal_width

            #            print self.detector, self.magnet.mass, self.magnet._mass

            mass = self.magnet.mass
            if abs(mass) > 1e-5:
                molweights = self.spectrometer.molecular_weights
                if self.isotope in molweights:
                    mw = molweights[self.isotope]
                    if abs(mw - mass) > 0.1:
                        self.isotope = NULL_STR

                self.info('set position {} on {}'.format(mass, self.detector))

                # thread not super necessary
                # simple allows gui to update while the magnet is delaying for settling_time
                t = Thread(target=self.ion_optics_manager.position, args=(mass, self.detector))
                t.start()
                #

    def _graph_y_auto_changed(self, new):
        p = self.graph.plots[0]
        if not new:
            #p.value_range.low_setting = 'auto'
            #p.value_range.high_setting = 'auto'
        #else:
            p.value_range.low_setting = self.graph_ymin
            p.value_range.high_setting = self.graph_ymax
        self.graph.redraw()


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
        g.set_x_tracking(mins)

    def _record_button_fired(self):
        if self._recording:
            self._stop_recording()
            self._recording = False
        else:
            self._start_recording()
            self._recording = True

    def _add_marker_button_fired(self):
        xs = self.graph.plots[0].data.get_data('x0')

        self.record_data_manager.write_to_frame(tuple(' '))
        self.graph.add_vertical_rule(xs[-1])


    def _integration_time_changed(self):
        if self.integration_time:
            self.spectrometer.set_integration_time(self.integration_time)

            self.graph.set_scan_delay(self.integration_time)
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
                #===============================================================================
                # factories
                #===============================================================================

    def _timer_factory(self, func=None):

        if func is None:
            func = self._update_scan_graph

        if self.timer:
            self.timer.Stop()
            self.timer.wait_for_completion()

        mult = 1000
        return Timer(self.integration_time * mult, func)

    def _graph_factory(self):
        g = TimeSeriesStreamGraph(container_dict=dict(bgcolor='lightgray',
                                                      padding=5))

        n = self.graph_scan_width * 60
        plot = g.new_plot(padding=[55, 5, 5, 50],
                          data_limit=n,
                          xtitle='Time',
                          ytitle='Signal',
                          scale=self.graph_scale,
                          bgcolor='whitesmoke',
                          zoom=True)

        plot.x_grid.visible = False

        for i, det in enumerate(self.detectors):
        #            if not det.active:
            g.new_series(visible=det.active,
                         #                         use_downsampling=False,
                         color=det.color)
            #            print s.use_downsampling
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

            #        self.graph_ymax_auto = True
        #        self.graph_ymin_auto = True
        #        p.value_range.low_setting = 'auto'
        #        p.value_range.high_setting = 'auto'
        #        p.value_range.tight_bounds = False

            n = self.graph_scan_width
            n = max(n, 1 / 60.)
            mins = n * 60
            g.data_limits[0] = 1.8 * mins
            #        g.set_x_tracking(mins)

        return g

    #===============================================================================
    # property get/set
    #===============================================================================
    @cached_property
    def _get_isotopes(self):
        molweights = self.spectrometer.molecular_weights
        return [NULL_STR] + sorted(molweights.keys(), key=lambda x: int(x[2:]))

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

    #===============================================================================
    # defaults
    #===============================================================================
    def _graph_default(self):
        return self._graph_factory()

    def _rise_rate_default(self):
        r = RiseRate(spectrometer=self.spectrometer,
                     graph=self.graph)
        return r

    def _scanner_default(self):
        s = MagnetScan(spectrometer=self.spectrometer)
        return s

    def _readout_view_default(self):
        rd = ReadoutView(spectrometer=self.spectrometer)
        p = os.path.join(paths.spectrometer_dir, 'readout.cfg')
        config = self.get_configuration(path=p)
        rd.load(config)

        return rd

if __name__ == '__main__':
    from pychron.spectrometer.molecular_weights import MOLECULAR_WEIGHTS

    class Magnet(HasTraits):
        dac = Range(0.0, 6.0)

        def map_mass_to_dac(self, d):
            return d

    class Source(HasTraits):
        y_symmetry = Float

    class DummySpectrometer(HasTraits):
        detectors = List
        magnet = Instance(Magnet, ())
        source = Instance(Source, ())
        molecular_weights = MOLECULAR_WEIGHTS

        def get_intensities(self):
            return [d.name for d in self.detectors], [random.random() + (i * 12.3) for i in range(len(self.detectors))]

        def get_intensity(self, *args, **kw):
            return 1

    detectors = [
        Detector(name='H2',
                 color='black',
                 isheader=True
        ),
        Detector(name='H1',
                 color='red'
        ),
        Detector(name='AX',
                 color='violet'
        ),
        Detector(name='L1',
                 color='maroon'
        ),
        Detector(name='L2',
                 color='yellow'
        ),
        Detector(name='CDD',
                 color='lime green',
                 active=False
        ),

    ]
    sm = ScanManager(
        #                     detectors=detectors,
        spectrometer=DummySpectrometer(detectors=detectors))
    #    sm.load_detectors()
    sm.configure_traits()
#============= EOF =============================================
