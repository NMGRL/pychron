# ===============================================================================
# Copyright 2013 Jake Ross
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
import time

from traits.api import Str, Any, Bool, Dict, List
from traitsui.api import View, Item, EnumEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================
import yaml
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.pychron_constants import NULL_STR


class SampleChanger(Loggable):
    chamber = Str
    manager = Any

    _isolated = Bool
    _rules = Dict

    chambers = List

    # def __init__(self, *args, **kw):
    # super(SampleChanger, self).__init__(*args, **kw)
    # self.chambers = self._get_chambers()
    # self._load_chamber_rules()

    def setup(self):
        rules = self._get_rules()
        if rules:
            self.chambers = self._get_chambers(rules)
            return True

    def _chamber_changed(self, new):
        if new and new != NULL_STR:
            # load chamber rules
            self._load_chamber_rules(new)

    def check_finish(self):
        msg = None
        if not self._isolated:
            msg = '{} was never isolated'.format(self.chamber)
        elif not self._evacuated:
            msg = '{} is not evacuated'.format(self.chamber)
        return msg

    def check_evacuation(self):
        """
            is it ok to evacuate the chamber
        """
        isolated_bit = self._isolated

        # verify valves are actually closed
        rules = self._rules['isolate']

        opens = []
        for v in self._get_valves(rules, 'close'):
            state = self.manager.get_valve_state(v)
            if state:
                opens.append(v)

        if not isolated_bit:
            return 'Chamber was not isolated'
        elif opens:
            return 'Chamber is not isolated. Valves {} open'.format(','.join(opens))

    def isolate_chamber(self):
        if self._execute_message('isolate', 'pre'):
            self._isolate_chamber()
            return True
            # t = Thread(target=self._isolate_chamber)
            # t.start()

    def evacuate_chamber(self):
        if self._execute_message('evacuate', 'pre'):
            self._evacuate_chamber()
            return True
            # t = Thread(target=self._evacuate_chamber)
            # t.start()

    def finish_chamber_change(self):
        if self._execute_message('finish', 'pre'):
            self._finish_chamber_change()
            return True
            # t = Thread(target=self._finish_chamber_change)
            # t.start()

    def _finish_chamber_change(self):
        self._isolated = False
        self._evacuated = False

        self.info('========================== finish sample change')
        rules = self._rules['finish']
        self._execute_rules(rules)
        self._execute_message('finish', 'post')

    def _evacuate_chamber(self):
        self._evacuated = True

        self.info('========================== evacuate chamber')
        rules = self._rules['evacuate']
        self._execute_rules(rules)
        self._execute_message('evacuate', 'post')

    def _isolate_chamber(self):
        self._evacuated = False
        self._isolated = True

        self.info('========================== isolating chamber')
        rules = self._rules['isolate']
        self._execute_rules(rules)
        self._execute_message('isolate', 'post')

    def _execute_message(self, name, kind):
        rules = self._rules[name]
        try:
            return self.confirmation_dialog(rules['{}_message'.format(kind)])
        except KeyError:
            pass

        return True

    def _execute_rules(self, rules):
        unlock_valves = self._get_valves(rules, 'unlock')
        for v in unlock_valves:
            self.manager.set_software_lock(v, False)

        close_valves = self._get_valves(rules, 'close')
        for v in close_valves:
            self.manager.close_valve(v)
            time.sleep(0.25)

        time.sleep(1)
        open_valves = self._get_valves(rules, 'open')
        for v in open_valves:
            self.manager.open_valve(v)
            time.sleep(0.25)

        lock_valves = self._get_valves(rules, 'lock')
        for v in lock_valves:
            self.manager.set_software_lock(v, True)

        self.manager.refresh_canvas()

    def _get_valves(self, rules, key):
        v = []
        if rules.has_key(key):
            valves = rules[key]
            if valves:
                v = valves.split(',')
        return v

    def _get_chambers(self, rules=None):
        if rules is None:
            rules = self._get_rules()

        c = [NULL_STR, ]
        if rules:
            c.extend(rules.keys())

        return c

    def _load_chamber_rules(self, name):
        """
            chamber_name:
              isolate:
               open:
               close:
               lock:
               unlock:
             evacuate:
               ...
             finish:
               ...

            e.g

            CO2:
             isolate:
              open: A,B,C
              close: D,E,F
              lock: A,B,C
              unlock: D,E,F

        """
        rules = self._get_rules()
        if rules:
            self._rules = rules[name]

    def _get_rules(self):
        path = os.path.join(paths.scripts_dir, 'sample_change_rules.yaml')
        if os.path.isfile(path):
            with open(path, 'r') as rfile:
                return yaml.load(rfile)
        else:
            self.warning_dialog('No sample change rules defined at {}. \n\n'
                                'Please see documentation for appropriate file format'.format(path))

    def chamber_select_view(self):
        v = View(Item('chamber', editor=EnumEditor(name='chambers')),
                 kind='livemodal',
                 title='Select Chamber',
                 resizable=True,
                 width=200,
                 buttons=['OK', 'Cancel']
                 )
        return v
        # ============= EOF =============================================
