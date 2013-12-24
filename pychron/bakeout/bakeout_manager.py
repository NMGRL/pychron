#!/usr/bin/python
#===============================================================================
# Copyright 2011 Jake Ross
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

#============= enthought library imports  ==========================
from traits.api import Instance, Bool, Button, Event, \
    Float, Str, Property, List, on_trait_change, Dict, Any, cached_property

#============= standard library imports  ==========================
from numpy import hstack
import os
import time
from ConfigParser import NoSectionError
#============= local library imports  ==========================
from pychron.managers.manager import Manager
from pychron.hardware.bakeout_controller import BakeoutController
from pychron.hardware.core.communicators.scheduler import CommunicationScheduler
from pychron.paths import paths
from pychron.graph.time_series_graph import TimeSeriesStackedGraph, \
    TimeSeriesStreamStackedGraph
from pychron.core.helpers.datetime_tools import generate_datestamp
from pychron.managers.data_managers.csv_data_manager import CSVDataManager
from pychron.hardware.core.i_core_device import ICoreDevice
from pychron.graph.graph import Graph
from pychron.hardware.core.core_device import CoreDevice
from pychron.hardware.gauges.granville_phillips.micro_ion_controller import MicroIonController
from pychron.managers.data_managers.data_manager import DataManager
from pychron.core.helpers.archiver import Archiver
from pychron.database.adapters.bakeout_adapter import BakeoutAdapter
from pychron.database.data_warehouse import DataWarehouse
import datetime
from pychron.bakeout.classifier import Classifier
from pychron.utils import get_display_size
from Queue import Queue
from pychron.core.ui.gui import invoke_in_main_thread

BATCH_SET_BAUDRATE = False
BAUDRATE = '38400'


class BakeoutManager(Manager):

    '''
    '''

    graph = Instance(Graph)
    bakeout1 = Instance(BakeoutController)
    bakeout2 = Instance(BakeoutController)
    bakeout3 = Instance(BakeoutController)
    bakeout4 = Instance(BakeoutController)
    bakeout5 = Instance(BakeoutController)
    bakeout6 = Instance(BakeoutController)

    update_interval = Float(2, enter_set=True, auto_set=False)
    scan_window = Float(10, enter_set=True, auto_set=False)

    execute = Event
    execute_ok = Property(depends_on='bakeout+:execute_dirty')
    execute_label = Property(depends_on='active')
    active = Bool(False)

    training_run = Bool(False)

    save = Button

    configuration = Str
    configurations = Property(depends_on='_configurations_dirty')
    _configurations_dirty = Event

    data_name = Str

    active_controllers = Property(List)

#     open_button = Button
#     open_label = 'Open'

    gauge_controller = Instance(CoreDevice)

    use_pressure_monitor = Bool(False)
    _pressure_sampling_period = 2
    _max_duration = 10  # 10 hrs
    _pressure_monitor_std_threshold = 1
    _pressure_monitor_threshold = 1e-2
    _pressure = Float

#     pressure_buffer = Array

    include_pressure = Bool
    include_heat = Bool(False)
    include_temp = Bool(True)

    plotids = List([0, 1, 2])

    _nactivated_controllers = 0
    data_manager = Instance(DataManager)
    graph_info = Dict

    database = Any
    _suppress_commit = False

    force_program = True

    def find_bakeout(self):
        db = self.database
        if db.connect():
#            db.selector.load_last()
            db.selector.load_recent()
            self.open_view(db.selector)

    def open_latest_bake(self):
        self.info('open last bake')
        db = self.database
        if db.connect():
            sel = db.selector
            sel.load_recent()
            if sel.records:
                rec = sel.records[-1]
                sel.open_record(rec)

    def refresh_scripts(self):
        for c in self._get_controllers():
            c.load_scripts()

    def reset_data_recording(self):
        controllers = self._get_controllers()
#         if not self.data_manager:
        self.data_manager = self._data_manager_factory(controllers,
                                                           [],
                                                           style='h5')

        self._current_data_path = cp = self.data_manager.get_current_path()
#        self._add_bakeout_to_db(controllers, cp)
    def destroy(self):
        cs = self._get_controllers()
        for c in cs:
            c.stop_timer()
        
    def activate(self):
        self.data_queue = Queue()
        from threading import Thread
        t = Thread(target=self._graph_thread)
        t.setDaemon(True)
        t.start()

        self.reset_general_scan()

    def reset_general_scan(self):
        self.info('Starting general scan')

        # reset the graph
        self.graph = self._graph_factory()
        for i, name in enumerate(self._get_controller_names()):
            self._setup_graph(name, i)

        # stop all timers first
        cs = self._get_controllers()
        for c in cs:
            c.stop_timer()

        # delay to allow threads to exit
        time.sleep(0.5)

        for i, c in enumerate(cs):
        # reset the general timers
            c.start_timer()

    def load(self, *args, **kw):
        app = self.application
        for bo in self._get_controller_names():
            bc = self._controller_factory(bo)
            self.trait_set(**{bo: bc})

            if app is not None:
                app.register_service(ICoreDevice, bc, {'display'
                        : False})

        if app is not None:
            self.gauge_controller = app.get_service(MicroIonController,
                    query='name=="roughing_gauge_controller"')
        else:

            gc = MicroIonController(name='roughing_gauge_controller')
            gc.bootstrap()
            self.gauge_controller = gc

        self._load_controllers()

#     def kill(self):
#         super(BakeoutManager, self).kill()
#
#         if self.data_manager:
#             self.data_manager.close_file()
#
#         for c in self._get_controllers():
#             c.end()
#             c.stop_timer()
#
#         self._clean_archive()
#==============================================================================
# private
#==============================================================================
    def _load_controllers(self):
        '''
        '''
        scheduler = CommunicationScheduler()
        program = False
        cnt = 0
        for bc in self._get_controllers():
#            bc.on_trait_change(self.update_active, 'active')
            # set the communicators scheduler
            # used to synchronize access to port
            if bc.load():
                bc.set_scheduler(scheduler)

                if bc.open():
                    '''
                        on first controller check to see if
                        memory block programming is required

                        if it is apply to all subsequent controllers
                    '''
                    if not self.force_program:
                        if cnt == 0:
                            if not bc.is_programmed():
                                program = True
                            m1 = 'Watlow controllers require programming. Programming automatically'
                            m2 = 'Watlow controllers are properly programmed'
                            self.info(m1 if program else m2)
                    else:
                        program = True

                    bc.program_memory_blocks = program

                    bc.initialize()
                    cnt += 1

        return True

    def _parse_config_file(self, p):
        config = self.get_configuration(p, warn=False)
        if config is None:
            return
        try:
            self.include_temp = config.getboolean('Include', 'temp')
            self.include_heat = config.getboolean('Include', 'heat')
            self.include_pressure = config.getboolean('Include',
                    'pressure')
        except NoSectionError:
            pass

        try:
            self.update_interval = config.getfloat('Scan', 'interval')
            self.scan_window = config.getfloat('Scan', 'window')
        except NoSectionError:
            pass

        for section in config.sections():
            if section.startswith('bakeout'):
                kw = dict()
                script = self.config_get(config, section, 'script',
                        optional=True)
                if script:
                    kw['script'] = script
                else:
                    kw['script'] = '---'
                    for opt in ['duration', 'setpoint']:
                        value = self.config_get(config, section, opt,
                                cast='float')
                        if value is not None:
                            kw[opt] = value

                    kw['record_process'] = self.config_get(config, section,
                                                           'record_process',
                                                           default=False,
                                                           optional=True,
                                                           cast='boolean'
                                                           )
                getattr(self, section).trait_set(**kw)

    def _clean_archive(self):
        root = os.path.join(paths.data_dir, 'bakeouts')
        self.info('cleaning bakeout data directory {}'.format(root))
        a = Archiver(root=root, archive_days=14, archive_months=8)
        a.clean(spawn_process=False)
#===============================================================================
# graph
#===============================================================================
    def _setup_graph(self, name, pid):
        self.graph.new_series()
        self.graph_info[name] = dict(id=pid)

        self.graph.set_series_label(name, series=pid)
        if self.include_heat:
            self.graph.new_series(plotid=self.plotids[1])

    def _do_graph(self, data):
#         self.debug('do graph {}'.format(len(data)))
        g = self.graph
        temp_id = self.plotids[0]
        heat_id = self.plotids[1]
        include_temp = self.include_temp
        include_heat = self.include_heat

        buf_x = []
#         for ci, (_name, i, pi, hi) in enumerate(self.data_buffer):
        n = len(data)
        kwargs = dict(track_y=False, pad=0.05)
        for ci, (_name, i, pi, hi) in enumerate(data):
            track_x = ci == n - 1
            kwargs['track_x'] = track_x
            kwargs['series'] = i
            if include_temp:
                kwargs['plotid'] = temp_id
                nx = g.record(pi, **kwargs)

            if include_heat:
                kwargs['plotid'] = heat_id
                kwargs['x'] = nx
                kwargs['track_x'] = False if include_temp else track_x
                g.record(hi, **kwargs)

            buf_x.append(nx)

        try:
            g.update_y_limits(plotid=temp_id)
        except IndexError:
            pass

        try:
            g.update_y_limits(plotid=heat_id)
        except IndexError:
            pass

        if self.include_pressure:
            self._get_pressure(nx)

        if self.active:
            self._write_data(data, buf_x)

#         self.data_buffer = []
#         self.data_buffer_x = []
#         self.data_count_flag = 0
#===============================================================================
# datamanager
#===============================================================================
    def _write_data(self, buf, buf_x):
        if isinstance(self.data_manager, CSVDataManager):
            self._write_csv_data(buf, buf_x)
        else:
            self._write_h5_data(buf, buf_x)

    def _write_h5_data(self, buf, buf_x):
        dm = self.data_manager
        for ((name, _, pi, hp), xi) in zip(buf, buf_x):

            for (ti, di) in [('temp', pi), ('heat', hp)]:
                table = dm.get_table(ti, name)
                if table is not None:
                    row = table.row
                    row['time'] = xi
                    row['value'] = di
                    row.append()
                    table.flush()

    def _write_csv_data(self, buf, buf_x):
        ns = sum(map(int, [self.include_heat,
                           self.include_pressure, self.include_temp])) + 1
        container = [0, ] * ns * self._nactivated_controllers

        for (sub, x) in zip(buf, buf_x):
            s = 1
            (_, pid, pi, hp) = sub

            ind = pid * ns
            container[ind] = x

            if self.include_temp:
                container[ind + s] = pi
                s += 1

            if self.include_heat:
                container[ind + s] = hp
                s += 1

            if self.include_pressure:
                container[ind + s] = self._pressure

        for i in range(self._nactivated_controllers):
            ind = i * ns
            if container[ind] < 0.001:
                container[ind] = x

        self.data_manager.write_to_frame(container)

#===============================================================================
# classifier
#===============================================================================
    def _classifier_save(self):
        if self.confirmation_dialog('Use data for classification'):
            classification = self.confirmation_dialog('Classify this bake as successful?')

            gxs, gys, gps = self._assemble_classifier_data()
            classifier = Classifier()
            classifier.add_to_training_data(gxs, gys, gps, int(classification))

    def _classify(self):
        classifier = Classifier()

        gxs, gys, gps = self._assemble_classifier_data()
        obs = classifier.assemble_observation(gxs, gys, gps)
        return classifier.sv_classify(obs)

    def _assemble_classifier_data(self):
#        dm = H5DataManager()
        dm = self.data_manager
#        dm.open_data(self._current_data_path)
        controllers = dm.get_groups()
        gxs = []
        gys = []
        gps = []

        # use only the first 10 minutes of data
        npts = 10 * 60 / float(self.update_interval)
        for ci in controllers:
            temptable = ci.temp[:npts]
            heattable = ci.heat[:npts]
            gxs.append([x['time'] for x in temptable])
            gys.append([x['value'] for x in temptable])
            gps.append([x['value'] for x in heattable])
        return gxs, gys, gps
#===============================================================================
# database
#===============================================================================
    def _db_save(self):
#        if not self.db_save_dialog():
##            self._db_rollback()
#        else:
#            self.database.commit()

        if self.db_save_dialog():
#            controllers=self._get_controllers()
#            path=self._current_data_path
            self._add_bakeout_to_db()
        else:
            if self.data_manager:
                self.data_manager.delete_frame()
                
        if self.data_manager is not None:
            self.data_manager.close_file()
    
#    def _db_rollback(self):
#        self.info('rolling back')
##        self.database.rollback()
#        self.database.close()
#        if self.data_manager:
#            self.data_manager.delete_frame()

    def _add_bakeout_to_db(self):
        controllers=self._get_controllers()
        path=self._current_data_path
        db = self.database
        with db.session_ctx():
            # add to BakeoutTable
            b = db.add_bakeout()
            b.timestamp = datetime.datetime.now()
            # add to PathTable
            db.add_path(b, path)
    
            # add to ControllerTable
            for c in controllers:
                db.add_controller(b, name=c.name, script=c.script,
                                  setpoint=c.setpoint, duration=c.duration)
#===============================================================================
# handlers
#===============================================================================
    @on_trait_change('bakeout+:active')
    def update_active(self, obj, name, old, new):
        if new:
            self.active = new
        else:
            self.active = bool(len(self._get_active_controllers()))

    def _scan_window_changed(self):
        dl = self.scan_window * 60 / self.update_interval
        self.graph.set_data_limits(dl)

        mi, _ = self.graph.get_x_limits()
        self.graph.set_x_limits(min_=mi, max_=mi + self.scan_window * 60)

    def _update_interval_changed(self):
#         for tr in self._get_controller_names():
#             bc = self.trait_get(tr)[tr]
#             bc.update_interval = self.update_interval
#             bc.
        v = self.update_interval
        for ci in self._get_controllers():
            if ci._timer:
                ci._timer.set_interval(v)
            ci.update_interval = v

        self.graph.set_scan_delay(v)

        dl = self.scan_window * 60 / v
        self.graph.set_data_limits(dl)


    def _configuration_changed(self):
        for tr in self._get_controller_names():
            kw = dict()
            tr_obj = getattr(self, tr)
            for attr, v in [('duration', 0),
                             ('setpoint', 0),
                             ('record_process', False)]:
                kw[attr] = v

            kw['script'] = '---'
            tr_obj.trait_set(**kw)

        if self.configuration is not '---':
            self._parse_config_file(os.path.join(paths.bakeout_config_dir, self.configuration))

    def _active_changed(self, name, old, new):
        if old and not new and not self._suppress_commit:
            if self.database is not None:
                ok_to_commit = True
                user_cancel = any([tr.user_cancel for tr in self._get_controllers()])
                if user_cancel:
                    ok_to_commit = self.db_save_dialog()

                if ok_to_commit:
                    if self.training_run:
                        self._classifier_save()

                    self._add_bakeout_to_db()
#                    self._db_save()
#                    self.info('commit session to db')
#                    invoke_in_main_thread(self.database.commit)

                    time.sleep(0.5)
                    invoke_in_main_thread(self.open_latest_bake)

#                else:
#                    self._db.rollback()

            if self.data_manager is not None:
                self.data_manager.close_file()

    @on_trait_change('include_+')
    def _toggle_graphs(self):
        self.graph = self._graph_factory()
        self.reset_general_scan()

    def _graph_thread(self):
        dq = self.data_queue
        n = len(self._get_controller_names())
        while 1:
            while dq.qsize() < n:
                time.sleep(0.1)

            data = [dq.get() for _ in range(n)]
            invoke_in_main_thread(self._do_graph,data)

    @on_trait_change('bakeout+:process_value_flag')
    def _update_graph_temperature(self, obj, name, old, new,):
        try:
            pid = self.graph_info[obj.name]['id']
        except KeyError:
            return

        pv = getattr(obj, 'process_value')
        hp = getattr(obj, 'heat_power_value')

        self.data_queue.put((obj.name, pid, pv, hp))

#==============================================================================
# Button handlers
#==============================================================================
    def _save_fired(self):

        path = self._file_dialog_('save as',
                                  default_directory=paths.bakeout_config_dir)

        if not path.endswith('.cfg'):
            path += '.cfg'

        if path is not None:
            config = self.get_configuration_writer()
            config.add_section('Include')
            config.set('Include', 'temp', self.include_temp)
            config.set('Include', 'heat', self.include_heat)
            config.set('Include', 'pressure', self.include_pressure)

            config.add_section('Scan')
            config.set('Scan', 'interval', self.update_interval)
            config.set('Scan', 'window', self.scan_window)

            for tr in self._get_controller_names():
                tr_obj = getattr(self, tr)
                config.add_section(tr)

                script = getattr(tr_obj, 'script')
                if script != '---':
                    config.set(tr, 'script', script)
                else:
                    for attr in ['duration', 'setpoint', 'record_process']:
                        config.set(tr, attr, getattr(tr_obj, attr))

            with open(path, 'w') as f:
                config.write(f)

            self._configurations_dirty = True
            self.configuration = os.path.basename(path)

    def _execute_fired(self):
        if self.active:
            self._suppress_commit = True
            if self.training_run:
                self._classifier_save()

            self._db_save()

            for c in self._get_controllers():
                c.end()

            self._suppress_commit = False

            self.reset_data_recording()
#            self.reset_general_scan()

        else:
            self.reset_data_recording()
            for c in self._get_controllers():
                if c.ok_to_run:
                    c.run()
                c.state_enabled = True
#                    self._training_controllers.append(c.name)
#                    states.append(True)
#===============================================================================
# property get/set
#===============================================================================
    @cached_property
    def _get_configurations(self):
        cs = ['---']
        for p in os.listdir(paths.bakeout_config_dir):
            if os.path.splitext(p)[1] == '.cfg':
                cs.append(p)
        return cs

    def _get_execute_label(self):
        return 'Stop' if self.active else 'Execute'

    def _get_controller_names(self):
        '''
        '''
        c = [tr for tr in self.traits() if tr.startswith('bakeout')]
        c.sort()
        return c

    def _get_controllers(self):
        return [getattr(self, tr)
                for tr in self._get_controller_names()]

    def _get_active_controllers(self):
        return [tr for tr in self._get_controllers()
                    if tr.isActive()]

    def _get_execute_ok(self):
        include_bit = sum(map(int, [self.include_temp, self.include_heat,
                             self.include_pressure])) > 0

        ok_to_run_bit = any([tr.ok_to_run for tr in self._get_controllers()])
        return include_bit and ok_to_run_bit

#===============================================================================
# factories
#===============================================================================
    def _controller_factory(self, name):
        bc = BakeoutController(name=name,
                               configuration_dir_name='bakeout',
                               update_interval=self.update_interval)
        return bc

    def _data_manager_factory(self, controllers, header, style='csv'):
        from pychron.managers.data_managers.h5_data_manager import H5DataManager

        dm = CSVDataManager() if style == 'csv' else H5DataManager()

        ni = 'bakeout-{}'.format(generate_datestamp())

        dw = DataWarehouse(root=paths.bakeout_db_root)
        dw.build_warehouse()

        _dn = dm.new_frame(directory=dw.get_current_dir(),
                           base_frame_name=ni,
                           )
#         dm.new_frame(os.path.join(paths.data_dir, 'foo.hdf5'))
        if style == 'csv':
            d = map(str, map(int, [self.include_temp,
                    self.include_heat, self.include_pressure]))
            d[0] = '#' + d[0]
            dm.write_to_frame(d)

            # set the header in for the data file
            dm.write_to_frame(header)
        else:
            for ci in controllers:
                cgrp = dm.new_group(ci.name)
                dm.new_table(cgrp, 'temp')
                dm.new_table(cgrp, 'heat')
                if self.include_pressure:
                    dm.new_table(cgrp, 'pressure')

                for attr in ['script', 'setpoint',
                             'duration', 'max_output']:
                    dm.set_group_attribute(cgrp, attr, getattr(ci, attr))

                if ci.script != '---':
                    p = os.path.join(paths.scripts_dir, 'bakeout', ci.script)
                    with open(p, 'r') as f:
                        txt = f.read()
                else:
                    txt = ''
                dm.set_group_attribute(cgrp, 'script_text', txt)
        return dm

    def _graph_factory(
        self,
        stream=True,
        graph=None,
        include_bits=None,
        panel_height=None,
        plot_kwargs=None,
        **kw
        ):

        if plot_kwargs is None:
            plot_kwargs = dict()

        if include_bits is None:
            include_bits = [self.include_temp, self.include_heat,
                            self.include_pressure]

        n = max(1, sum(map(int, include_bits)))
        if graph is None:

            if stream:
                graph = TimeSeriesStreamStackedGraph(panel_height=435 / n,
                                    container_dict=dict(padding_top=30),
                         **kw)
            else:
                if panel_height is None:
                    ds = get_display_size()
                    panel_height = ds.height * 0.65 / n

                graph = \
                    TimeSeriesStackedGraph(panel_height=panel_height, **kw)

        graph.clear()
        kw['data_limit'] = self.scan_window * 60 / self.update_interval
        kw['scan_delay'] = self.update_interval

        self.plotids = [0, 1, 2]

        # temps

        if include_bits[0]:
            p = graph.new_plot(show_legend='ll', **kw)
            graph.set_y_title('Temp (C)')
            p.x_grid.visible = False
        else:
            self.plotids = [0, 0, 1]

        # heat power

        if include_bits[1]:
            p = graph.new_plot(**kw)
            p.x_grid.visible = False
            graph.set_y_title('Heat Power (%)', plotid=self.plotids[1])
        elif not include_bits[0]:
            self.plotids = [0, 0, 0]
        else:
            self.plotids = [0, 0, 1]

        # pressure

        if include_bits[2]:
            p = graph.new_plot(**kw)
            p.x_grid.visible = False
            graph.set_y_title('Pressure (torr)', plotid=self.plotids[2])

        if include_bits:
            graph.set_x_title('Time')
            graph.set_x_limits(0, self.scan_window * 60)

        return graph
#===============================================================================
# defaults
#===============================================================================
    def _graph_default(self):
        g = self._graph_factory()
        return g

#    def _script_editor_default(self):
#        return PyScriptManager(kind='Bakeout',
#                               default_directory_name='bakeout'
#                               )

#        kw = dict(kind='Bakeout',
#                  default_directory_name='bakeoutscripts')
#        if self.script_style == 'pyscript':
#            klass = PyScriptManager
#            kw['execute_visible'] = False
#        else:
#            klass = ScriptManager
#
#        m = klass(**kw)
#        return m

    def _database_default(self):
        db = BakeoutAdapter(
#                            name='/Users/ross/Sandbox/bakeout.sqlite',
                            name=paths.bakeout_db,
#                            password='Argon',
                            kind='sqlite',
                            application=self.application
                            )
        try:
            db.manage_database()
        except Exception, e:
            import traceback
            self.debug(traceback.format_exc())
        db.connect()

        return db

#==============================================================================
# Pressure
#==============================================================================
    def _get_pressure(self, x):
        if self.gauge_controller:
            pressure = self.gauge_controller.get_ion_pressure()
        else:
            import random
            pressure = random.randint(0, 10)

        self._pressure = pressure
        self.graph.record(
            pressure,
            x=x,
            track_y=(5e-3, None),
            track_y_pad=5e-3,
            track_x=False,
            plotid=self.plotids[2],
#            do_later=10,
            )

        if self.use_pressure_monitor:
            dbuffer = self.pressure_buffer
            window = 100

            dbuffer = hstack((dbuffer[-window:], pressure))
            n = len(dbuffer)
            std = dbuffer.std()
            mean = dbuffer.mean()
            if std < self._pressure_monitor_std_threshold:
                if mean < self._pressure_monitor_threshold:
                    self.info('pressure set point achieved:mean={} std={} n={}'.format(mean,
                              std, n))

            dtime = self._start_time - time.time()
            if dtime > self._max_duration:
                for ac in self._get_active_controllers():
                    error = \
                        'Max duration exceeded max={:0.1f}, dur={:0.1f}'.format(self._max_duration,
                            dtime)
                    ac.end(error=error)

if __name__ == '__main__':
    path = os.path.join(paths.data_dir, 'bakeouts', 'bakeout-2012-03-31007.txt')
    b = BakeoutManager()
    b.load()
    b._add_bakeout_to_db()
# ============= EOF ====================================

#    b._convert_to_h5(path)
#    n = 10
#    from timeit import Timer
#    t = Timer('load_h5()', 'from __main__ import load_h5')
#    h5_time = t.timeit(n) / float(n)
#    print 'h5', h5_time
#
#    t = Timer('load_csv()', 'from __main__ import load_csv')
#    csv_time = t.timeit(n) / float(n)
#
#    print 'csv', csv_time
# def _execute2_(self):
#        '''
#        '''
#        self._buffer_lock = Lock()
#        pid = 0
#        header = []
#        self.data_buffer = []
#        self.data_buffer_x = []
#        self.data_count_flag = 0
#        for c in self._get_controllers():
#            c.stop_timer()
#
#        self.graph = self._graph_factory()
#
#        controllers = []
#        for bc in self._get_controllers():
#            name = bc.name
# #        for name in self._get_controller_names():
# #            bc = self.trait_get(name)[name]
#            if bc.ok_to_run():
#
#                bc.on_trait_change(self.update_alive, 'active')
#
#                # set up graph
# #                self.graph.new_series()
# #                self.graph_info[bc.name] = dict(id=pid)
# #
# #                self.graph.set_series_label(name, series=pid)
#
# #                if self.include_heat:
# #                    self.graph.new_series(plotid=self.plotids[1])
#                self._setup_graph(name, pid)
#                if pid == 0:
#                    header.append('#{}_time'.format(name))
#                else:
#                    header.append('{}_time'.format(name))
#
#                if self.include_temp:
#                    header.append('{}_temp'.format(name))
#
#                if self.include_heat:
#                    header.append('{}_heat_power'.format(name))
#
#                if self.include_pressure:
#                    header.append('pressure')
#
#                controllers.append(bc)
#
#                pid += 1
#
#        if controllers:
#            self.data_manager = self._data_manager_factory(controllers, header,
#                                                           style='h5')
#
#            self._add_bakeout_to_db(controllers,
#                                    self.data_manager.get_current_path())
#
#            self._nactivated_controllers = len(controllers)
#            pv = ProcessView()
#            for c in controllers:
#                c.run()
#                try:
#                    a = c._active_script
#                    if a is not None:
#                        pv.add_script(c.name, a)
#                except Exception, _e:
#                    #this isnt a .bo script not currently conducive to process view
#                    pass
#
#            if pv.scripts:
#                do_later(pv.edit_traits)
#
# #            time.sleep(0.5)
#            for c in controllers:
#                c.start_timer()
#
#            if self.include_pressure:
#                # pressure plot
#                self.graph.new_series(type='line',
#                        render_style='connectedpoints',
#                        plotid=self.plotids[2])
#
#            # start a pressure monitor thread
# #                t = Thread(target=self._pressure_monitor)
# #                t.start()
#
#            self._start_time = time.time()
#        else:
#            self.active = False
#            self.reset_general_scan()

#    def _pressure_monitor(self):
#
#        window = 100
#
#        st = time.time()
#
#
#        dbuffer = np.array([])
#
#        success = False
#        while time.time() - st < self._max_duration * 60 * 60:
#
#            nv = self.gauge_controller.get_convectron_a_pressure()
#            self._pressure = nv
#            self.graph.record(nv, track_y=(5e-3, None), track_y_pad=5e-3,
#                    track_x=False, plotid=2, do_later=10)
#
#            if self.use_pressure_monitor:
#                dbuffer = np.hstack((dbuffer[-window:], nv))
#                n = len(dbuffer)
#                std = dbuffer.std()
#                mean = dbuffer.mean()
#                if std < self._pressure_monitor_std_threshold:
#                    if mean < self._pressure_monitor_threshold:
#                        self.info('pressure set point achieved:mean={} std={}
#                                     n={}'.format(mean, std, n))
#                        success = True
#                        break
#
#            time.sleep(self._pressure_sampling_period)
#            if not self.isAlive():
#                break
#
#        for ac in self._get_active_controllers():
#            ac.end(error=None if success else 'Max duration exceeded max={:0.1f}, dur={:0.1f}'.format(self._max_duration,

#    def _convert_to_h5(self, path):
#        args = self._bakeout_csv_parser(path)
#        (names, nseries, ib, data, path, attrs) = args
#        dm = H5DataManager()
#        dm.new_frame()
#        for n, d in zip(names, data):
#            g = dm.new_group(n)
#            print d.transpose()
#            dm.new_array('/{}'.format(n), 'data', d.transpose())
#
#        dm.close()
#    def traits_view(self):
#        '''
#        '''
#        controller_grp = HGroup()
#        for tr in self._get_controller_names():
#            controller_grp.content.append(Item(tr,
#                                               show_label=False, style='custom'))
#
#        control_grp = HGroup(
#                             VGroup(Item('execute',
#                                         editor=ButtonEditor(label_value='execute_label'), show_label=False,
#                                         enabled_when='execute_ok'),
#                                    HGroup(spring, Item('training_run', label='Training Run'))
#                                    ),
#                             HGroup(Item('configuration',
#                                         editor=EnumEditor(name='configurations'),
#                                         show_label=False),
#                                    Item('save',
#                                         show_label=False)),
#                             VGroup('include_pressure',
#                                    'include_heat',
#                                    'include_temp', enabled_when='not active'),
#                             label='Control', show_border=True
#                             )

#        scan_grp = VGroup(Item('update_interval',
#                          label='Sample Period (s)'), Item('scan_window'
#                          , label='Data Window (mins)'), label='Scan',
#                          show_border=True)
#
#        pressure_grp = VGroup(
#                              HGroup(
#                                     Item('use_pressure_monitor'),
#                                     Item('_pressure_sampling_period',
#                                          label='Sample Period (s)')),
#                              VGroup(
#                                     Item('_max_duration',
#                                          label='Max. Duration (hrs)'),
#                                     Item('_pressure_monitor_std_threshold'),
#                                     Item('_pressure_monitor_threshold'),
#                                          enabled_when='use_pressure_monitor'
#                                     ),
#                                     label='Pressure', show_border=True
#                            )
#        v = View(VGroup(
#                        HGroup(control_grp,
#                               HGroup(scan_grp, pressure_grp,
#                                      enabled_when='not active')
#                               ),
#                        controller_grp,
#                        Item('graph', show_label=False, style='custom')),
#                 handler=AppHandler,
#                 resizable=True, title='Bakedpy', height=830)
#        return v
# def launch_bakeout():
#    b = BakeoutManager()
#    b.load()
#    b.configure_traits()

# #bm = BakeoutManager()
#
#
# def load_h5():
#    bm._bakeout_h5_parser(path + '.h5')
#
#
# def load_csv():
#    bm._bakeout_csv_parser(path + '.txt')
