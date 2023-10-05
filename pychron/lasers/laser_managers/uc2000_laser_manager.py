# ===============================================================================
# Copyright 2023 ross
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
from pychron.hardware.uc2000 import UC2000
from pychron.lasers.laser_managers.laser_manager import LaserManager
from traits.api import Instance


class UC2000LaserManager(LaserManager):
    laser_controller = Instance(UC2000)


class UC2000CO2Manager(UC2000LaserManager):
    stage_manager_id = "uc2000.co2"
# ============= EOF =============================================
