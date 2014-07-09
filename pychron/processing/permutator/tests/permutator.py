import os
import unittest
from pychron.processing.permutator.permutator import Permutator

__author__ = 'argonlab2'


class Configuration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.perm = Permutator()
        p = 'pychron/processing/permutator/tests/data/config.yaml'
        if not os.path.isfile(p):
            p = './data/config.yaml'

        cls.perm.path = p

    def test_load(self):
        yd = self.perm.configuration_dict
        self.assertIsInstance(yd,dict)

    def test_fits(self):
        fits = self.perm.get_fits()
        self.assertEqual(fits, ['linear', 'parabolic'])








