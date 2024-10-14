# ===============================================================================
# Copyright 2023 Jake Ross
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

from __future__ import absolute_import
from pychron.lasers.tasks.laser_panes import (
    BaseLaserPane,
    ClientPane,
    StageControlPane,
    ControlPane,
    AxesPane,
    SupplementalPane,
)

from traitsui.api import View, Item, VGroup, HGroup, UItem, InstanceEditor


class UC2000CO2Pane(BaseLaserPane):
    pass


class UC2000CO2ClientPane(ClientPane):
    pass


class UC2000CO2StagePane(StageControlPane):
    id = "pychron.uc2000.co2.stage"


class UC2000CO2ControlPane(ControlPane):
    id = "pychron.uc2000.co2.control"

    def _get_request_group(self):
        request_grp = super()._get_request_group()
        control_grp = HGroup(Item("power_setpoint", label="Power Setpoint"))
        v = VGroup(control_grp, request_grp)
        return v


class UC2000CO2AxesPane(AxesPane):
    id = "pychron.uc2000.co2.axes"


class UC2000CO2SupplementalPane(SupplementalPane):
    id = "pychron.uc2000.co2.supplemental"
    name = "CO2"

    # def traits_view(self):
    #     grp = VGroup(
    #         Item("fiber_light", style="custom", show_label=False),
    #         show_border=True,
    #         label="FiberLight",
    #     )
    #     v = View(VGroup(grp))
    #     return v


# ============= EOF =============================================
