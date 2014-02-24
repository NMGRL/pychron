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

#=============enthought library imports=======================
from traits.api import Instance, List, Any, Bool, on_trait_change, Str, Int
from apptools.preferences.preference_binding import bind_preference
#=============standard library imports ========================
import os
import time
from threading import Thread
from socket import gethostbyname, gethostname
#=============local library imports  ==========================
from pychron.extraction_line.explanation.extraction_line_explanation import ExtractionLineExplanation
from pychron.extraction_line.extraction_line_canvas import ExtractionLineCanvas
from pychron.extraction_line.sample_changer import SampleChanger
from pychron.paths import paths
from pychron.managers.manager import Manager
# from pychron.pyscripts.manager import PyScriptManager
from pychron.monitors.system_monitor import SystemMonitor

from pychron.extraction_line.status_monitor import StatusMonitor
from pychron.extraction_line.graph.extraction_line_graph import ExtractionLineGraph

# from pychron.managers.multruns_report_manager import MultrunsReportManager

# Macro = None
# start_recording = None
# stop_recording = None
# play_macro = None


class ExtractionLineManager(Manager):
    """
    Manager for interacting with the extraction line
    contains 2 interaction canvases, 2D and 3D
    contains reference to valve manager, gauge manager and laser manager

    """
    canvas = Instance(ExtractionLineCanvas)
    _canvases = List

    explanation = Instance(ExtractionLineExplanation, ())
    gauge_manager = Instance(Manager)
    monitor = Instance(SystemMonitor)

    valve_manager = Any  # Instance(Manager)
    status_monitor = Any
    multiplexer_manager = Any  # Instance(Manager)
    multruns_report_manager = Any  # Instance(Manager)
    network = Instance(ExtractionLineGraph)

    #    multruns_report_manager = Instance(MultrunsReportManager)
    #    environmental_manager = Instance(Manager)
    #    device_stream_manager = Instance(Manager)
    #     view_controller = Instance(ViewController)
    #    pumping_monitor = Instance(PumpingMonitor)

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

    def bind_preferences(self):

        bind_preference(self, 'check_master_owner',
                        'pychron.extraction_line.check_master_owner')
        bind_preference(self, 'use_network',
                        'pychron.extraction_line.use_network')
        bind_preference(self.network, 'inherit_state',
                        'pychron.extraction_line.inherit_state')

        bind_preference(self, 'display_volume', 'pychron.extraction_line.display_volume')
        bind_preference(self, 'volume_key', 'pychron.extraction_line.volume_key')

        bind_preference(self, 'use_status_monitor', 'pychron.extraction_line.use_status_monitor')

    def _use_status_monitor_changed(self):
        if self.mode == 'client':
            if self.use_status_monitor:
                #start
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

    def isolate_chamber(self):
        #get chamber name
        sc = self._sample_changer_factory()
        if sc:
            sc.isolate_chamber()

    def evacuate_chamber(self):
        sc = self.sample_changer
        #confirm evacuation if sample chamber is not (not isolated)
        # or check for evacuation fails
        msg = None
        if sc is None:
            msg = 'Are you sure you want to evacuate a chamber. No chamber has been isolated'
        else:
            err = sc.check_evacuation()
            if err:
                name = sc.chamber
                msg = 'Are you sure you want to evacuate the {} chamber. {}'.format(name, err)

        if msg:
            if self.confirmation_dialog(msg):
                sc = self._sample_changer_factory()

        if sc:
            sc.evacuate_chamber()

    def finish_chamber_change(self):
        sc = self.sample_changer
        if sc is None:
            msg = 'Sample change procedure was not started for any chamber'
        else:
            msg = sc.check_finish()

        if msg:
            if self.confirmation_dialog('{}. Are sure you want to finish?'.format(msg)):
                sc = self._sample_changer_factory()
        if sc:
            sc.finish_chamber_change()

        self.sample_changer = None

    def get_volume(self, node_name):
        v = 0
        if self.use_network:
            v = self.network.calculate_volumes(node_name)[0][1]

        return v

    def test_connection(self):
        return self.get_valve_states() is not None

    def refresh_canvas(self):
        for ci in self._canvases:
            ci.refresh()

    def finish_loading(self):
        if self.mode != 'client':
            self.monitor = SystemMonitor(manager=self,
                                         name='system_monitor')
            self.monitor.monitor()

        if self.use_network:
            p = os.path.join(paths.canvas2D_dir, 'canvas.xml')
            self.network.load(p)

    def deactivate(self):
        self.stop_status_monitor()
        if self.gauge_manager:
            self.gauge_manager.stop_scans()

        if self.monitor:
            self.monitor.stop()

    def stop_status_monitor(self):
        self.info('stopping status monitor')
        self.status_monitor.stop()

    def reload_canvas(self, load_states=False):
        self.reload_scene_graph()
        net = self.network
        vm = self.valve_manager
        if net:
            p = os.path.join(paths.canvas2D_dir, 'canvas.xml')
            net.load(p)

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

    def activate(self):
        self.debug('$$$$$$$$$$$$$$$$$$$$$$$$ EL Activated')
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

    def start_status_monitor(self):
        self.info('starting status monitor')
        self.status_monitor.start(self.valve_manager)

    def reload_scene_graph(self):
        self.info('reloading canvas scene')

        for c in self._canvases:
            if c is not None:
                c.load_canvas_file(c.config_name)

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

    def get_pressure(self, controller, name):
        if self.gauge_manager:
            return self.gauge_manager.get_pressure(controller, name)

    def disable_valve(self, description):
        self._enable_valve(description, False)

    def enable_valve(self, description):
        self._enable_valve(description, True)

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

    #===============================================================================
    # private
    #===============================================================================
    def _enable_valve(self, description, state):
        if self.valve_manager:
            valve = self.valve_manager.get_valve_by_description(description)
            if valve is None:
                valve = self.valve_manager.get_valve_by_name(description)

            if valve is not None:
                if not state:
                    self.close_valve(valve.name)

                valve.enabled = state

    def _open_close_valve(self, name, action,
                          description=None, address=None, mode='remote', **kw):
        vm = self.valve_manager
        if vm is not None:
            if address:
                name = vm.get_name_by_address(address)

            if description and description != '---':
                name = vm.get_name_by_description(description)

            result = self._change_valve_state(name, mode, action, **kw)
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
        if self.mode == 'client' or self.check_master_owner:
            if requestor is None:
                requestor = gethostbyname(gethostname())

            self.debug('checking ownership. requestor={}'.format(requestor))
            if name in self.valve_manager.valves:
                v = self.valve_manager.valves[name]
                return not (v.owner and v.owner != requestor)

        return True

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
            sc = SampleChanger(manager=self,
                               chamber='CO2')

        result = sc.edit_traits(view='chamber_select_view')
        if result:
            if sc.chamber and sc.chamber != 'None':
                self.sample_changer = sc
                return sc

    def _create_manager(self, klass, manager, params, **kw):
        # try a lazy load of the required module
        if 'fusions' in manager:
            package = 'pychron.managers.laser_managers.{}'.format(manager)
            self.laser_manager_id = manager
        elif 'rpc' in manager:
            package = 'pychron.rpc.manager'
        else:
            package = 'pychron.managers.{}'.format(manager)

        class_factory = self.get_manager_factory(package, klass, warn=False)
        if class_factory is None:
            package = 'pychron.extraction_line.{}'.format(manager)
            class_factory = self.get_manager_factory(package, klass)

        if class_factory:
            m = class_factory(**params)

            if manager in ['gauge_manager',
                           'valve_manager',
                           'multiplexer_manager',
                           # 'environmental_manager', 'device_stream_manager',
                           'multruns_report_manager']:
                self.trait_set(**{manager: m})
            else:
                self.add_trait(manager, m)

            return m
        else:
            self.debug('could not create manager {}, {},{},{}'.format(klass, manager, params, kw))

    #===============================================================================
    # handlers
    #===============================================================================
    def _valve_manager_changed(self):
        if self.valve_manager is not None:
            self.status_monitor.valve_manager = self.valve_manager
            e = self.explanation
            if e is not None:
                e.load(self.valve_manager.explanable_items)
                self.valve_manager.on_trait_change(e.load_item, 'explanable_items[]')

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

    #===============================================================================
    # defaults
    #===============================================================================
    def _status_monitor_default(self):
        sm = StatusMonitor(valve_manager=self.valve_manager)
        return sm

    def _valve_manager_default(self):
        from pychron.extraction_line.valve_manager import ValveManager

        return ValveManager(extraction_line_manager=self)

    #    def _gauge_manager_default(self):
    #        from pychron.extraction_line.gauge_manager import GaugeManager
    #        return GaugeManager()

    def _explanation_default(self):
    #        '''
    #        '''
        e = ExtractionLineExplanation()
        if self.valve_manager is not None:
            e.load(self.valve_manager.explanable_items)
            self.valve_manager.on_trait_change(e.load_item, 'explanable_items[]')

        return e

    def new_canvas(self, name='canvas_config'):
        c = ExtractionLineCanvas(manager=self,
                                 config_name='{}.xml'.format(name))
        self._canvases.append(c)
        c.canvas2D.trait_set(display_volume=self.display_volume,
                             volume_key=self.volume_key)

        return c

    def _canvas_default(self):
        """
        """
        return self.new_canvas()

    def _network_default(self):
        return ExtractionLineGraph()

#    def _pumping_monitor_default(self):
#        '''
#        '''
#        return PumpingMonitor(gauge_manager=self.gauge_manager,
#                              parent=self)

#    def _multruns_report_manager_default(self):
#        return MultrunsReportManager(application=self.application)
if __name__ == '__main__':
    elm = ExtractionLineManager()
    elm.bootstrap()
    elm.canvas.style = '2D'
    elm.configure_traits()

#=================== EOF ================================
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
