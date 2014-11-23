# ===============================================================================
# Copyright 2014 Jake Ross
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
import time

from traits.api import HasTraits, Str, Float, Enum, List

# ============= standard library imports ========================
import yaml
# ============= local library imports  ==========================
from pychron.envisage.initialization.initialization_parser import InitializationParser
from pychron.loggable import Loggable
from pychron.paths import paths


class TestResult(HasTraits):
    name = Str
    duration = Float
    result = Enum('Passed', 'Fail', 'Skipped', 'Invalid')


class SystemTester(Loggable):
    results = List

    def do_test(self):
        yl = self._load()
        ip = InitializationParser()

        self.results = []

        # test database connections
        for i, ti in enumerate(yl):
            if self._verify_test(i, ti):
                if self._should_test(ti, ip):
                    self._do_test(ti, ip)
                else:
                    name = ti.get('name')
                    self.results.append(TestResult(name=name, result='Skipped'))
            else:
                name = ti.get('name', 'Test #{:02n}'.format(i+1))
                self.results.append(TestResult(name=name, result='Invalid'))

    def _do_test(self, testdict, ip):
        name = testdict['name']
        self.info('doing test {}'.format(name))
        func = getattr(self, '_test_{}'.format(name))
        st = time.time()

        result = TestResult(name=name)
        ret = func(ip)
        result.trait_set(duration=time.time() - st, result=ret)
        self.results.append(result)

    def _test_pychron_database(self, ip):
        return 'Passed'

    def _test_massspec_database(self, ip):
        return 'Passed'

    def _should_test(self, td, ip):
        """
        determine whether this test should be performed.

        for example database tests should be skipped in DatabasePlugin not enabled in the Initialization file
        :param td:
        :param ip:
        :return: True if should perform this test
        """
        ret = True
        plugin_name = td.get('plugin')
        if plugin_name:
            plugin = ip.get_plugin(plugin_name)
            if plugin is not None:
                self.debug('Plugin "{}" not in Initialization file "{}"'.format(plugin_name, ip.path))
                ret = False

        return ret

    def _verify_test(self, i, td):
        """
        verify this is a valid test dictionary

        :param i: counter
        :param td: test dict
        :return: True if valid test
        """
        ret = True
        for attr in ('name',):
            if not attr in td:
                self.warning('Failed to verify test #{:02n} no key={}, test={}'.format(i, attr, td))
                ret = False

        else:
            if not hasattr(self, '_test_{}'.format(td['name'])):
                self.warning('invalid test name. "{}"'.format(td['name']))
                ret = False

        return ret

    def _load(self):
        with open(paths.system_test, 'r') as fp:
            yd = yaml.load(fp)
        return yd

# ============= EOF =============================================



