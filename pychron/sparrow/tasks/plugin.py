# ===============================================================================
# Copyright 2017 ross
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

from traits.api import List

from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.sparrow.sparrow_client import SparrowClient
from pychron.sparrow.tasks.preferences import SparrowPreferencesPane


class SparrowPlugin(BaseTaskPlugin):
    name = "Sparrow"
    nodes = List(contributes_to="pychron.pipeline.nodes")
    predefined_templates = List(contributes_to="pychron.pipeline.predefined_templates")

    def test_api(self):
        ret, err = True, None

        s = SparrowClient()
        ret = s.test_api()
        if not ret:
            err = "Failed to connect"
        return ret, err

    def _preferences_panes_default(self):
        return [SparrowPreferencesPane]

    # def _executable_path_changed(self, new):
    #     if new:
    #         paths.clovera_root = new
    def _service_offers_default(self):
        so = self.service_offer_factory(protocol=SparrowClient, factory=SparrowClient)
        return [so]

    # def _predefined_templates_default(self):
    #     return [('Plot', (('Sparrow Ideogram', IDEOGRAM),
    #                      ('Sparrow Spectrum', SPECTRUM)))]

    # def _nodes_default(self):
    #     return [SparrowNode]


# ============= EOF =============================================
