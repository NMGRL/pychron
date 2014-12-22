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
from traits.api import HasTraits, Str, Float, Enum, List
# ============= standard library imports ========================
import os
import time
import yaml
# ============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.paths import paths


class TestResult(HasTraits):
    name = Str
    plugin = Str
    duration = Float
    result = Enum('Passed', 'Failed', 'Skipped', 'Invalid')
    description = Str


class StartupTester(Loggable):
    results = List

    def __init__(self, *args, **kw):
        super(StartupTester, self).__init__(*args, **kw)
        self._tests = self._load()

    def test_plugin(self, plugin):
        pname = plugin.name
        try:
            tests = self._get_tests(pname)
        except KeyError:
            self.warning('Could not load tests for "{}". Check startup_test.yaml format'.format(pname))
            return

        if not tests:
            return

        for ti in tests:
            try:
                func = getattr(plugin, ti)
            except AttributeError:
                self.warning('Invalid test "{}" for plugin "{}"'.format(pname, ti))
                self.add_test_result(plugin=pname, name=ti, result='Invalid')
                continue

            try:
                description = getattr(plugin, '{}_description'.format(ti))
            except AttributeError:
                description=''

            self.info('Testing "{} - {}"'.format(pname, ti))
            st = time.time()
            result = func()
            if isinstance(result, bool):
                result = 'Passed' if result else 'Failed'
            elif result is None:
                result = 'Invalid'

            self.add_test_result(name=ti, plugin=pname,
                                 description=description,
                                 duration=time.time() - st,
                                 result=result)

    def ok_close(self):
        ok = True
        specresult = next((ri for ri in self.results
                           if 'spectrometer' in ri.plugin.lower() and ri.name == 'test_communication'), None)
        if specresult:
            ok = specresult.result == 'Passed'
        return ok

    def add_test_result(self, **kw):
        """
            rdict is a dictionary with the follow key:value_type

            name: str, duration: float, result: enum('Passed', 'Fail', 'Skipped', 'Invalid')
        """

        if kw:
            self.results.append(TestResult(**kw))

    def _get_tests(self, name):
        if self._tests:
            return next((ti['tests'] for ti in self._tests if ti['plugin'].lower() == name.lower()), None)

    def _load(self):
        if os.path.isfile(paths.startup_tests):
            with open(paths.startup_tests, 'r') as fp:
                yd = yaml.load(fp)
            return yd
        else:
            self.warning('No Startup Test file located at "{}"'.format(paths.startup_tests))

    @property
    def all_passed(self):
        a = all([ri.result in ('Passed','Skipped') for ri in self.results])
        return a

    # ============= EOF =============================================
    # def do_test(self):
    # yl = self._load()
    # ip = InitializationParser()
    #
    # self.results = []
    #
    # # test database connections
    #     for i, ti in enumerate(yl):
    #         if self._verify_test(i, ti):
    #             if self._should_test(ti, ip):
    #                 self._do_test(ti, ip)
    #             else:
    #                 name = ti.get('name')
    #                 self.results.append(TestResult(name=name, result='Skipped'))
    #         else:
    #             name = ti.get('name', 'Test #{:02n}'.format(i+1))
    #             self.results.append(TestResult(name=name, result='Invalid'))
    #
    # def _do_test(self, testdict, ip):
    #     name = testdict['name']
    #     self.info('doing test {}'.format(name))
    #     func = getattr(self, '_test_{}'.format(name))
    #     st = time.time()
    #
    #     result = TestResult(name=name)
    #     ret = func(ip)
    #     result.trait_set(duration=time.time() - st, result=ret)
    #     self.results.append(result)
    #
    # def _test_pychron_database(self, ip):
    #     return 'Passed'
    #
    # def _test_massspec_database(self, ip):
    #     return 'Passed'
    #
    # def _should_test(self, td, ip):
    #     """
    #     determine whether this test should be performed.
    #
    #     for example database tests should be skipped in DatabasePlugin not enabled in the Initialization file
    #     :param td:
    #     :param ip:
    #     :return: True if should perform this test
    #     """
    #     ret = True
    #     plugin_name = td.get('plugin')
    #     if plugin_name:
    #         plugin = ip.get_plugin(plugin_name)
    #         if plugin is not None:
    #             self.debug('Plugin "{}" not in Initialization file "{}"'.format(plugin_name, ip.path))
    #             ret = False
    #
    #     return ret
    #
    # def _verify_test(self, i, td):
    #     """
    #     verify this is a valid test dictionary
    #
    #     :param i: counter
    #     :param td: test dict
    #     :return: True if valid test
    #     """
    #     ret = True
    #     for attr in ('name',):
    #         if not attr in td:
    #             self.warning('Failed to verify test #{:02n} no key={}, test={}'.format(i, attr, td))
    #             ret = False
    #
    #     else:
    #         if not hasattr(self, '_test_{}'.format(td['name'])):
    #             self.warning('invalid test name. "{}"'.format(td['name']))
    #             ret = False
    #
    #     return ret
    #


