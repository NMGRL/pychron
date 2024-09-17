# ===============================================================================
# Copyright 2014 Jake Ross
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
# ============= standard library imports ========================
# ============= local library imports  ==========================
from __future__ import absolute_import
from pychron.envisage.tasks.base_task import BaseManagerTask
from pychron.spectrometer.tasks.inspector.panes import ScanInspectorCentralPane
from pychron.spectrometer.tasks.inspector.scan_inspector import ScanInspector


class ScanInspectorTask(BaseManagerTask):

    def create_dock_panes(self):
        return []

    def create_central_pane(self):
        return ScanInspectorCentralPane(model=self.manager)

    def _manager_default(self):
        return ScanInspector()


# ============= EOF =============================================
