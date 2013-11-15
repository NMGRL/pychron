#===============================================================================
# Copyright 2011 Jake Ross
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

#============= standard library imports ========================

#============= local library imports  ==========================
from pychron.modeling.modeler_manager import ModelerManager
from pychron.envisage.core.core_plugin import CorePlugin
from apptools.preferences.preference_binding import bind_preference

class MDDModelerPlugin(CorePlugin):
    '''
    '''
    id = 'pychron.mdd'

    def _service_offers_default(self):
        '''
        '''
        so = self.service_offer_factory(protocol=ModelerManager,
                          factory=self._factory
                          )
        return [so]

    def _factory(self):
        '''
        '''
        m = ModelerManager()
        bind_preference(m.modeler, 'logr_ro_line_width', 'pychron.mdd.logr_ro_line_width')
        bind_preference(m.modeler, 'arrhenius_plot_type', 'pychron.mdd.plot_type')
        bind_preference(m.modeler, 'clovera_directroy', 'pychron.mdd.clovera_directory')

        return m



#============= EOF ====================================
