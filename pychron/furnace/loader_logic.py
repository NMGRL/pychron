# ===============================================================================
# Copyright 2015 Jake Ross
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
import os

import yaml
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change, Dict
from traitsui.api import View, UItem, Item, HGroup, VGroup

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.paths import paths


class LoaderLogic(Loggable):
    rules = Dict
    switches = Dict
    manager = Any

    def check(self, name):
        rule = self.rules[name]
        return self._check_rule(rule)

    def open(self, name):
        name = self.switch_map[name]
        key = '{}_O'.format(name)
        return self.check(key)

    def close(self, name):
        name = self.switch_map[name]
        key = '{}_C'.format(name)
        return self.check(key)

    def load_config(self):
        p = os.path.join(paths.device_dir, 'furnace', 'logic.yaml')
        with open(p, 'r') as fp:
            yd = yaml.load(fp)
            self.rules = yd['rules']
            self.switches = yd['switches']

    def _check_rule(self, rule):
        bits = []
        for flag in rule:
            if '_' in flag:
                name, state = flag.split('_')
                if name in self.switches:
                    s = self.manager.get_switch_state(name)
                    b = False
                    if (s and state == 'C') or (not s and state == 'O'):
                        b = True
                else:
                    b = self.manager.get_flag_state(flag)
            else:
                b = self.manager.get_flag_state(flag)
            bits.append(b)

        return all(bits)

# ============= EOF =============================================
