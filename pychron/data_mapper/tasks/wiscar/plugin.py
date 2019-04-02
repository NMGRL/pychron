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
from traitsui.api import View, UItem, VGroup

from pychron.data_mapper.sources.wiscar_source import WiscArNuSource
from pychron.envisage.tasks.base_plugin import BasePlugin


class ViewWiscArNuSource(WiscArNuSource):
    def traits_view(self):
        n = VGroup(UItem('nice_path'), show_border=True, label='Nice')
        mp = VGroup(UItem('metadata_path'), show_border=True, label='MetaData')
        d = VGroup(UItem('directory'), show_border=True, label='Directory')
        p = VGroup(UItem('path'), show_border=True, label='File', enabled_when='not directory')
        return View(VGroup(n, mp, d, p))


class WiscArDataPlugin(BasePlugin):
    sources = List(contributes_to='pychron.entry.data_sources')

    def _sources_default(self):
        return [('WiscAr Nu', ViewWiscArNuSource()), ]

# ============= EOF =============================================
