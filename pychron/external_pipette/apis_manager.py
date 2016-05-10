# ===============================================================================
# Copyright 2014 Jake Ross
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

# ============= enthought library imports =======================
from traits.api import Instance, Button, Bool, Str, List, provides, Property

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.external_pipette.protocol import IPipetteManager
from pychron.hardware.apis_controller import ApisController
from pychron.managers.manager import Manager


class InvalidPipetteError(BaseException):
    def __init__(self, name, av):
        self.available = '\n'.join(av)
        self.name = name

    def __repr__(self):
        return 'Invalid Pipette name={} av={}'.format(self.name, self.available)

    def __str__(self):
        return repr(self)


@provides(IPipetteManager)
class SimpleApisManager(Manager):
    controller = Instance(ApisController)

    test_command = Str
    test_command_response = Str
    clear_test_response_button = Button
    test_button = Button
    testing = Bool
    test_script_button = Button
    display_response_info = Bool(True)
    test_enabled = Property

    available_pipettes = List
    available_blanks = List

    mode = 'client'

    #for unittesting
    _timeout_flag = False

    def test_connection(self):
        return self.controller.test_connection()

    def set_extract_state(self, state, *args, **kw):
        pass

    def finish_loading(self):
        blanks = self.controller.get_available_blanks()
        airs = self.controller.get_available_airs()
        if blanks:
            self.available_blanks = blanks.split('[13]')
        if airs:
            self.available_pipettes = airs.split('[13]')

        #setup linking
            # v = self.controller.isolation_valve
            # elm = self.application.get_service('pychron.extraction_line.extraction_line_manager.ExtractionLineManager')
            # print 'exception', elm
            # print v
            # if elm:
            #     elm.link_valve_actuation(v, self.isolation_valve_state_change)
            # else:
            #     self.warning('could not find Extraction Line Manager. Needed for valve actuation linking')

    # def isolation_valve_state_change(self, name, action):
    #     self.controller.set_external_pumping(action == 'open')

    def bind_preferences(self, prefid):
        pass

    def load_pipette_non_blocking(self, *args, **kw):
        func = 'load_pipette'
        # self.controller.set_external_pumping()
        ret = self._load_pipette(self.available_pipettes, func, block=False, *args, **kw)
        # self.controller.set_external_pumping()

        return ret

    def load_blank_non_blocking(self, *args, **kw):
        func = 'load_blank'
        # self.controller.set_external_pumping()
        ret = self._load_pipette(self.available_blanks, func, block=False, *args, **kw)
        # self.controller.set_external_pumping()
        return ret

    def load_pipette(self, *args, **kw):
        func = 'load_pipette'
        # self.controller.set_external_pumping()
        ret = self._load_pipette(self.available_pipettes, func, *args, **kw)
        # self.controller.set_external_pumping()

        return ret

    def load_blank(self, *args, **kw):
        func = 'load_blank'
        # self.controller.set_external_pumping()
        ret = self._load_pipette(self.available_blanks, func, *args, **kw)
        # self.controller.set_external_pumping()
        return ret

    #private
    def _load_pipette(self, av, func, name, script=None, block=True, timeout=10, period=1):
        if script is None:
            self.debug('Script is none. check ExtractionPyScript.extract_pipette')
            raise NotImplementedError

        name = str(name)
        if not name in av:
            raise InvalidPipetteError(name, av)

        func = getattr(self.controller, func)
        func(name)

        if block:
            #wait for completion
            return self._loading_complete(script, timeout=timeout, period=period)
        else:
            return True

    def _loading_complete(self, script, **kw):
        if self._timeout_flag:
            return True
        else:
            return self.controller.script_loading_block(script, **kw)

    def _test_script_button_fired(self):
        self.testing = True
        from pychron.pyscripts.extraction_line_pyscript import ExtractionPyScript

        e = ExtractionPyScript(manager=self)
        e.setup_context(extract_device='',
                        analysis_type='blank')
        # e.extract_pipette('Blank AC pt1 cc', timeout=120)
        e.extract_pipette('Blank Air pt1 cc', timeout=120)
        # e.extract_pipette(self.available_pipettes[0], timeout=3)
        self.testing = False

    def _test_commmand_changed(self):
        self._execute_test_command()

    def _test_button_fired(self):
        self._execute_test_command()

    def _execute_test_command(self):
        cmd = self._assemble_command()
        if cmd:
            if self.controller.is_connected():
                resp = self.controller.ask(cmd)
                r = resp if resp else 'No Response'
            else:
                resp = ''
                r = 'No Connection'

            tcr = '{}\n{} >> {}'.format(self.test_command_response, cmd, r)
            if self.display_response_info:
                tcr = '{}\n\tresponse length={}'.format(tcr, len(resp))

            self.test_command_response = tcr

    def _assemble_command(self):
        cmd = self.test_command
        if cmd.strip().endswith(','):
            return

        return cmd

    def _controller_default(self):
        v = ApisController(name='apis_controller')
        return v

    def _get_test_enabled(self):
        return self.test_command and not self.testing

        # class ApisManager(Manager):
        #     implements(IPipetteManager)
        #     controller = Instance(ApisController)
        #
        #     available_pipettes = List(['1', '2'])
        #
        #     #testing buttons
        #     test_load_1 = Button('Test Load 1')
        #     testing = Bool
        #     test_result = Str
        #
        #     test_script_button = Button('Test Script')
        #
        #     reload_canvas_button = Button('Reload Canvas')
        #
        #     _timeout_flag = False
        #     canvas = Instance('pychron.canvas.canvas2D.extraction_line_canvas2D.ExtractionLineCanvas2D')
        #     valve_manager = Instance('pychron.extraction_line.valve_manager.ValveManager')
        #     mode = 'normal'
        #
        #     def finish_loading(self):
        #         from pychron.extraction_line.valve_manager import ValveManager
        #
        #         vm = ValveManager(extraction_line_manager=self)
        #         vm.load_valves_from_file('apis_valves.xml')
        #         for v in vm.valves.values():
        #             v.actuator = self.controller
        #
        #         self.valve_manager = vm
        #         for p in vm.pipette_trackers:
        #             p.load()
        #             self._set_pipette_counts(p.name, p.counts)
        #
        #     def open_valve(self, name, **kw):
        #         return self._change_valve_state(name, 'normal', 'open')
        #
        #     def close_valve(self, name, **kw):
        #         return self._change_valve_state(name, 'normal', 'close')
        #
        #     def set_selected_explanation_item(self, name):
        #         pass
        #
        #
        #
        #     def set_extract_state(self, state):
        #         pass
        #
        #     def load_pipette(self, name, timeout=10, period=1):
        #         name = str(name)
        #         if not name in self.available_pipettes:
        #             raise InvalidPipetteError(name)
        #
        #         self.controller.load_pipette(name)
        #
        #         #wait for completion
        #         return self._loading_complete(timeout=timeout, period=period)
        #
        #     #private
        #     def _loading_complete(self, **kw):
        #         if self._timeout_flag:
        #             return True
        #         else:
        #             return self.controller.blocking_poll('get_loading_status', **kw)
        #
        #     #testing buttons
        #     def _test_load_1_fired(self):
        #         self.debug('Test load 1 fired')
        #         self.testing = True
        #         self.test_result = ''
        #         try:
        #             ret = self.load_pipette('1', timeout=3)
        #             self.test_result = 'OK'
        #         except (TimeoutError, InvalidPipetteError), e:
        #             self.test_result = str(e)
        #         # self.test_result = 'OK' if ret else 'Failed'
        #         self.testing = False
        #
        #     def _test_script_button_fired(self):
        #         self.testing = True
        #         from pychron.pyscripts.extraction_line_pyscript import ExtractionPyScript
        #
        #         e = ExtractionPyScript(manager=self)
        #         e.setup_context(extract_device='')
        #         e.extract_pipette(1, timeout=3)
        #         self.testing = False


        # def _change_valve_state(self, name, mode, action):
        #     result, change = False, False
        #     func = getattr(self.valve_manager, '{}_by_name'.format(action))
        #     ret = func(name, mode=mode)
        #     if ret:
        #         result, change = ret
        #         if isinstance(result, bool):
        #             if change:
        #                 self.canvas.update_valve_state(name, True if action == 'open' else False)
        #                 self.canvas.request_redraw()
        #
        #     return result, change
        #
        # def _set_pipette_counts(self, name, value):
        #     c = self.canvas
        #     obj = c.scene.get_item('vlabel_{}'.format(name))
        #     if obj is not None:
        #         obj.value = value
        #         c.request_redraw()
        # def _load_canvas(self, c):
        #     c.load_canvas_file('apis_canvas_config.xml',
        #                        setup_name='apis_canvas')
        # @on_trait_change('valve_manager:pipette_trackers:counts')
        # def _update_pipette_counts(self, obj, name, old, new):
        #     self._set_pipette_counts(obj.name, new)
        #
        # def _reload_canvas_button_fired(self):
        #     self._load_canvas(self.canvas)
        #     self.canvas.request_redraw()
        #
        # def _canvas_default(self):
        #     from pychron.canvas.canvas2D.extraction_line_canvas2D import ExtractionLineCanvas2D
        #
        #     c = ExtractionLineCanvas2D(manager=self)
        #     self._load_canvas(c)
        #     return c

# ============= EOF =============================================

