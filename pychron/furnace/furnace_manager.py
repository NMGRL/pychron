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
from traits.api import TraitError, Instance, Float, provides
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.canvas.canvas2D.furnace_canvas import FurnaceCanvas
from pychron.furnace.furnace_controller import FurnaceController
from pychron.furnace.ifurnace_manager import IFurnaceManager
from pychron.hardware.linear_axis import LinearAxis
from pychron.managers.manager import Manager


class BaseFurnaceManager(Manager):
    controller = Instance(FurnaceController)
    setpoint = Float
    setpoint_readback = Float

    def _controller_default(self):
        c = FurnaceController(name='controller',
                              configuration_dir_name='furnace')
        return c


class Dumper(LinearAxis):
    def dump(self):
        pass


@provides(IFurnaceManager)
class NMGRLFurnaceManager(BaseFurnaceManager):
    dumper = Instance(Dumper)
    funnel = Instance(LinearAxis)
    canvas = Instance(FurnaceCanvas)

    def dump_sample(self):
        self.debug('dump sample')

    def set_setpoint(self, v):
        if self.controller:
            self.controller.set_sepoint(v)

    def read_setpoint(self):
        v = 0
        if self.controller:
            v = self.controller.read_setpoint()

        try:
            self.setpoint_readback = v
            return v
        except TraitError:
            pass

    # handlers
    def _setpoint_changed(self, new):
        self.set_setpoint(new)

    def _dumper_default(self):
        d = Dumper(name='dumper', configuration_dir_name='furnace')
        return d

    def _funnel_default(self):
        f = LinearAxis(name='funnel', configuration_dir_name='furnace')
        return f

    def _canvas_default(self):
        c = FurnaceCanvas(dumper=self.dumper)
        return c

# ============= EOF =============================================
