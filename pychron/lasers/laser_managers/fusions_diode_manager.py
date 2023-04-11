# ===============================================================================
# Copyright 2011 Jake Ross
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

# =============enthought library imports=======================
from traits.api import Instance, Button, Bool, Float
from traitsui.api import VGroup, Item, InstanceEditor

from pychron.lasers.laser_managers.pyrometer_mixin import PyrometerMixin
from pychron.lasers.laser_managers.watlow_mixin import WatlowMixin
from .fusions_laser_manager import FusionsLaserManager
from pychron.hardware.fusions.fusions_diode_logic_board import FusionsDiodeLogicBoard
from pychron.hardware.mikron_pyrometer import MikronGA140Pyrometer
from pychron.hardware.pyrometer_temperature_monitor import PyrometerTemperatureMonitor
from pychron.hardware.temperature_monitor import DPi32TemperatureMonitor
from pychron.lasers.laser_managers.vue_metrix_manager import VueMetrixManager
from pychron.monitors.fusions_diode_laser_monitor import FusionsDiodeLaserMonitor
from pychron.response_recorder import ResponseRecorder


class FusionsDiodeManager(FusionsLaserManager, WatlowMixin, PyrometerMixin):
    """ """

    stage_manager_id = "fusions.diode"
    id = "pychron.fusions.diode"
    name = "FusionsDiode"
    configuration_dir_name = "fusions_diode"

    temperature_monitor = Instance(DPi32TemperatureMonitor)
    control_module_manager = Instance(VueMetrixManager)
    pyrometer_temperature_monitor = Instance(PyrometerTemperatureMonitor)

    tune = Button
    configure = Button
    tuning = Bool

    monitor_name = "diode_laser_monitor"
    monitor_klass = FusionsDiodeLaserMonitor

    request_power = Float
    request_powermin = Float(0)
    request_powermax = Float(1500)

    pyrometer_klass = MikronGA140Pyrometer

    def get_laser_internal_temperature(self, **kw):
        """ """
        return self._try("control_module_manager", "get_internal_temperature", kw)

    def get_power_slider(self):
        return None

    def emergency_shutoff(self, *args, **kw):
        super(FusionsDiodeManager, self).emergency_shutoff(*args, **kw)
        self.control_module_manager.disable()

    # ===============================================================================
    # private
    # ===============================================================================

    def _enable_hook(self):
        if super(
            FusionsDiodeManager, self
        )._enable_hook():  # logic board sucessfully enabled
            # disable the temperature_controller unit a value is set
            self.temperature_controller.disable()

            self.response_recorder.start("diode_response_tc_control")
            if self.pyrometer:
                self.pyrometer.start_scan()
            return self.control_module_manager.enable()

    def _disable_hook(self):
        self.response_recorder.stop()
        self.temperature_controller.disable()
        self.control_module_manager.disable()

        if self.pyrometer:
            self.pyrometer.stop_scan()

        return super(FusionsDiodeManager, self)._disable_hook()

    def _try(self, obj, func, kw):
        try:
            obj = getattr(self, obj)
            func = getattr(obj, func)
            return func(**kw)

        except AttributeError:
            pass

    # ===============================================================================
    # views
    # ===============================================================================
    def get_additional_controls(self):
        #        v = Group(
        gs = [
            VGroup(
                Item(
                    "temperature_controller",
                    style="custom",
                    editor=InstanceEditor(view="control_view"),
                    show_label=False,
                ),
                label="Watlow",
            ),
            VGroup(
                Item("pyrometer", show_label=False, style="custom"), label="Pyrometer"
            ),
            VGroup(
                Item("control_module_manager", show_label=False, style="custom"),
                label="ControlModule",
            ),
            VGroup(
                Item("fiber_light", style="custom", show_label=False),
                label="FiberLight",
            ),
        ]
        return gs

    # ===============================================================================
    # defaults
    # ===============================================================================

    def _response_recorder_default(self):
        r = ResponseRecorder(
            response_device=self.temperature_controller,
            # response_device_secondary = self.temperature_monitor,
            response_device_secondary=self.pyrometer,
            output_device=self.temperature_controller,
        )
        return r

    def _temperature_monitor_default(self):
        tm = DPi32TemperatureMonitor(
            name="temperature_monitor",
            configuration_dir_name=self.configuration_dir_name,
        )
        return tm

    def _laser_controller_default(self):
        b = FusionsDiodeLogicBoard(
            name="laser_controller",
            configuration_name="laser_controller",
            configuration_dir_name=self.configuration_dir_name,
        )
        return b

    def _pyrometer_temperature_monitor_default(self):
        py = PyrometerTemperatureMonitor(
            name="pyrometer_tm", configuration_dir_name=self.configuration_dir_name
        )
        return py

    def _title_default(self):
        return "Diode Manager"

    def _control_module_manager_default(self):
        v = VueMetrixManager()  # control = self.control_module)
        return v


if __name__ == "__main__":
    from pychron.core.helpers.logger_setup import logging_setup
    from pychron.envisage.initialization.initializer import Initializer

    logging_setup("fusions diode")
    f = FusionsDiodeManager()
    f.use_video = True
    f.record_brightness = True
    ini = Initializer()

    a = dict(manager=f, name="FusionsDiode")
    ini.add_initialization(a)
    ini.run()
    #    f.bootstrap()
    f.configure_traits()

# ======================= EOF ============================
#    def finish_loading(self):
#        super(FusionsDiodeManager, self).finish_loading()
#
#        self.pyrometer.start_scan()
# #        self.control_module_manager.start_scan()
# def open_scanner(self):
#    from pychron.lasers.scanner import PIDScanner
#
#    self._open_scanner(PIDScanner, 'scanner.yaml')
#
# def open_autotuner(self):
#    from pychron.lasers.autotuner import AutoTuner
#
#    self._open_scanner(AutoTuner, 'autotuner.yaml')
#
# def _open_scanner(self, klass, name):
#    from pychron.lasers.scanner import ScannerController
#
#    p = os.path.join(paths.scripts_dir, name)
#
#    s = klass(control_path=p,
#              manager=self
#    )
#
#    tc = self.temperature_controller
#    tm = self.get_device('temperature_monitor')
#
#    def tc_gen():
#        while 1:
#            pr = tc.get_temp_and_power(verbose=False)
#            for pi in pr.data:
#                yield pi
#
#    # populate scanner with functions
#    gen = tc_gen()
#    s.setup(directory='diode_autotune_scans')
#    s.new_function(gen, name='Temp. Pyrometer (C)')
#    s.new_function(gen, name='Power (%)')
#
#    if tm is not None:
#        func = partial(tm.read_temperature, verbose=False)
#        s.new_function(func, name='Reflector Temp (C)')
#
#    # bind to request_power change. set Setpoint static value
#    s.new_static_value('Setpoint')
#    self.on_trait_change(lambda v: s.set_static_value('Setpoint', v), self._requested_power)
#
#    # bind to Scanner's stop_event. Set laser power to 0.
#    s.on_trait_change(lambda: self.set_laser_temperature(0), 'stop_event')
#
#    # bind to Scanners setpoint
#    #        s.on_trait_change(lambda v: self.set_laser_temperature(v), 'setpoint')
#
#    sc = ScannerController(model=s,
#                           application=self.application)
#    self.open_view(sc)

# def bind_preferences(self, pref_id):
#     super(FusionsDiodeManager, self).bind_preferences(pref_id)
#     bind_preference(self, 'use_calibrated_temperature', '{}.use_calibrated_temperature'.format(pref_id))

#    def get_laser_amps(self):
#        '''
#        '''
#        return self.control_module.read_laser_amps()
#
#    def get_laser_current(self):
#        '''
#        '''
#        return self.control_module.read_laser_current_adc()

#    def get_laser_power(self):
#        '''
#        '''
#        return self.control_module.read_laser_power_adc()
#
#    def get_measured_power(self):
#        '''
#        '''
#        return self.control_module.read_measured_power()
#    def disable_laser(self):
#        '''
#        '''
#        if self.fiber_light.auto_onoff and not self.fiber_light.state:
#            self.fiber_light.power_on()
#
#        self.temperature_controller.disable()
#        self.control_module_manager.disable()
#
#        super(FusionsDiodeManager, self).disable_laser()
#
#        return True

#    def get_degas_manager(self):
#        from degas_manager import DegasManager
#
# #        path = self.open_file_dialog(default_directory = os.path.join(scripts_dir,
# #                                                                      'laserscripts',
# #                                                                      'degas'
# #                                                                      )
# #                                     )
#
#        path = '/Users/pychron/Pychrondata_beta/scripts/laserscripts/degas/puck1.rs'
#        if path:
#            dm = DegasManager()
#            dm.parent = self
#            dm.file_name = path
#            dm.new_script()
#            return dm


#    def launch_camera_scan(self):
#        '''
#        '''
#        p = os.path.join(paths.scripts_dir, 'laserscripts', 'camera_scans')
#        cs = CameraScanScript(manager = self, parent_path = p)
#        cs.open()
#
#    def launch_power_scan(self):
#        '''
#        overriding super
#        '''
#        p = os.path.join(paths.scripts_dir, 'laserscripts', 'diode_power_scans')
#        ps = DiodePowerScanScript(manager = self, parent_path = p)
#        ps.open()

#    def show_image_process(self):
#        '''
#        '''
#
#        vm = self.video_manager
#        p = os.path.join(paths.data_dir, 'video', 'testframe.png')
#        vm.process_frame(path=p)
#        vm.edit_traits(view='image_view')

#    def show_step_heater(self):
#
#        shm = StepHeatManager(laser_manager = self,
#                              video_manager = self.stage_manager.video_manager
#                              )
#        shm.edit_traits()

#    def show_pyrometer_calibration_manager(self):
#        '''
#        '''
#        c = CalibrationManager(diode_manager = self,
#                             style = 'pyrometer')
#        c.open()
#
#    def show_calibration_manager(self):
#        '''
#        '''
#
#        c = CalibrationManager(diode_manager = self)
#        c.open()

#    @on_trait_change('configure')
#    def _show_temperature_controller_configuration(self):
#        '''
#        '''
#        self.temperature_controller.edit_traits(view='configure_view')


#    def __watlow__group__(self):
#        '''
#        '''
#        return VGroup(Item('temperature_controller', style = 'custom', show_label = False),
#                      label = 'Watlow',
#                      show_border = True)
#
#    def __pyrometer__group__(self):
#        '''
#        '''
#        return VGroup(Item('pyrometer', show_label = False, style = 'custom'),
#                      show_border = True,
#                      label = 'Pyrometer')
#    def show_streams(self):
#        '''
#        '''
#
#        tc = self.temperature_controller
#        pyro = self.pyrometer
#        tm = self.pyrometer_temperature_monitor
#        apm = self.analog_power_meter
#        ipm = self.control_module
#
#
#        avaliable_streams = [apm, pyro, tc, tm, ipm]
#    @on_trait_change('tune')
#    def _tune_temperature_controller(self):
#        '''
#        '''
#        if not self.tuning:
#            tune = TuneThread(self)
#            tune.setDaemon(1)
#            tune.start()
#
#        self.tuning = not self.tuning

#    @on_trait_change('calibrate')
#    def _calibrate_power(self):
#        '''
#        '''
#
#        cm = CalibrationManager(parent = self)
#        cm._calibrate_()
#        cm.edit_traits(kind = 'livemodal')


#    def _devices_default(self):
#        '''
#        '''
#        return [self.pyrometer,
#                self.temperature_controller,
#                self.temperature_monitor,
#                self.analog_power_meter,
#                self.logic_board,
#                self.control_module,
#                self.stage_controller]

#    def launch_power_profile(self):
#        '''
#        '''
#        self.logger.info('launching power profile')
#
#        sm = self.stream_manager
#        tc = self.temperature_controller
#        pyro = self.pyrometer
#        stm = self.stage_manager
#        apm = self.analog_power_meter
#
#        self.raster_manager = rm = RasterManager(stream_manager = sm)
#
#        if not stm.centered:
#            self.warning('Please set a center position')
#
#            return
#        p=os.path.join(preferences.root,'laserscripts','beamprofile.txt')
#        pt = BeamProfileThread(self,p)
#        rm.set_canvas_parameters(pt.steps, pt.steps)
#
#        if sm.open_stream_loader([pyro, tc, apm]):
#            self.dirty = True
#
#            #setup the data frame
#            dm = sm.data_manager
#            if not self.streaming:
#                self.streaming = True
#
#                dm.add_group('molectron')
#            for i in range(10):
#                dm.add_group('row%i' % i, parent = 'root.molectron')
#                for j in range(10):
#                    dm.add_group('cell%i%i' % (i, j), parent = 'root.molectron.row%i' % i)
#                    dm.add_table('power', parent = 'root.molectron.row%i.cell%i%i' % (i, i, j))
#
#            #stm.edit_traits(kind = 'livemodal')
#            pt.center_x = stm.center_x
#            pt.center_y = stm.center_y
#
#            pt.start()
#            rm.edit_traits()
#    def get_calibration_menu(self):
#        d = super(FusionsDiodeManager, self).get_calibration_menu()
#        dn = d[1] + [#dict(name='Calibrate',action='show_calibration_manager'),
#                 dict(name = 'Calibrate Pyrometer', action = 'show_pyrometer_calibration_manager'),
#                 dict(name = 'Camera Scan', action = 'launch_camera_scan'),
#                 dict(name = 'Image Process', action = 'show_image_process')
#                 ]
#        return (d[0], dn)
#    def get_control_buttons(self):
#        '''
#        '''
#        v = super(FusionsDiodeManager, self).get_control_buttons()
#        return v + [('pointer', None, None),
#                  #('enable', None, None),
#                  #('interlock', None, None)
#                  ]

#    def get_menus(self):
#        '''
#        '''
#        m = super(FusionsDiodeManager, self).get_menus()
#
#
#
#        m += [('Calibration', [
#                                  dict(name = 'Tune', action = '_tune_temperature_controller'),
#                                  dict(name = 'Calibrate', action = '_calibrate_power'),
#                                  #dict(name='Open Graph',action='_open_graph'),
#                                  dict(name = 'Power Profile', action = 'launch_power_profile'),
#                                  ]
#                                ),
#
# #            ('Streams', [dict(name = 'Stop', action = 'stop_streams', enabled_when = 'streaming'),
# #                        dict(name = 'Stream ...', action = '_launch_stream'),
# #                        dict(name='Save Graph ...', action ='_save_graph', enabled_when='dirty')
# #                        ])
#                ]
#        return m

#    def show_stats_view(self):
#        '''
#        '''
#
#        self.timer = t = Timer(1000, self._update_stats)
#        self.update_timers.append(t)
#        self.outputfile = open(os.path.join(paths.data_dir, 'laser_stats.txt'), 'w')
#        self.outputfile.write('time\tlaser power\tmeasured power\tlaser_current\tlaser amps\n')
#
#        self.edit_traits(view = 'stats_view')
#
#    def _update_stats(self):
#        '''
#        '''
#        self.laser_power = lp = self.get_laser_power()
#        self.laser_measured_power = lm = self.get_measured_power()
#        self.laser_current = lc = self.get_laser_current()
#        self.laser_amps = la = self.get_laser_amps()
#        self.outputfile.write('%s\n' % '\t'.join(('%0.3f' % time.time(), '%s' % lp, '%s' % lm, '%s' % lc, '%s' % la)))
#
#    def _request_amps_changed(self):
#        '''
#        '''
#        self.control_module.set_request_amps(self.request_amps)
#
#    def stats_view(self):
#        '''
#        '''
#        v = View(VGroup(Item('request_amps'),
#                      Item('laser_power'),
#                      Item('laser_measured_power'),
#                      Item('laser_current'),
#                      Item('laser_amps'),
#                    ),
#                    resizable = True,
#                    handler = UpdateHandler
#                )
#        return v
