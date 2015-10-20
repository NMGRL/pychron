# ===============================================================================
# Copyright 2013 Jake Ross
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
from pychron.lasers.tasks.laser_panes import BaseLaserPane, ClientPane, \
    StageControlPane, ControlPane, AxesPane
# ============= standard library imports ========================
# ============= local library imports  ==========================


class FusionsCO2Pane(BaseLaserPane):
    pass


class FusionsCO2ClientPane(ClientPane):
    pass


class FusionsCO2StagePane(StageControlPane):
    id = 'pychron.fusions.co2.stage'


class FusionsCO2ControlPane(ControlPane):
    id = 'pychron.fusions.co2.control'


class FusionsCO2AxesPane(AxesPane):
    id = 'pychron.fusions.co2.axes'

# ============= EOF =============================================
