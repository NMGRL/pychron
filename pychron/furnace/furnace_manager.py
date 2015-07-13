# ===============================================================================
# Copyright 2015 Jake Ross
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
from pyface.timer.do_later import do_after
from traits.api import TraitError, Instance, Float, provides, Int
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.furnace.furnace_controller import FurnaceController
from pychron.furnace.ifurnace_manager import IFurnaceManager
from pychron.furnace.stage_manager import NMGRLFurnaceStageManager, BaseFurnaceStageManager
from pychron.graph.stream_graph import StreamGraph
from pychron.managers.manager import Manager


class BaseFurnaceManager(Manager):
    controller = Instance(FurnaceController)
    setpoint = Float(auto_set=False, enter_set=True)
    setpoint_readback = Float
    stage_manager = Instance(BaseFurnaceStageManager)

    def _controller_default(self):
        c = FurnaceController(name='controller',
                              configuration_dir_name='furnace')
        return c


@provides(IFurnaceManager)
class NMGRLFurnaceManager(BaseFurnaceManager):
    setpoint_readback_min = Float(0)
    setpoint_readback_max = Float(1600.0)

    graph = Instance(StreamGraph)
    update_period = Int(2)

    _alive = False
    _guide_overlay = None

    def activate(self):
        # pref_id = 'pychron.furnace'
        # bind_preference(self, 'update_period', '{}.update_period'.format(pref_id))

        self._start_update()

    def prepare_destroy(self):
        self._stop_update()

    def dump_sample(self):
        self.stage_manager.dump_sample()

    def set_setpoint(self, v):
        if self.controller:
            # print self.controller, self.controller._cdevice
            self.controller.set_setpoint(v)
            if not self._guide_overlay:
                self._guide_overlay = self.graph.add_horizontal_rule(v)

            self._guide_overlay.visible = bool(v)
            self._guide_overlay.value = v

            # ymi, yma = self.graph.get_y_limits()
            d = self.graph.get_data(axis=1)
            self.graph.set_y_limits(min_=0, max_=max(d.max(), v * 1.1))

            self.graph.redraw()

    def read_setpoint(self, update=False):
        v = 0
        if self.controller:
            force = update and not self.controller.is_scanning()
            v = self.controller.read_setpoint(force=force)

        try:
            self.setpoint_readback = v
            return v
        except TraitError:
            pass

    # private
    def _stop_update(self):
        self._alive = False

    def _start_update(self):
        self._alive = True

        self.graph = g = StreamGraph()
        # g.plotcontainer.padding_top = 5
        # g.plotcontainer.padding_right = 5
        g.new_plot(xtitle='Time (s)', ytitle='Temp. (C)', padding_top=5, padding_right=5)
        g.set_scan_width(600)
        g.new_series()

        self._update_readback()

    def _update_readback(self):
        v = self.read_setpoint(update=True)
        self.graph.record(v, track_y=False)
        if self._alive:
            do_after(self.update_period * 1000, self._update_readback)

    # handlers
    def _setpoint_changed(self, new):
        self.set_setpoint(new)

    def _stage_manager_default(self):
        sm = NMGRLFurnaceStageManager(stage_manager_id='nmgrl.furnace.stage_map')
        return sm

# ============= EOF =============================================
