
__author__ = 'ross'

from pychron.core.ui import set_toolkit
set_toolkit('qt4')
import unittest

from pychron.entry.loaders.sample_loader import SampleLoader, XLSParser


class SampleLoaderTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loader=SampleLoader()
        cls.parser=XLSParser()
        p='../data/sample.xls'
        cls.parser.load(p)

    def test_itervalues(self):
        values=list(self.parser.itervalues(keys=('sample','material')))
        self.assertEqual(values[1]['sample'],'B')


if __name__ == '__main__':
    unittest.main()
