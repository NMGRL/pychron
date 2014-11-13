from pychron.core.helpers.logger_setup import logging_setup

logging_setup('foobot_unitest')
from pychron.foobot.foobot import Foobot, Run

__author__ = 'argonlab2'

import unittest


class FoobotTestCase(unittest.TestCase):
    def setUp(self):
        self.bot=Foobot()

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
        self.assertEqual('''run is not a valid function for experimentda. valid=experiment''', ret)

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

if __name__ == '__main__':
    unittest.main()
