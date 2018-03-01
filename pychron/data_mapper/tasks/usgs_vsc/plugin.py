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
from __future__ import absolute_import
from traits.api import List, Dict
from traitsui.api import View, UItem, VGroup

from pychron.data_mapper.sources.usgs_vsc_source import USGSVSCNuSource, USGSVSCMAPSource
from pychron.envisage.tasks.base_plugin import BasePlugin


class ViewUSGSVSCNuSource(USGSVSCNuSource):
    def traits_view(self):
        return View(VGroup(VGroup(UItem('directory'), show_border=True, label='Directory'),
                           VGroup(UItem('path'), show_border=True, label='File')))

    def irradiation_view(self):
        v = View(VGroup(UItem('irradiation_path'), show_border=True, label='File'))
        return v


class ViewUSGSVSCMAPSource(USGSVSCMAPSource):
    def traits_view(self):
        return View(VGroup(VGroup(UItem('directory'), show_border=True, label='Directory'),
                           VGroup(UItem('path'), show_border=True, label='File')))

    def irradiation_view(self):
        v = View(VGroup(UItem('irradiation_path'), show_border=True, label='File'))
        return v


class USGSVSCDataPlugin(BasePlugin):
    sources = List(contributes_to='pychron.entry.data_sources')

    def _sources_default(self):
        return [('USGSVSC MAP', ViewUSGSVSCMAPSource()), ('USGSVSC Nu', ViewUSGSVSCNuSource())]

# ============= EOF =============================================
