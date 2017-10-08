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
from traits.api import Any, Dict

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.paths import paths


class LoaderLogic(Loggable):
    rules = Dict
    switches = Dict
    manager = Any

    def get_check_message(self):
        # rt = ''.join(['<td>{}</td>'.format(r) for r in self._rules])
        # bt = ''.join(['<td>{}</td>'.format('X' if not b else '') for b in self._bits])
        rs = zip(self._rules, self._bits)
        rs = [ri for ri in rs if not ri[1]]
        checks = ', '.join([ri[0] for ri in rs])
        return '{} checks are not OK'.format(checks)

    def check(self, name):
        rule = self.rules[name]
        return self._check_rule(name, rule)

    def open(self, name):
        name = self.switches[name]
        key = '{}_O'.format(name)
        return self.check(key)

    def close(self, name):
        name = self.switches[name]
        key = '{}_C'.format(name)
        return self.check(key)

    def load_config(self):
        p = os.path.join(paths.device_dir, 'furnace', 'logic.yaml')
        with open(p, 'r') as fp:
            yd = yaml.load(fp)
            self.rules = yd['rules']
            self.switches = yd['switches']

    def _convert_switch_name(self, name):

        return next((k for k, v in self.switches.iteritems() if v == name), None)

    def _check_rule(self, key, rule):
        bits = []
        self.debug('------- check rule {}: {}'.format(key, ','.join(rule)))
        for flag in rule:
            if '_' in flag:
                key, state = flag.split('_')
                name = self._convert_switch_name(key)
                if name in self.switches:
                    s = self.manager.get_switch_state(name)
                    b = False
                    if (s and state == 'O') or (not s and state == 'C'):
                        b = True

                    self.debug('switch state: name={}, state={}, s={}, b={}'.format(name, state, s, b))
                else:
                    self.debug('name not in switches {}'.format(name))
                    self.debug('switches={}'.format(self.switches.keys()))
                    b = self.manager.get_flag_state(flag)
            else:
                b = self.manager.get_flag_state(flag)
            bits.append(b)

        self._rules = rule
        self._bits = bits

        rs = ['{:>10}'.format(f) for f in rule]
        bs = ['{:>10}'.format(bi) for bi in bits]
        rs = '|'.join(rs)
        bs = '|'.join(bs)
        self.debug(rs)
        self.debug(bs)

        return all(bits)

# ============= EOF =============================================
