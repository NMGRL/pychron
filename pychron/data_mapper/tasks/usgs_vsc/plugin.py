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
from envisage.service_offer import ServiceOffer
from traits.api import List, Dict

from pychron.data_mapper.sources.vfile_source import ViewUSGSVSCMAPSource
from pychron.envisage.tasks.base_plugin import BasePlugin


class USGSVSCDataPlugin(BasePlugin):
    sources = List(contributes_to='pychron.entry.data_sources')

    def _sources_default(self):
        return [('USGSVSC MAP', ViewUSGSVSCMAPSource()), ('USGSVSC Nu', ViewUSGSVSCNuSource) ]

    # service_offers = List(contributes_to='envisage.service_offers')
    #
    # def _service_offers_default(self):
    #     so = ServiceOffer(protocol='pychron.data_mapper.sources.usgs_vsc_source.ViewUSGSVSCSource',
    #                       factory=ViewUSGSVSCSource)
    #     return [so,]
# ============= EOF =============================================
