from pychron.experiment.importer.mass_spec_binary_extractor import MassSpecBinaryExtractor

__author__ = 'ross'

import unittest


class Expected(object):
    project='Zimmerer'
    sample = 'ORGAN-8'
    material = 'Biotite'
    investigator = 'Zimmerer'
    fits = 'LLLLLL'
    locality=''
    rundate = '3/3/2010'
    irradlabel='NM-227L'
    runhour = 2.0
    version = 7.875

class MassSpecBinaryExtractorTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.extractor = MassSpecBinaryExtractor()
        cls.specs = cls.extractor.import_file('./data/MSDataFile_7875')
        cls.expected = Expected()

    def test_sample(self):
        self._test_spec_attr('sample')

    def test_material(self):
        self._test_spec_attr('material')

    def test_investigator(self):
        self._test_spec_attr('investigator')

    def test_project(self):
        self._test_spec_attr('project')

    def test_locality(self):
        self._test_spec_attr('locality')

    def test_rundate(self):
        self._test_spec_attr('rundate')

    def test_irradlabel(self):
        self._test_spec_attr('irradlabel')

    def test_fits(self):
        self._test_spec_attr('fits')

    # def test_comment(self):
    #     self._test_spec_attr('comment', '1350; 1800/20')

    def test_runhour(self):
        self._test_spec_attr('runhour')

    def test_version(self):
        self._test_spec_attr('version')

    def _test_spec_attr(self, attr, idx=0):
        self.assertEqual(getattr(self.specs[idx], attr),
                         getattr(self.expected, attr))


if __name__ == '__main__':
    unittest.main()
