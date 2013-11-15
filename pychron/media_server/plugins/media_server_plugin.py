#===============================================================================
# Copyright 2012 Jake Ross
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import HasTraits
from traitsui.api import View, Item, TableEditor
from pychron.envisage.core.core_plugin import CorePlugin
from pychron.media_server.client import MediaClient
from pychron.media_server.browser import MediaBrowser
#============= standard library imports ========================
#============= local library imports  ==========================

class MediaServerPlugin(CorePlugin):
    def _service_offers_default(self):
        so = self.service_offer_factory(protocol=MediaClient,
                                        factory=MediaClient
                                        )
        so1 = self.service_offer_factory(protocol=MediaBrowser,
                                        factory=MediaBrowser
                                        )
        return [so, so1]
#============= EOF =============================================
