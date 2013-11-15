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
from traits.api import HasTraits, Instance, Any, Button, DelegatesTo, Float
from traitsui.api import View, Item, TableEditor, HGroup
from pychron.viewable import Viewable
from enable.component_editor import ComponentEditor
from pychron.canvas.canvas2D.extraction_line_canvas2D import ExtractionLineCanvas2D
import os
from pychron.paths import paths
# from pychron.managers.manager import Manager
from pychron.extraction_line.valve_manager import ValveManager
from pyface.timer.timer import Timer
#============= standard library imports ========================
#============= local library imports  ==========================

class UVGasHandlerManager(ValveManager):
    canvas = Instance(ExtractionLineCanvas2D)
    controller = Any
    use_explanation = False
    mode = 'normal'

    auto_gas_exchange = Button

    # energy_readback=DelegatesTo('controller')
    pressure_readback = DelegatesTo('controller')
#    pressure_readback=Float
    def set_software_lock(self, name, lock):
        if lock:
            self.lock(name)
        else:
            self.unlock(name)

    def load(self):
        path = os.path.join(paths.extraction_line_dir, 'uv_gas_handling_valves.xml')
        self._load_valves_from_file(path)
        return True

    def open_valve(self, name, mode):
        pass
#        v = self.get_valve_by_name(name)
#        self.controller.open_valve(v.address)
#        return True

    def close_valve(self, name, mode):
        pass
#        v = self.get_valve_by_name(name)
#        self.controller.close_valve(v.address)
#        return True

    def set_selected_explanation_item(self, item):
        pass

    def _auto_gas_exchange(self):
        self.info('Starting auto gas exchange')
        self._timer = Timer(1000, self._update_pressure)
        self._timer.Start()
#        self.controller.start_update_timer()
        if not self.confirmation_dialog('Are both gas cylinders closed', title='Auto Gas Exchange'):
            self._timer.Stop()
            return

        self.controller.do_auto_vac()
        if not self.confirmation_dialog('Open Premix Cylinder, set secondary pressure to 6.5 - 7.5 bar', title='Auto Gas Exchange'):
            self._timer.Stop()
            return

        self.controller.do_auto_gas_exchange()
        self.information_dialog('Close Premix Gas Cylinder', title='Auto Gas Exchange')
        self._timer.Stop()

    def _update_pressure(self):
        self.controller.get_pressure()

#===============================================================================
# handlers
#===============================================================================
    def _auto_gas_exchange_fired(self):
        self._auto_gas_exchange()

    def _canvas_default(self):
        p = os.path.join(paths.canvas2D_dir, 'uv_gas_handling_canvas.xml')
        canvas = ExtractionLineCanvas2D(manager=self)
        canvas.load_canvas_file(p)
        return canvas

    def traits_view(self):
        ctrl_grp = HGroup(Item('auto_gas_exchange', show_label=False))
        info_grp = HGroup(
                        # Item('energy_readback', width=50,style='readonly'),
                        Item('pressure_readback', width=50, style='readonly')
                        )
        v = View(
                 ctrl_grp,
                 info_grp,
                 Item('canvas',
                      show_label=False,
                      editor=ComponentEditor(),
                      ), resizable=True,
                 width=700,
                 height=500
                 )
        return v
#============= EOF =============================================
