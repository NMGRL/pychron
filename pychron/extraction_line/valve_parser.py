# ===============================================================================
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
# ===============================================================================

#============= enthought library imports =======================
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.xml.xml_parser import XMLParser


class ValveParser(XMLParser):
    def get_valve(self, name, groups=None, element=True):
        if groups is None:
            groups = self.get_groups()

        return next((v if element else v.text.strip()
                        for gi in groups
                        for v in gi.findall('valve') if v.text.strip()==name), None)

    def get_groups(self, element=True):
        tree = self.get_root()
#        tree = self._tree
        return [g if element else g.text.strip()
                for g in tree.findall('group')]

    def get_switches(self, group=None, element=True):
        if group is None:
            group = self.get_root()
        return [v if element else v.text.strip()
                for v in group.findall('switch')]

    def get_valves(self, group=None, element=True):
        if group is None:
            group = self.get_root()
        return [v if element else v.text.strip()
                for v in group.findall('valve')]

    def get_pipettes(self, group=None, element=True):
        if group is None:
            group = self.get_root()
        return [v if element else v.text.strip()
                    for v in group.findall('pipette')]
# ============= EOF =============================================

