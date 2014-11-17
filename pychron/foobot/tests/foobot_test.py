from pychron.core.helpers.logger_setup import logging_setup
from pychron.foobot.scripts.run import Run

logging_setup('foobot_unitest')
from pychron.foobot.foobot import Foobot

__author__ = 'argonlab2'

import unittest

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.bot=Foobot()

class FoobotTestCase(BaseTestCase):
    def test_script_factory(self):
        sobj = self.bot.script_factory('run')
        self.assertIsInstance(sobj, Run)

    def test_get_tokens(self):
        script, tokens = self.bot.get_tokens('run experiment')
        self.assertListEqual(tokens, ['experiment'])

    def test_enter_context(self):
        cmd = '%mz'
        self.bot.process_command(cmd)
        self.assertEqual(self.bot.context.name, 'mz')

    def test_mz_easter_egg(self):
        self.bot.process_command('%mz')
        self.bot.process_command('80085')
        self.assertEqual(self.bot.ee, True)

    def test_mz_easter_egg_fail(self):
        self.bot.process_command('80085')
        self.assertEqual(self.bot.ee, False)


class ConvertTestCase(BaseTestCase):
    def test_convert_float(self):
        cmd = 'convert 3.4'
        ret = self.bot.process_command(cmd)
        self.assertEqual(ret, 340.0)

    def test_convert_int(self):
        cmd = 'convert 3'
        ret = self.bot.process_command(cmd)
        self.assertEqual(ret, 300)

    def test_tokens(self):
        cmd ='convert 3.4'
        name, tokens=self.bot.get_tokens(cmd)

        self.assertListEqual(['3.4'], [''.join(tokens)])


class RunTestCase(BaseTestCase):
    def test_process_run_experiment(self):
        cmd = 'run experiment'
        script= self.bot.get_script_name(cmd)
        self.assertEqual(script, 'run')

    def test_process_run_experiment1(self):
        cmd = 'run experiment'
        ret = self.bot.process_command(cmd)
        self.assertTrue(ret)

    def test_process_run_experiment2(self):
        cmd = 'run experimentda'
        ret = self.bot.process_command(cmd)
        self.assertEqual('''"experimentda" is not a valid function for "run". valid=experiment''', ret)


if __name__ == '__main__':
    unittest.main()
