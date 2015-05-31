# ===============================================================================
# Copyright 2012 Jake Ross
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
from pychron.core.xml.xml_parser import XMLParser


class SwitchParser(XMLParser):
    def get_manual_valve(self, *args, **kw):
        return self._get_item('manual_valve', *args, **kw)

    def get_valve(self, *args, **kw):
        return self._get_item('valve', *args, **kw)

    def _get_item(self, attr, name, groups=None, element=True):
        if groups is None:
            groups = self.get_groups()

        return next((v if element else v.text.strip()
                     for gi in groups
                     for v in gi.findall(attr) if v.text.strip() == name), None)

    def get_groups(self, element=True):
        tree = self.get_root()
        #        tree = self._tree
        return [tree]+[g if element else g.text.strip()
                for g in tree.findall('group')]

    def get_manual_valves(self, **kw):
        return self._get_items('manual_valve', **kw)

    def get_switches(self, **kw):
        return self._get_items('switch', **kw)

    def get_valves(self, **kw):
        return self._get_items('valve', **kw)

    def get_pipettes(self, **kw):
        return self._get_items('pipettes', **kw)

    def _get_items(self, attr, group=None, element=True):
        if group is None:
            group = self.get_root()
        return [v if element else v.text.strip()
                for v in group.findall(attr)]

# ============= EOF =============================================

