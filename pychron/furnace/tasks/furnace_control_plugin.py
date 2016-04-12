# ===============================================================================
# Copyright 2016 Jake Ross
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
from traits.api import List

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.furnace.tasks.preferences import NMGRLFurnaceControlPreferencesPane


class NMGRLFurnaceControlPlugin(BaseTaskPlugin):
    canvases = List(contributes_to='pychron.extraction_line.plugin_canvases')

    # def __init__(self, *args, **kw):
    #     super(NMGRLFurnaceControlPlugin, self).__init__(*args, **kw)
    #
    def _canvases_default(self):
        c = {'display_name': 'Furnace',
             'valve_path': self.application.preferences.get('pychron.nmgrlfurnace.control.valve_path'),
             'canvas_path': self.application.preferences.get('pychron.nmgrlfurnace.control.canvas_path'),
             'config_path': self.application.preferences.get('pychron.nmgrlfurnace.control.canvas_config_path')}

        return [c, ]

    def _preferences_panes_default(self):
        return [NMGRLFurnaceControlPreferencesPane, ]

# ============= EOF =============================================
