# ===============================================================================
# Copyright 2024 Pychron Developers
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

from traits.api import Instance

from pychron.pipeline.nodes.base import BaseNode
from pychron.processing.analyses.analysis_group import AnalysisGroup


class AusGeochemNode(BaseNode):
    service = Instance("pychron.ausgeochem.earthdata_service.AusGeochemEarthDataService")

    def configure(self):
        return True

    def run(self, state):
        if not state.unknowns:
            return

        if self.service is None:
            return

        ag = AnalysisGroup(analyses=state.unknowns)
        self.service.info(
            "Uploading {} analyses to AusGeochem EarthData".format(len(state.unknowns))
        )
        result = self.service.upload_analysis_group(ag)
        if result:
            self.service.info(
                "AusGeochem age calculation created with id {}".format(
                    result.get("id")
                )
            )


# ============= EOF =============================================
