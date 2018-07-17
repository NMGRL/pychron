from __future__ import absolute_import

import os
import unittest

from pychron.data_mapper.sources.wiscar_meta_parser import WiscArMetaParser
# from pychron.data_mapper.sources.wiscar_source import WiscArNuSource
# from pychron.data_mapper.tests.file_source import BaseFileSourceTestCase
from pychron.data_mapper.tests import fget_data_dir


class Spec:
    def __init__(self):
        self.run_spec = RunSpec()


class RunSpec:
    pass


class WiscArMetaTxtTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        parser = WiscArMetaParser()

        spec = Spec()
        p = os.path.join(fget_data_dir(), 'WISCAR_test_metadata.txt')
        parser.populate_spec(p, spec)
        cls.expected = {'sample': 'H-15-27A',
                        'irradiation': 'UW133'}
        cls.spec = spec

    def test_sample(self):
        self.assertEqual(self.expected['sample'], self.spec.run_spec.sample)

    def test_irradiation(self):
        self.assertEqual(self.expected['irradiation'], self.spec.run_spec.irradiation)

#
# class WiscArNuTestCase(BaseFileSourceTestCase):
#     @classmethod
#     def setUpClass(cls):
#         cls.src = WiscArNuSource()
#         p = os.path.join(fget_data_dir(), 'Data_NAG1072.RUN')
#         pnice = os.path.join(fget_data_dir(), 'wiscar.nice')
#         mp = os.path.join(fget_data_dir(), 'H-15-27_C5_20170610.xls')
#         cls.src.path = p
#         cls.src.nice_path = pnice
#         cls.src.metadata_path = mp
#         cls.spec = cls.src.get_analysis_import_spec()
#
#         cls.expected = {'runid': 'Data_NAG1072',
#                         'irradiation': 'UW133',
#                         'irradiation_level': 'A',
#                         'sample': 'Blank 1',
#                         'material': 'Blank',
#                         'project': 'NoProject',
#                         'j': 0.000811,
#                         'j_err': 0.0000024,
#                         'timestamp_month': 6,
#                         'cnt40': 200,
#                         'cnt39': 200,
#                         'cnt38': 200,
#                         'cnt37': 200,
#                         'cnt36': 200,
#                         'discrimination': 1.0462399093612802,
#                         'uuid': 'Data_NAG1072'
#                         }
#
#     def test_irradiation(self):
#         self.assertEqual(self.spec.run_spec.irradiation, self.expected['irradiation'])
#
#     def test_level(self):
#         self.assertEqual(self.spec.run_spec.irradiation_level, self.expected['irradiation_level'])
#
#     def test_sample(self):
#         self.assertEqual(self.spec.run_spec.sample, self.expected['sample'])
#
#     def test_material(self):
#         self.assertEqual(self.spec.run_spec.material, self.expected['material'])
#
#     def test_project(self):
#         self.assertEqual(self.spec.run_spec.project, self.expected['project'])
#
#     def test_j(self):
#         self.assertEqual(self.spec.j, self.expected['j'])
#
#     def test_j_err(self):
#         self.assertEqual(self.spec.j_err, self.expected['j_err'])
#

if __name__ == '__main__':
    unittest.main()
