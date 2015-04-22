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
from pyface.timer.do_later import do_after
from traits.api import Instance, List, Any, Bool, on_trait_change, Str, Int, Dict, File
from apptools.preferences.preference_binding import bind_preference
# =============standard library imports ========================
import time
from threading import Thread
from socket import gethostbyname, gethostname
# =============local library imports  ==========================
from pychron.envisage.consoleable import Consoleable
from pychron.extraction_line.explanation.extraction_line_explanation import ExtractionLineExplanation
from pychron.extraction_line.extraction_line_canvas import ExtractionLineCanvas
from pychron.extraction_line.sample_changer import SampleChanger
from pychron.globals import globalv
from pychron.managers.manager import Manager
from pychron.monitors.system_monitor import SystemMonitor
from pychron.extraction_line.status_monitor import StatusMonitor
from pychron.extraction_line.graph.extraction_line_graph import ExtractionLineGraph
from pychron.pychron_constants import NULL_STR


class ExtractionLineManager(Manager, Consoleable):
    """
    Manager for interacting with the extraction line
    contains reference to valve manager, gauge manager and laser manager

    """
    canvas = Instance(ExtractionLineCanvas)
    _canvases = List

    explanation = Instance(ExtractionLineExplanation, ())
    monitor = Instance(SystemMonitor)

    valve_manager = Any
    gauge_manager = Any
    status_monitor = Any
    multiplexer_manager = Any
    network = Instance(ExtractionLineGraph)

    runscript = None
    learner = None

    mode = 'normal'

    use_status_monitor = Bool
    _update_status_flag = None
    _monitoring_valve_status = False

    valve_state_frequency = Int
    valve_lock_frequency = Int

    check_master_owner = Bool
    use_network = Bool
    display_volume = Bool
    volume_key = Str

    sample_changer = Instance(SampleChanger)
    link_valve_actuation_dict = Dict

    canvas_path = File
    canvas_config_path = File
    valves_path = File

    def activate(self):
        self._active = True
        if self.mode == 'client':
            self.start_status_monitor()
        else:
            if self.gauge_manager:
                self.info('start gauge scans')
                self.gauge_manager.start_scans()

        self.reload_canvas(load_states=True)

        # need to wait until now to load the ptrackers
        # this way our canvases are created
        for p in self.valve_manager.pipette_trackers:
            p.load()

        do_after(100, self._refresh_canvas)

    def _refresh_canvas(self):
        self.refresh_canvas()
        if self._active:
            do_after(100, self._refresh_canvas)

    def deactivate(self):
        self.stop_status_monitor()
        if self.gauge_manager:
            self.gauge_manager.stop_scans()

        if self.monitor:
            self.monitor.stop()
        self._active = False
    def bind_preferences(self):

        prefid = 'pychron.extraction_line'
        bind_preference(self, 'canvas_path', '{}.canvas_path'.format(prefid))
        bind_preference(self, 'canvas_config_path', '{}.canvas_config_path'.format(prefid))
        bind_preference(self, 'valves_path', '{}.valves_path'.format(prefid))

        bind_preference(self, 'check_master_owner',
                        '{}.check_master_owner'.format(prefid))
        bind_preference(self, 'use_network',
                        '{}.use_network'.format(prefid))
        bind_preference(self.network, 'inherit_state',
                        '{}.inherit_state'.format(prefid))

        self.console_bind_preferences('{}.console'.format(prefid))

        if self.gauge_manager:
            bind_preference(self.gauge_manager, 'update_period',
                            '{}.gauge_update_period'.format(prefid))
            bind_preference(self.gauge_manager, 'use_update',
                            '{}.use_gauge_update'.format(prefid))

        if self.canvas:
            bind_preference(self.canvas.canvas2D, 'display_volume', '{}.display_volume'.format(prefid))
            bind_preference(self.canvas.canvas2D, 'volume_key', '{}.volume_key'.format(prefid))

    def link_valve_actuation(self, name, func, remove=False):
        if remove:
            try:
                del self.link_valve_actuation_dict[name]
            except KeyError:
                self.debug('could not remove "{}". not in dict {}'.format(name,
                                                                          ','.join(
                                                                              self.link_valve_actuation_dict.keys())))
        else:
            self.debug('adding name="{}", func="{}" to link_valve_actuation_dict'.format(name, func.func_name))
            self.link_valve_actuation_dict[name] = func

    def do_sample_loading(self):
        """
        1. isolate chamber
        2.
        :return:
        """
        sc = self._sample_changer_factory()
        if sc:
            if self.confirmation_dialog('Ready to Isolate Chamber'):
                self._handle_console_message(('===== Isolate Chamber =====', 'maroon'))
                if not sc.isolate_chamber():
                    return
            else:
                return

            if self.confirmation_dialog('Ready to Evacuate Chamber'):
                self._handle_console_message(('===== Evacuate Chamber =====', 'maroon'))
                err = sc.check_evacuation()
                if err:
                    name = sc.chamber
                    msg = 'Are you sure you want to evacuate the {} chamber. {}'.format(name, err)
                    if not self.confirmation_dialog(msg):
                        return

                if not sc.evacuate_chamber():
                    return

            else:
                return

            if self.confirmation_dialog('Ready to Finish Sample Change'):
                self._handle_console_message(('===== Finish Sample Change =====', 'maroon'))
                sc.finish_chamber_change()

    # def isolate_chamber(self):
    # # get chamber name
    # sc = self._sample_changer_factory()
    #     if sc:
    #         sc.isolate_chamber()
    #
    # def evacuate_chamber(self):
    #     sc = self.sample_changer
    #     # confirm evacuation if sample chamber is not (not isolated)
    #     # or check for evacuation fails
    #     msg = None
    #     if sc is None:
    #         msg = 'Are you sure you want to evacuate a chamber. No chamber has been isolated'
    #     else:
    #         err = sc.check_evacuation()
    #         if err:
    #             name = sc.chamber
    #             msg = 'Are you sure you want to evacuate the {} chamber. {}'.format(name, err)
    #
    #     if msg:
    #         if self.confirmation_dialog(msg):
    #             sc = self._sample_changer_factory()
    #
    #     if sc:
    #         sc.evacuate_chamber()
    #
    # def finish_chamber_change(self):
    #     sc = self.sample_changer
    #     if sc is None:
    #         msg = 'Sample change procedure was not started for any chamber'
    #     else:
    #         msg = sc.check_finish()
    #
    #     if msg:
    #         if self.confirmation_dialog('{}. Are sure you want to finish?'.format(msg)):
    #             sc = self._sample_changer_factory()
    #     if sc:
    #         sc.finish_chamber_change()
    #
    #     self.sample_changer = None

    def get_volume(self, node_name):
        v = 0
        if self.use_network:
            v = self.network.calculate_volumes(node_name)[0][1]

        return v

    def test_gauge_communication(self):
        if self.gauge_manager:
            if self.gauge_manager.simulation:
                return globalv.communication_simulation
            else:
                return self.gauge_manager.test_connection()

    def test_connection(self):
        return self.test_valve_communication()

    def test_valve_communication(self):
        # if self.simulation:
        # return globalv.communication_simulation
        # else:
        if self.valve_manager:
            if self.valve_manager.simulation:
                return globalv.communication_simulation
            else:
                return bool(self.get_valve_states())

    def refresh_canvas(self):
        for ci in self._canvases:
            ci.refresh()

    def finish_loading(self):
        if self.mode != 'client':
            self.monitor = SystemMonitor(manager=self,
                                         name='system_monitor')
            self.monitor.monitor()

        if self.use_network:
            # p = os.path.join(paths.canvas2D_dir, 'canvas.xml')
            self.network.load(self.canvas_path)

    def stop_status_monitor(self):
        self.info('stopping status monitor')
        self.status_monitor.stop()

    def reload_canvas(self, load_states=False):
        self.reload_scene_graph()
        net = self.network
        vm = self.valve_manager
        if net:
            # p = os.path.join(paths.canvas2D_dir, 'canvas.xml')
            net.load(self.canvas_path)

        if net:
            net.suppress_changes = True

        vm.load_valve_states(refresh=False, force_network_change=True)
        vm.load_valve_lock_states(refresh=False)
        if self.mode == 'client':
            self.valve_manager.load_valve_owners(refresh=False)

        if net:
            net.suppress_changes = False

        vm.load_valve_states(refresh=False, force_network_change=True)

        for p in vm.pipette_trackers:
            self._set_pipette_counts(p.name, p.counts)

        self.refresh_canvas()

    def start_status_monitor(self):
        self.info('starting status monitor')
        self.status_monitor.start(self.valve_manager)

    def reload_scene_graph(self):
        self.info('reloading canvas scene')

        for c in self._canvases:
            if c is not None:
                c.load_canvas_file(self.canvas_path, self.canvas_config_path, self.valves_path)
                # c.load_canvas_file(c.config_name)

                if self.valve_manager:
                    for k, v in self.valve_manager.valves.iteritems():
                        vc = c.get_object(k)
                        if vc:
                            vc.soft_lock = v.software_lock
                            vc.state = v.state

    def update_valve_state(self, name, state, *args, **kw):

        if self.use_network:
            self.network.set_valve_state(name, state)
            for c in self._canvases:
                self.network.set_canvas_states(c, name)

        for c in self._canvases:
            c.update_valve_state(name, state, *args, **kw)

    def update_valve_lock_state(self, *args, **kw):
        for c in self._canvases:
            c.update_valve_lock_state(*args, **kw)

    def update_valve_owned_state(self, *args, **kw):
        for c in self._canvases:
            c.update_valve_owned_state(*args, **kw)

    def set_valve_owner(self, name, owner):
        """
            set flag indicating if the valve is owned by a system
        """
        if self.valve_manager is not None:
            self.valve_manager.set_valve_owner(name, owner)

    def show_valve_properties(self, name):
        if self.valve_manager is not None:
            self.valve_manager.show_valve_properties(name)

    def get_software_lock(self, name, **kw):
        if self.valve_manager is not None:
            return self.valve_manager.get_software_lock(name, **kw)

    def set_software_lock(self, name, lock):
        if self.valve_manager is not None:
            if lock:
                self.valve_manager.lock(name)
            else:
                self.valve_manager.unlock(name)

            description = self.valve_manager.get_valve_by_name(name).description
            self.info('Valve-{} ({}) {}'.format(name, description, 'lock' if lock else 'unlock'),
                      color='blue' if lock else 'black')
            self.update_valve_lock_state(name, lock)

    def get_valve_owners(self):
        if self.valve_manager is not None:
            return self.valve_manager.get_owners()

    def get_valve_lock_states(self):
        if self.valve_manager is not None:
            return self.valve_manager.get_software_locks()

    def get_valve_state(self, name=None, description=None):
        if self.valve_manager is not None:
            if description is not None and description.strip():
                return self.valve_manager.get_state_by_description(description)
            else:
                return self.valve_manager.get_state_by_name(name)

    def get_valve_states(self):
        if self.valve_manager is not None:
            return self.valve_manager.get_states()

    def get_valve_by_name(self, name):
        if self.valve_manager is not None:
            return self.valve_manager.get_valve_by_name(name)

    def get_valve_names(self):
        names = []
        if self.valve_manager is not None:
            names = self.valve_manager.get_valve_names()
        return names

    def get_pressure(self, controller, name):
        if self.gauge_manager:
            return self.gauge_manager.get_pressure(controller, name)

    def get_device_value(self, dev_name):
        dev = self.get_device(dev_name)
        if dev is None:
            self.unique_warning('No device named {}'.format(dev_name))
        else:
            return dev.get()

    def disable_valve(self, description):
        self._enable_valve(description, False)

    def enable_valve(self, description):
        self._enable_valve(description, True)

    def lock_valve(self, name, **kw):
        return self._lock_valve(name, True, **kw)

    def unlock_valve(self, name, **kw):
        return self._lock_valve(name, False, **kw)

    def open_valve(self, name, **kw):
        return self._open_close_valve(name, 'open', **kw)

    def close_valve(self, name, **kw):
        return self._open_close_valve(name, 'close', **kw)

    def sample(self, name, **kw):
        def sample():
            valve = self.valve_manager.get_valve_by_name(name)
            if valve is not None:
                self.info('start sample')
                self.open_valve(name, **kw)
                time.sleep(valve.sample_period)

                self.info('end sample')
                self.close_valve(name, **kw)

        t = Thread(target=sample)
        t.start()

    def cycle(self, name, **kw):
        def cycle():

            valve = self.valve_manager.get_valve_by_name(name)
            if valve is not None:
                n = valve.cycle_n
                period = valve.cycle_period

                self.info('start cycle n={} period={}'.format(n, period))
                for i in range(n):
                    self.info('valve cycling iteration ={}'.format(i + 1))
                    self.open_valve(name, **kw)
                    time.sleep(period)
                    self.close_valve(name, **kw)
                    time.sleep(period)

        t = Thread(target=cycle)
        t.start()

    def get_script_state(self, key):
        return self.pyscript_editor.get_script_state(key)

    def set_selected_explanation_item(self, obj):
        if self.explanation:
            selected = None
            if obj:
                selected = next((i for i in self.explanation.explanable_items if obj.name == i.name), None)

            self.explanation.selected = selected

    def new_canvas(self):
        c = ExtractionLineCanvas(manager=self)
        self._canvases.append(c)
        c.canvas2D.trait_set(display_volume=self.display_volume,
                             volume_key=self.volume_key)

        return c

    # ===============================================================================
    # private
    # ===============================================================================
    def _log_spec_event(self, name, action):
        sm = self.application.get_service('pychron.spectrometer.scan_manager.ScanManager')
        if sm:
            color = 0x98FF98 if action == 'open' else 0xFF9A9A
            sm.add_spec_event_marker('{} ({})'.format(name, action),
                                     mode='valve',
                                     extra=name,
                                     bgcolor=color)

    def _enable_valve(self, description, state):
        if self.valve_manager:
            valve = self.valve_manager.get_valve_by_description(description)
            if valve is None:
                valve = self.valve_manager.get_valve_by_name(description)

            if valve is not None:
                if not state:
                    self.close_valve(valve.name)

                valve.enabled = state

    def _lock_valve(self, name, action, description=None, address=None, **kw):
        """

        :param name:
        :param action: bool True ==lock false ==unlock
        :param description:
        :param kw:
        :return:
        """
        vm = self.valve_manager
        if vm is not None:
            oname = name
            if address:
                name = vm.get_name_by_address(address)

            if description and description != '---':
                name = vm.get_name_by_description(description)

            if not name:
                self.warning('Invalid valve name={}, description={}'.format(oname, description))
                return False

            v = vm.get_valve_by_name(name)
            if action:
                v.lock()
            else:
                v.unlock()

            self.update_valve_lock_state(name, action)
            self.refresh_canvas()
            return True

    def _open_close_valve(self, name, action,
                          description=None, address=None, mode='remote', **kw):
        vm = self.valve_manager
        if vm is not None:
            oname = name
            if address:
                name = vm.get_name_by_address(address)

            if description and description != '---':
                name = vm.get_name_by_description(description)

            # check if specified valve is in the valves.xml file
            if not name:
                self.warning('Invalid valve name={}, description={}'.format(oname, description))
                return False, False

            result = self._change_valve_state(name, mode, action, **kw)

            if result:
                if all(result):
                    description = vm.get_valve_by_name(name).description
                    self._log_spec_event(name, action)
                    self.info('{:<6s} Valve-{} ({})'.format(action.upper(), name, description),
                        color='red' if action == 'close' else 'green')
                    vm.actuate_children(name, action, mode)
                    ld = self.link_valve_actuation_dict
                    if ld:
                        try:
                            func = ld[name]
                            func(name, action)
                        except KeyError:
                            self.debug('name="{}" not in '
                                       'link_valve_actuation_dict. keys={}'.format(name, ','.join(ld.keys())))

            return result

    def _change_valve_state(self, name, mode, action, sender_address=None):
        result, change = False, False
        if self._check_ownership(name, sender_address):
            func = getattr(self.valve_manager, '{}_by_name'.format(action))
            ret = func(name, mode=mode)
            if ret:
                result, change = ret
                if isinstance(result, bool):
                    if change:
                        self.update_valve_state(name, True if action == 'open' else False)
                        self.refresh_canvas()

        return result, change

    def _check_ownership(self, name, requestor):
        """
            check if this valve is owned by
            another client 
            
            if this is not a client but you want it to 
            respect valve ownership 
            set check_master_owner=True
            
        """
        ret = True
        if self.mode == 'client' or self.check_master_owner:
            if requestor is None:
                requestor = gethostbyname(gethostname())

            self.debug('checking ownership. requestor={}'.format(requestor))
            try:
                v = self.valve_manager.valves[name]
                ret = not (v.owner and v.owner != requestor)
            except KeyError:
                pass
        return ret

    def _set_pipette_counts(self, name, value):
        for c in self._canvases:
            scene = c.canvas2D.scene
            obj = scene.get_item('vlabel_{}Pipette'.format(name))
            if obj is not None:
                obj.value = value
                c.refresh()

    def _sample_changer_factory(self):
        sc = self.sample_changer
        if sc is None:
            sc = SampleChanger(manager=self)

        if sc.setup():
            result = sc.edit_traits(view='chamber_select_view')
            if result:
                if sc.chamber and sc.chamber != NULL_STR:
                    self.sample_changer = sc
                    return sc

    def _create_manager(self, klass, manager, params, **kw):
        # try a lazy load of the required module
        # if 'fusions' in manager:
        # package = 'pychron.managers.laser_managers.{}'.format(manager)
        # self.laser_manager_id = manager
        if 'rpc' in manager:
            package = 'pychron.rpc.manager'
        else:
            package = 'pychron.managers.{}'.format(manager)
        print manager, manager in ('valve_manager', 'gauge_manager', 'multiplexer_manager')
        if manager in ('valve_manager', 'gauge_manager', 'multiplexer_manager'):
            return getattr(self, manager)
        else:
            class_factory = self.get_manager_factory(package, klass, warn=False)
            if class_factory is None:
                package = 'pychron.extraction_line.{}'.format(manager)
                class_factory = self.get_manager_factory(package, klass)

            if class_factory:
                m = class_factory(**params)
                self.add_trait(manager, m)

                return m
            else:
                self.debug('could not create manager {}, {},{},{}'.format(klass, manager, params, kw))

    # ===============================================================================
    # handlers
    # ===============================================================================
    def _use_status_monitor_changed(self):
        if self.mode == 'client':
            if self.use_status_monitor:
                bind_preference(self.status_monitor, 'state_freq',
                                'pychron.extraction_line.valve_state_frequency')
                bind_preference(self.status_monitor, 'lock_freq',
                                'pychron.extraction_line.valve_lock_frequency')
                bind_preference(self.status_monitor, 'owner_freq',
                                'pychron.extraction_line.valve_owner_frequency')
                bind_preference(self.status_monitor, 'update_period',
                                'pychron.extraction_line.update_period')
            else:
                if self.status_monitor.isAlive():
                    self.status_monitor.stop()

    @on_trait_change('valve_manager:pipette_trackers:counts')
    def _update_pipette_counts(self, obj, name, old, new):
        self._set_pipette_counts(obj.name, new)

    @on_trait_change('use_network,network:inherit_state')
    def _update_network(self):
        from pychron.canvas.canvas2D.scene.primitives.valves import Valve

        if not self.use_network:
            for c in self._canvases:
                scene = c.canvas2D.scene
                for item in scene.get_items():
                    if not isinstance(item, Valve):
                        item.active_color = item.default_color
                    else:
                        item.active_color = item.oactive_color
        else:
            net = self.network
            for k, vi in self.valve_manager.valves.iteritems():
                net.set_valve_state(k, vi.state)
            self.reload_canvas()

    @on_trait_change('display_volume,volume_key')
    def _update_canvas_inspector(self, name, new):
        for c in self._canvases:
            c.canvas2D.trait_set(**{name: new})

    def _handle_state(self, new):
        self.update_valve_state(*new)

    def _handle_lock_state(self, new):
        self.update_valve_lock_state(*new)

    def _handle_owned_state(self, new):
        self.update_valve_owned_state(*new)

    def _handle_refresh_canvas(self, new):
        self.refresh_canvas()

    def _handle_console_message(self, new):
        color = None
        if isinstance(new, tuple):
            msg, color = new
        else:
            msg = new

        if color is None:
            color = self.console_default_color

        if self.console_display:
            self.console_display.add_text(msg, color=color)

    # ===============================================================================
    # defaults
    # ===============================================================================
    def _status_monitor_default(self):
        sm = StatusMonitor(valve_manager=self.valve_manager)
        return sm

    def _valve_manager_default(self):
        from pychron.extraction_line.valve_manager import ValveManager
        # vm = ValveManager(extraction_line_manager=self)
        vm = ValveManager(mode=self.mode, application=self.application)
        vm.on_trait_change(self._handle_state, 'refresh_state')
        vm.on_trait_change(self._handle_lock_state, 'refresh_lock_state')
        vm.on_trait_change(self._handle_owned_state, 'refresh_owned_state')
        vm.on_trait_change(self._handle_refresh_canvas, 'refresh_canvas_needed')
        vm.on_trait_change(self._handle_console_message, 'console_message')
        return vm

    def _explanation_default(self):
        e = ExtractionLineExplanation()
        if self.valve_manager is not None:
            e.load(self.valve_manager.explanable_items)
            self.valve_manager.on_trait_change(e.load_item, 'explanable_items[]')

        return e

    def _canvas_default(self):
        """
        """
        return self.new_canvas()

    def _network_default(self):
        return ExtractionLineGraph()


if __name__ == '__main__':
    elm = ExtractionLineManager()
    elm.bootstrap()
    elm.canvas.style = '2D'
    elm.configure_traits()

# =================== EOF ================================
# def _valve_manager_changed(self):
# if self.valve_manager is not None:
# self.status_monitor.valve_manager = self.valve_manager
# e = self.explanation
#         if e is not None:
#             e.load(self.valve_manager.explanable_items)
#             self.valve_manager.on_trait_change(e.load_item, 'explanable_items[]')

# def _pumping_monitor_default(self):
# '''
# '''
# return PumpingMonitor(gauge_manager=self.gauge_manager,
#                              parent=self)

#    def _multruns_report_manager_default(self):
#        return MultrunsReportManager(application=self.application)
#     def _view_controller_factory(self):
#         if self.canvas.canvas3D:
#             v = ViewController(scene_graph=self.canvas.canvas3D.scene_graph)
#             self.canvas.canvas3D.user_views = v.views
#             return v

#    def add_extraction_line_macro_delay(self):
#        global Macro
#        if Macro is None:
#            from macro import _Macro_ as Macro
#
#        info = Macro.edit_traits()
#        if info.result:
#            Macro.record_action(('delay', Macro.delay))
#
#    def stop_extraction_line_macro_recording(self):
#        global stop_recording
#        if stop_recording is None:
#            from macro import stop_recording
#        stop_recording()
#
#    def start_extraction_line_macro_recording(self):
#        global start_recording
#        if start_recording is None:
#            from macro import start_recording
#        start_recording()
#
#    def play_extraction_line_macro_recording(self):
#        #lazy pre_start time and Thread
#        global time
#        if time is None:
#            import time
#
#        global Thread
#        if Thread is None:
#            from threading import Thread
#
#        global play_macro
#        if play_macro is None:
#            from macro import play_macro
#
#        def _play_():
#            for c in play_macro():
#                args = c[0]
#                kw = c[1]
#
#                if args == 'delay':
#
#                    time.sleep(kw)
#                else:
#                    action = args[3]
#                    name = args[1]
#
#                    func = getattr(self, '%s_valve' % action)
#                    func(name, mode = 'manual')
#
#        t = Thread(target = _play_)
#        t.start()
