# ===============================================================================
# Copyright 2019 ross
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
from pychron.lasers.tasks.plugins.remote_laser_plugin import RemoteLaserPlugin


class AblationCO2Plugin(RemoteLaserPlugin):
    id = 'pychron.ablation.co2'
    name = 'AblationCO2'
    klass = ('pychron.lasers.laser_managers.ablation_laser_manager', 'AblationCO2Manager')
    task_name = 'Ablation CO2'
    task_klass = ('pychron.lasers.tasks.laser_task', 'AblationCO2Task')

# ============= EOF =============================================
