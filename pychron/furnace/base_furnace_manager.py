# ===============================================================================
# Copyright 2018 ross
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
from traits.api import Instance, Float, Bool, Any
from pychron.extraction_line.switch_manager import SwitchManager
from pychron.furnace.base_stage_manager import BaseFurnaceStageManager
from pychron.managers.stream_graph_manager import StreamGraphManager
from pychron.response_recorder import ResponseRecorder


class BaseFurnaceManager(StreamGraphManager):
    controller_klass = None
    controller = Any

    setpoint = Float(auto_set=False, enter_set=True)
    temperature_readback = Float
    output_percent_readback = Float
    stage_manager = Instance(BaseFurnaceStageManager)
    switch_manager = Instance(SwitchManager)
    response_recorder = Instance(ResponseRecorder)

    use_network = False
    verbose_scan = Bool(False)

    def check_heating(self):
        pass

    def _controller_default(self):
        if self.controller_klass is None:
            raise NotImplementedError
        c = self.controller_klass(name='controller',
                                  configuration_dir_name='furnace')
        return c

    def _switch_manager_default(self):
        sm = SwitchManager(configuration_dir_name='furnace',
                           setup_name='furnace_valves')
        sm.on_trait_change(self._handle_state, 'refresh_state')
        return sm

    def _response_recorder_default(self):
        r = ResponseRecorder(response_device=self.controller,
                             output_device=self.controller)
        return r

    def _handle_state(self, new):
        pass

    def test_furnace_api(self):
        self.info('testing furnace api')
        ret, err = False, ''
        if self.controller:
            ret, err = self.controller.test_connection()
        return ret, err

    def test_connection(self):
        self.info('testing connection')
        return self.test_furnace_api()

# ============= EOF =============================================
