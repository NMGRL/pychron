from pychron.processing.autoupdate_parser import AutoupdateParser

__author__ = 'ross'

import unittest


class MassSpecMassSpecDiffTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sample_id = 'AF-72'
        cls.analysis_id = 0

        p1 = '../data/autoupdate_AF_72_7.875.txt'
        p1 = '../data/autoupdate_AF_72_7.875.25.txt'
        p2 = '../data/autoupdate_AF_72_8.03b.txt'
        cls.parsers = {}
        for k, p in (('7.875', p1), ('8.03b', p2)):
            pa = AutoupdateParser()
            pa.parse(p)
            cls.parsers[k] = pa

    def test_Ar40(self):
        self._compare_value('Ar40')

    def test_Ar39(self):
        self._compare_value('Ar39')

    def test_Ar38(self):
        self._compare_value('Ar38')

    def test_Ar37(self):
        self._compare_value('Ar37')

    def test_Ar36(self):
        self._compare_value('Ar36')

    def test_Ar40Er(self):
        self._compare_value('Ar40Er')

    # def test_Ar39(self):
    # self._compare_value('Ar39')
    #
    # def test_Ar38(self):
    #     self._compare_value('Ar38')
    #
    # def test_Ar37(self):
    #     self._compare_value('Ar37')
    #
    # def test_Ar36(self):
    #     self._compare_value('Ar36')
    #
    def _get_value(self, pk, ak):
        parser = self.parsers[pk]
        s = parser.samples[self.sample_id]
        a = s.analyses[self.analysis_id]
        return getattr(a, ak)

    def _compare_value(self, k):
        p1 = self._get_value('7.875', k)
        p2 = self._get_value('8.03b', k)

        self.assertEqual(p1, p2)


if __name__ == '__main__':
    unittest.main()
