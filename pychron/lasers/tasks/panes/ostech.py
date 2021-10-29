# ===============================================================================
# Copyright 2013 Jake Ross
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
from traitsui.api import View, UItem, VGroup, InstanceEditor, UCustom

from pychron.lasers.tasks.laser_panes import (
    ClientPane,
    BaseLaserPane,
    StageControlPane,
    ControlPane,
    AxesPane,
    SupplementalPane,
)


# ============= standard library imports ========================
# ============= local library imports  ==========================
class OsTechDiodeClientPane(ClientPane):
    xmin = 0.0
    xmax = 152.0
    ymin = 0.0
    ymax = 152.0
    zmin = 0.0
    zmax = 152.0


class OsTechDiodePane(BaseLaserPane):
    pass


class OsTechDiodeStagePane(StageControlPane):
    id = "pychron.ostech.diode.stage"


class OsTechDiodeControlPane(ControlPane):
    id = "pychron.ostech.diode.control"


class OsTechDiodeAxesPane(AxesPane):
    id = "pychron.ostech.diode.axes"


class OsTechDiodeSupplementalPane(SupplementalPane):
    id = "pychron.ostech.diode.supplemental"
    name = "Diode"

    def traits_view(self):
        v = View(
            VGroup(
                UCustom(
                    "temperature_controller", editor=InstanceEditor(view="control_view")
                ),
                label="Watlow",
            ),
            VGroup(
                UItem("pyrometer", style="custom"),
                label="Pyrometer",
            ),
            # VGroup(Item('control_module_manager', show_label=False, style='custom',
            #             ),
            #        #                      show_border = True,
            #        label='ControlModule',
            #
            #        ),
            VGroup(UCustom("fiber_light"), label="FiberLight"),
        )
        return v


# ============= EOF =============================================
