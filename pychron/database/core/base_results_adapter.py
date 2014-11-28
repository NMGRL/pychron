# ===============================================================================
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
# ===============================================================================

#============= enthought library imports =======================
from traits.api import  Int
from traitsui.tabular_adapter import TabularAdapter
#============= standard library imports ========================
#============= local library imports  ==========================
class BaseResultsAdapter(TabularAdapter):
    columns = [('ID', 'rid'),
               ('Date', 'rundate'),
               ('Time', 'runtime')
               ]

#    runtime_text = Property
#
#    def _get_runtime_text(self):
#        return self.item.runtime.strftime('%H:%M:%S')
    rid_width = Int(20)
    runtime_width = Int(80)
    rundate_width = Int(100)

#    def get_bg_color(self, obj, trait, row, *args):
#        if getattr(obj, trait)[row].loadable:
# #        if obj.results[row]._loadable:
#            return 'white'
#        else:
#            return '#FF4D4D'

class RIDResultsAdapter(BaseResultsAdapter):
    columns = [('RunID', 'runid'),
               ('Date', 'rundate'),
               ('Time', 'runtime')
               ]


# ============= EOF =============================================
