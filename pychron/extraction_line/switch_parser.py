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

import yaml

from pychron.core.xml.xml_parser import XMLParser
from pychron.core.yaml import yload


class SwitchParser(XMLParser):
    def load(self, path):
        self.path = path
        if self.is_yaml:
            try:
                self._yobj = yload(path)
            except yaml.YAMLError:
                return

            return True
        else:
            return super(SwitchParser, self).load(path)

    @property
    def is_yaml(self):
        return self.path and (self.path.endswith(".yaml") or self.path.endswith(".yml"))

    def get_all_switches(self):
        switches = []
        for g in self.get_groups():
            for v in self.get_valves(group=g):
                switches.append(v)

        for v in self.get_valves():
            switches.append(v)

        for s in self.get_switches():
            switches.append(s)

        for mv in self.get_manual_valves():
            switches.append(mv)
        return switches

    def get_manual_valve(self, *args, **kw):
        return self._get_item("manual_valve", *args, **kw)

    def get_valve(self, *args, **kw):
        return self._get_item("valve", *args, **kw)

    def _get_item(self, attr, name, groups=None, element=True):
        if groups is None:
            groups = self.get_groups()

        return next(
            (
                v if element else v.text.strip()
                for gi in groups
                for v in gi.findall(attr)
                if v.text.strip() == name
            ),
            None,
        )

    def get_groups(self, element=True):
        ret = []
        if not self.is_yaml:
            tree = self.get_root()
            if tree:
                ret = [g if element else g.text.strip() for g in tree.findall("group")]

        return ret

    def get_manual_valves(self, **kw):
        return self._get_items("manual_valve", **kw)

    def get_switches(self, **kw):
        return self._get_items("switch", **kw)

    def get_valves(self, **kw):
        return self._get_items("valve", **kw)

    def get_pipettes(self, **kw):
        return self._get_items("pipette", **kw)

    def _get_items(self, attr, group=None, element=True):

        if self.is_yaml:
            return [i for i in self._yobj if i.get("kind", "valve") == attr]
        else:
            if group is None:
                group = self.get_root()
            return [v if element else v.text.strip() for v in group.findall(attr)]

# ============= EOF =============================================
