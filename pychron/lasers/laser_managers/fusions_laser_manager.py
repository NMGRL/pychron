# ===============================================================================
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
# ===============================================================================

# =============enthought library imports=======================
from apptools.preferences.preference_binding import bind_preference
from traits.api import (
    DelegatesTo,
    Instance,
    Str,
    List,
    Dict,
    on_trait_change,
    Event,
    Bool,
    Any,
)
from traitsui.api import HGroup, spring, UReadonly, Readonly

from pychron.core.helpers.strtools import to_bool
from pychron.core.pychron_traits import BorderVGroup
from pychron.hardware.fiber_light import FiberLight
from pychron.hardware.fusions.fusions_logic_board import FusionsLogicBoard
from pychron.lasers.laser_managers.laser_manager import LaserManager
from pychron.response_recorder import ResponseRecorder


class FusionsLaserManager(LaserManager):
    """ """

    laser_controller = Instance(FusionsLogicBoard)
    fiber_light = Instance(FiberLight)
    response_recorder = Instance(ResponseRecorder)

    power_timer = None
    brightness_timer = None

    power_graph = None
    _prev_power = 0
    record_brightness = Bool
    #     recording_zoom = Float

    #     record = Event
    #     record_label = Property(depends_on='_recording_power_state')
    _recording_power_state = Bool(False)

    simulation = DelegatesTo("laser_controller")

    data_manager = None
    _data_manager_lock = None

    _current_rid = None

    chiller = Any

    motor_event = Event

    def finish_loading(self):
        super(FusionsLaserManager, self).finish_loading()
        self.do_motor_initialization()

    # ===============================================================================
    #   IExtractionDevice interface
    # ===============================================================================
    def stop_measure_grain_polygon(self):
        return self.stage_manager.stop_measure_grain_polygon()

    def start_measure_grain_polygon(self):
        return self.stage_manager.start_measure_grain_polygon()

    def get_grain_polygon(self):
        return self.stage_manager.get_grain_polygon()

    def get_grain_polygon_blob(self):
        return self.stage_manager.get_grain_polygon_blob()

    def extract(self, power, units=None, **kw):
        if self.enable_laser():
            self.set_laser_power(power, units=units)

    def end_extract(self):
        self.disable_laser()
        self.stop_pattern()

    def open_motor_configure(self):
        self.laser_controller.open_motor_configure()

    def bind_preferences(self, pref_id):
        self.debug("binding preferences")
        super(FusionsLaserManager, self).bind_preferences(pref_id)
        bind_preference(self, "recording_zoom", "{}.recording_zoom".format(pref_id))
        bind_preference(
            self, "record_brightness", "{}.record_brightness".format(pref_id)
        )
        self.debug("preferences bound")

    def set_light(self, value):
        try:
            value = float(value)
        except ValueError:
            return
        self.set_light_state(value > 0)
        self.set_light_intensity(value)

    def set_light_state(self, state):
        if state:
            self.fiber_light.power_on()
        else:
            self.fiber_light.power_off()

    def set_light_intensity(self, v):
        self.fiber_light.intensity = min(max(0, v), 100)

    @on_trait_change("laser_controller:refresh_canvas")
    def refresh_canvas(self):
        if self.stage_manager:
            self.stage_manager.canvas.request_redraw()

    # @on_trait_change('pointer')
    # def pointer_ononff(self):
    #     """
    #     """
    #     self.pointer_state = not self.pointer_state
    #     self.laser_controller.set_pointer_onoff(self.pointer_state)

    def get_laser_watts(self):
        return self._requested_power

    def get_coolant_temperature(self, **kw):
        """ """
        chiller = self.chiller
        if chiller is not None:
            return chiller.get_coolant_out_temperature(**kw)

    def get_coolant_status(self, **kw):
        chiller = self.chiller
        if chiller is not None:
            return chiller.get_faults(**kw)

    def do_motor_initialization(self):
        self.debug("do motor initialization")

        if self.laser_controller:
            for motor in self.laser_controller.motors:
                # motor = self.laser_controller.get_motor(name)
                # if motor is not None:
                def handle(obj, name, old, new):
                    # self.motor_event = (motor.name, new)
                    self.stage_manager.motor_event_hook(obj.name, new)

                motor.on_trait_change(handle, "_data_position")

    def set_beam_diameter(self, bd, force=False, **kw):
        """ """
        result = False
        motor = self.get_motor("beam")
        if motor is not None:
            if motor.enabled or force:
                self.set_motor("beam", bd, **kw)
                result = True

        return result

    def set_zoom(self, z, **kw):
        """ """
        self.set_motor("zoom", z, **kw)

    def set_motor_lock(self, name, value):
        m = self.get_motor(name)
        if m is not None:
            m.locked = to_bool(value)
            return True

    def set_motor(self, *args, **kw):
        self.stage_manager.motor_event_hook(*args, **kw)
        return self.laser_controller.set_motor(*args, **kw)

    def get_motor(self, name):
        return next(
            (mi for mi in self.laser_controller.motors if mi.name == name), None
        )

    def do_autofocus(self, **kw):
        if self.use_video:
            am = self.stage_manager.autofocus_manager
            am.passive_focus(block=True, **kw)

    def take_snapshot(self, *args, **kw):
        if self.use_video:
            return self.stage_manager.snapshot(auto=True, inform=False, *args, **kw)

    def start_video_recording(self, name="video", *args, **kw):
        if self.use_video:
            return self.stage_manager.start_recording(basename=name)

    def stop_video_recording(self, *args, **kw):
        if self.use_video:
            return self.stage_manager.stop_recording()

    # def degasser_factory(self):
    #     from pychron.mv.degas.degasser import Degasser
    #
    #     dm = Degasser(laser_manager=self)
    #     return dm
    #
    # def do_machine_vision_degas(self, lumens, duration, new_thread=False):
    #     if self.use_video:
    #         dm = self.degasser_factory()
    #
    #         def func():
    #             dm.degas(lumens, duration)
    #
    #         if new_thread:
    #             self._degas_thread = Thread(target=func)
    #             self._degas_thread.start()
    #         else:
    #             func()

    # def get_peak_brightness(self, **kw):
    #     if self.use_video:
    #         args = self.stage_manager.find_lum_peak(**kw)
    #         if args is not None:
    #             pt, peaks, cpeaks, lum = args
    #             return peaks, lum

    def get_brightness(self, **kw):
        if self.use_video:
            return self.stage_manager.get_brightness(**kw)
        else:
            return super(FusionsLaserManager, self).get_brightness(**kw)

    def luminosity_degas_test(self):
        self.enable_laser()
        p = self.pulse.power
        self.debug("luminosity degas test. {}".format(p))
        self._luminosity_hook(p, autostart=True)

    def set_stage_map(self, mapname):
        if self.stage_manager is not None:
            self.stage_manager.set_stage_map(mapname)

    # ===============================================================================
    # pyscript interface
    # ===============================================================================
    def show_motion_controller_manager(self):
        """ """
        stage_controller = self.stage_manager.stage_controller
        package = "pychron.managers.motion_controller_managers"
        if "Aerotech" in stage_controller.__class__.__name__:
            klass = "AerotechMotionControllerManager"
            package += ".aerotech_motion_controller_manager"
        else:
            klass = "NewportMotionControllerManager"
            package += ".newport_motion_controller_manager"

        module = __import__(package, globals(), locals(), [klass])
        factory = getattr(module, klass)
        m = factory(motion_controller=stage_controller)
        self.open_view(m)

    def get_response_blob(self):
        return (
            self.response_recorder.get_response_blob() if self.response_recorder else ""
        )

    def get_output_blob(self):
        return (
            self.response_recorder.get_output_blob() if self.response_recorder else ""
        )

    def set_response_recorder_period(self, p):
        if self.response_recorder:
            self.response_recorder.period = p

    def start_response_recorder(self):
        if self.response_recorder:
            self.response_recorder.start()

    def stop_response_recorder(self):
        if self.response_recorder:
            self.response_recorder.stop()

    # private
    def _luminosity_hook(self, power, **kw):
        self.degasser.degas(power, **kw)

    def _move_to_position(self, position, autocenter, **kw):
        if self.stage_manager is not None:
            if isinstance(position, tuple):
                if len(position) > 1:
                    x, y = position[:2]
                    self.stage_manager.linear_move(x, y, **kw)
                    if len(position) == 3:
                        self.stage_manager.set_z(position[2])
            else:
                self.stage_manager.move_to_hole(position, correct_position=autocenter)
                if kw.get("block"):
                    self.stage_manager.block()

            return True

    def _disable_hook(self):
        self.degasser.stop()
        return super(FusionsLaserManager, self)._disable_hook()

    # ========================= views =========================
    def get_control_buttons(self):
        """ """
        return [
            ("enable", "enable_label", None),
        ]

    def get_power_group(self):
        power_grp = BorderVGroup(
            self.get_control_button_group(),
            HGroup(
                Readonly("requested_power", format_str="%0.2f", width=100),
                spring,
                UReadonly("units"),
                spring,
            ),
            label="Power",
        )

        return power_grp

    def _get_record_label(self):
        return "Record" if not self._recording_power_state else "Stop"

    def _get_record_brightness(self):
        return self.record_brightness and self._get_machine_vision() is not None

    # ========================= defaults =======================
    def _fiber_light_default(self):
        """ """
        return FiberLight(name="fiber_light")


if __name__ == "__main__":
    d = FusionsLaserManager()

# ========================== EOF ====================================
# def get_power_database(self):
#     def get_additional_group(self):
#         og = Group(Item('laser_controller', show_label=False,
#                     editor=InstanceEditor(view='control_view'),
#                     style='custom'),
#                    label='Optics',
#                    )
#         ac = Group(
#                    og,
#                    show_border=True,
#                    label='Additional Controls',
#                    layout='tabbed')
#
#         aclist = self.get_additional_controls()
#         if aclist is None:
#             og.label = 'Optics'
#             og.show_border = True
#             ac = og
#         else:
#             for ai in aclist:
#                 ac.content.append(ai)
#         return ac

#     def get_control_group(self):
#         '''
#         '''
#         power_grp = self.get_power_group()
#         pulse_grp = Group(Item('pulse', style='custom', show_label=False),
#                         label='Pulse', show_border=True
#                         )
#         power_grp = HGroup(power_grp, pulse_grp)
#         ac = self.get_additional_group()
#         g = HGroup(power_grp, ac)
#
#         return g

# from pychron.database.adapters.power_adapter import PowerAdapter
#
#     db = PowerAdapter(name=self.dbname,
#                       kind='sqlite')
#     return db

# def get_power_calibration_database(self):
# from pychron.database.adapters.power_calibration_adapter import PowerCalibrationAdapter
#
#     db = PowerCalibrationAdapter(name=self.dbname,
#                                  kind='sqlite')
#     return db

#    def _subsystem_default(self):
#        '''
#        '''
#        return ArduinoSubsystem(name='arduino_subsystem_2')

#    def _brightness_meter_default(self):
#        if self.use_video:
#            b = BrightnessPIDManager(parent=self)
# #            b.brightness_manager.video = self.stage_manager.video
#
#            return b
#    def get_control_items(self):
#        '''
#        '''
# #        return Item('laser_controller', show_label=False,
# #                    editor=InstanceEditor(view='control_view'),
# #                    style='custom',
# #                    springy=False, height= -100)
#
# #        return self.laser_controller.get_control_group()
#        s = [('zoom', 'zoom', {}),
#            ('beam', 'beam', {'enabled_when':'object.beam_enabled'})
#            ]
#        return self._update_slider_group_factory(s)

#    def get_lens_configuration_group(self):
#        return Item('lens_configuration',
#                    editor=EnumEditor(values=self.lens_configuration_names)
#                    )

#    def get_optics_group(self):
#        csliders = self.get_control_items()
#        vg = HGroup(csliders,
#                      show_border=True,
#                      label='Optics', springy=False
#                      )
#
#        lens_config = self.get_lens_configuration_group()
#        if lens_config:
#            vg.content.insert(0, lens_config)
#
#        return vg
#    def get_control_button_group(self):
#        grp = HGroup(spring, Item('enabled_led', show_label=False, style='custom', editor=LEDEditor()),
#                        self._button_group_factory(self.get_control_buttons(), orientation='h'),
# #                                  springy=True
#                    )
#        return grp
# def collect_baseline_brightness(self, **kw):
#         bm = self.brightness_manager
#         if bm is not None:
#             bm.collect_baseline(**kw)
#
#     def get_laser_brightness(self, **kw):
#         bm = self.brightness_manager
#         if bm is not None:
#             return bm.get_value(**kw)
#     def _open_power_graph(self, graph):
#         ui = graph.edit_traits()
#         self.add_window(ui)
#
#     def _dispose_optional_windows_hook(self):
#         if self.power_graph is not None:
#             self.power_graph.close()

#    def _lens_configuration_changed(self):
#
#        t = Thread(target=self.set_lens_configuration)
#        t.start()

# def open_power_graph(self, rid, path=None):
#         if self.power_graph is not None:
#             self.power_graph.close()
#             del(self.power_graph)
#
#         g = StreamGraph(
#                     window_x=0.01,
#                     window_y=0.4,
#                     container_dict=dict(padding=5),
# #                        view_identifier='pychron.fusions.power_graph'
#                     )
#         self.power_graph = g
#
#         g.window_title = 'Power Readback - {}'.format(rid)
#         g.new_plot(data_limit=60,
#                    scan_delay=1,
#                    xtitle='time (s)',
#                    ytitle='power (%)',
#
#                    )
#         g.new_series()
#
#         if self.record_brightness:
#             g.new_series()
#
#         invoke_in_main_thread(self._open_power_graph, g)
#     def finish_loading(self):
#         '''
#         '''
# #        if self.fiber_light._cdevice is None:
# #            self.fiber_light._cdevice = self.subsystem.get_module('FiberLightModule')
#
#         super(FusionsLaserManager, self).finish_loading()
# #        self.load_lens_configurations()
#    def load_lens_configurations(self):
#        for config_name in ['gaussian', 'homogenizer']:
#            config = self.get_configuration(name=config_name)
#            if config:
#                self.info('loading lens configuration {}'.format(config_name))
#                self.lens_configuration_names.append(config_name)
#
#                offset = tuple(map(int, self.config_get(config, 'General', 'offset', default='0,0').split(',')))
#
#                bd = self.config_get(config, 'General', 'beam', cast='float')
#                user_enabled = self.config_get(config, 'General', 'user_enabled', cast='boolean', default=True)
#                self.lens_configuration_dict[config_name] = (bd, offset, user_enabled)
#
#        self.set_lens_configuration('gaussian')
#
#    def set_lens_configuration(self, name=None):
#        if name is None:
#            name = self.lens_configuration
#
#        try:
#            bd, offset, enabled = self.lens_configuration_dict[name]
#        except KeyError:
#            return
#
#        self.stage_manager.canvas.crosshairs_offset = offset
#
#        self.set_beam_diameter(bd, force=True)
#        self.beam_enabled = enabled
#     def _write_h5(self, table, v, x):
#         dm = self.data_manager
#         table = dm.get_table(table, 'Power')
#         if table is not None:
#             row = table.row
#             row['time'] = x
#             row['value'] = v
#             row.append()
#             table.flush()
# def _record_brightness(self):
#         cp = self.get_laser_brightness(verbose=False)
#         if cp is None:
#             cp = 0
#
#         xi = self.power_graph.record(cp, series=1)
#         self._write_h5('brightness', cp, xi)
#
#     def _record_power(self):
#         p = self.get_laser_watts()
#
#         if p is not None:
#             self._prev_power = p
#         else:
#             p = self._prev_power
#
#         if p is not None:
#             try:
#                 x = self.power_graph.record(p)
#                 self._write_h5('internal', p, x)
#             except Exception, e:
#                 self.info(e)
#                 print 'record power ', e
# def start_power_recording(self, rid):
#         self._recording_power_state = True
#         m = 'power and brightness' if self.record_brightness else 'power'
#         self.info('start {} recording for {}'.format(m, rid))
#         self._current_rid = rid
#
#         # zoom in for recording
#         self._previous_zoom = self.zoom
#         self.set_zoom(self.recording_zoom, block=True)
#
#         self.open_power_graph(rid)
#
#         self.data_manager = dm = H5DataManager()
#         self._data_manager_lock = Lock()
#
#         dw = DataWarehouse(root=os.path.join(self.db_root, 'power'))
#         dw.build_warehouse()
#
#         dm.new_frame(directory=dw.get_current_dir(),
#                                     base_frame_name=rid)
#         pg = dm.new_group('Power')
#         dm.new_table(pg, 'internal')
#
#         if self.power_timer is not None and self.power_timer.isAlive():
#             self.power_timer.Stop()
#
#         self.power_timer = Timer(1000, self._record_power)
#
#         if self._get_record_brightness():
#             dm.new_table(pg, 'brightness')
#         if self.brightness_timer is not None and self.brightness_timer.isAlive():
#             self.brightness_timer.Stop()
#
#         # before starting the timer collect quick baseline
#         # default is 5 counts @ 25 ms per count
#         if self._get_record_brightness():
#             self.collect_baseline_brightness()
#             self.brightness_timer = Timer(175, self._record_brightness)
#
#     def stop_power_recording(self, delay=5, save=True):
#
#         def _stop():
#             self._recording_power_state = False
#             if self.power_timer is not None:
#                 self.power_timer.Stop()
#             if self.brightness_timer is not None:
#                 self.brightness_timer.Stop()
#
#             self.info('Power recording stopped')
#             self.power_timer = None
#             self.brightness_timer = None
#             if save:
#                 db = self.get_power_database()
#                 if db.connect():
#                     dbp = db.add_power_record(rid=str(self._current_rid))
#                     self._current_rid = None
#                     db.add_path(dbp, self.data_manager.get_current_path())
#                     db.commit()
#
#             else:
#                 self.data_manager.delete_frame()
#
#             self.data_manager.close_file()
#
#             self.set_zoom(self._previous_zoom)
#             '''
#                 analyze the power graph
#                 if requested power greater than 1.5
#                 average power should be greater than 2
#             '''
#             if self._requested_power > 1.5:
#                 ps = self.power_graph.get_data(axis=1)
#                 a = sum(ps) / len(ps)
#                 if a < 2:
#                     self.warning('Does not appear laser fired. Average power reading ={}'.format(a))
#
# #        delay = 0
#         if self.power_timer is not None:
#
#             if delay == 0:
#                 _stop()
#             else:
#                 self.info('Stopping power recording in {} seconds'.format(delay))
#                 t = DoLaterTimer(delay, _stop)
#                 t.start()
#    def show_video_controls(self):
#        '''
#        '''
#        self.video_manager.edit_traits(view = 'controls_view')

#    def launch_laser_pulse(self):
#        '''
#        '''
#        p = os.path.join(paths.scripts_dir, 'laserscripts', 'laser_pulse.txt')
#        pulse = LaserPulseScript(manager = self)
#        pulse._load_script(p)
#        pulse.edit_traits()

#    def show_power_scan(self):
#        '''
#        '''
#
#        pp = os.path.join(paths.scripts_dir, 'laserscripts', 'power_scans')
#        pscan = PowerScanScript(manager = self, source_dir = pp)

# pscan.start()
# pscan.open()
#    def traits_view(self):
#        '''
#        '''
#        title = self.__class__.__name__ if self.title == '' else self.title
#        vg = VSplit()
#
#        hooks = [h for h in dir(self) if '__group__' in h]
#        for h in hooks:
#            vg.content.append(getattr(self, h)())
#
#        return View(#HSplit(
#                           #Item('stream_manager', show_label = False, style = 'custom'),
#                           vg,
#                       #    ),
#                    resizable = True,
#                   # menubar = self._menubar_factory(),
#                    title = title,
#                    handler = self.handler_klass)
#    def _stage_manager_factory(self, args):
#        if self.use_video:
#            klass = VideoStageManager
#        else:
#            klass = StageManager
#
#        sm = klass(**args)
#        return sm
#
#    def show_stage_manager(self, **kw):
#        #self.stage_manager.controllable = True
#        self.stage_manager.edit_traits(**kw)
#
#    def close_stage_manager(self):
#        self.stage_manager.close_ui()
#    def _show_streams_(self, available_streams):
#        sm = self.stream_manager
#        dm = sm.data_manager
#
#        available_streams.append(self.laser_controller)
#
#        streams = sm.open_stream_loader(available_streams)
#
#        if streams:
#
#            self.streaming = True
#            self.dirty = True
#            if streams != 'running':
#                for s in streams:
#                    p = s['parent']
#                    name = p.name
#
#                    dm.add_group(name)
#                    table = 'stream'
#                    dm.add_table(table, parent = 'root.%s' % name)
#                    sm.set_stream_tableid(name, 'root.%s.%s' % (name, table))
#                self.stream_manager.edit_traits()

#    def show_laser_control(self):
#        self.edit_traits()
#
#    def show_stage_manager(self):
#        '''
#        '''
#        self.stage_manager.edit_traits()

#    def show_motor_configurer(self):
#        self.laser_controller.configure_motors()

#    def show_video(self):
#        self.video_manager = VideoManager()
#        self.video_manager.edit_traits()

#    def stop_streams(self):
#        '''
#        '''
#        self.streaming = False
#        self.stream_manager.stop_streams()

#    def show_preferences(self):
#        preferences.edit_traits()
# def get_menus(self):
#        '''
#        '''
#        return [('File', [dict(name = 'Preferences', action = 'show_preferences',),
#                         #dict(name = 'Open Graph', action = 'open_graph'),
#                         #dict(name = 'Video Controls', action = 'show_video_controls')
#                         ]),
#
#                ('Devices', [
#                             #dict(name = 'Laser Controller', action = 'show_laser_controller'),
#                             #dict(name = 'Laser Stats', action = 'show_laser_stats'),
#                             dict(name = 'Stage Manager', action = 'show_stage_manager'),
#                             dict(name = 'Configure Motion Controller', action = 'show_motion_controller_manager',
#                                #enabled_when='not stage_simulation'
#                                ),
#                             dict(name = 'Configure Motors', action = 'show_motor_configurer'),
#                          # dict(name = 'Video', action = 'show_video')
#                           ]),
# #               ('Streams', [dict(name = 'Streams...', action = 'show_streams'),
# #                            dict(name = 'Stop', action = 'stop_streams', enabled_when = 'streaming'),
# #                            #dict(name = 'Save Graph ...', action = '_save_graph', enabled_when = 'dirty')
# #                            ]),
#
#
#                self.get_calibration_menu()
#
#                ]
# #    def get_calibration_menu(self):
# #        '''
# #        '''
# #        return ('Calibration', [
# #                               dict(name = 'Power Map', action = 'launch_power_map'),
# #                               dict(name = 'Beam Scan', action = 'launch_beam_scan')
# ##                               dict(name = 'Power Scan', action = 'launch_power_scan'),
# ##                               dict(name = 'Laser Pulse', action = 'launch_laser_pulse')
# #                                  ]
# #                                )

#    def control_group(self):
#        cg = VGroup(
#                    HGroup(
#                          # Item('simulation_led', show_label = False, style = 'custom', editor = LEDEditor()),
#                           Item('enabled_led', show_label = False, style = 'custom', editor = LEDEditor()),
#                           self._button_factory('enable', 'enable_label', None),
#                           ),
#
#                    self._slider_group_factory([('request_power', 'request_power',
#                                                 {'enabled_when':'object.parent._enabled',
#                                                  'defined_when':'object.parent.use_power_slider'
#                                                  }
#                                                 #{'defined_when':'"Diode" not in object.parent.__class__.__name__'}
#                                                 )]),
#                    self._update_slider_group_factory([('zoom', 'zoom', {})]),
#                    self._update_slider_group_factory([('beam', 'beam', {})]),
#
#                    defined_when = 'object.controllable'
#                    )
#        return cg
