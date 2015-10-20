from pychron.core.ui import set_toolkit

set_toolkit('qt4')

from pychron.paths import paths, build_directories

paths.build('_unittest')
build_directories(paths)

from pychron.core.helpers.logger_setup import logging_setup

logging_setup('export_spec')
from pychron.processing.export.export_spec import MassSpecExportSpec
from pychron.core.helpers.isotope_utils import sort_isotopes

import unittest


class ExportSpecTestCase(unittest.TestCase):
    def setUp(self):
        data_path = '/Users/ross/Sandbox/aaaa_isotope.h5'
        self.spec = MassSpecExportSpec(data_path=data_path)

    def test_sorted_iter_isotopes(self):
        e = self.spec
        with self.spec.open_file():
            isotopes = list(e.iter_isotopes())
            isotopes = sort_isotopes(isotopes, key=lambda x: x[0])

            for (iso, det), siso in zip(isotopes, ('Ar40', 'Ar39',
                                                   'Ar38', 'Ar37', 'Ar36')):
                self.assertEqual(iso, siso)

    def test_non_fool_massspec(self):
        e = self.spec
        with e.open_file():
            det = e._get_baseline_detector('Ar40', 'H1')
            self.assertEqual(det, 'H1')

    def test_fool_massspec(self):
        e = self.spec
        with e.open_file():
            e.is_peak_hop = True
            det = e._get_baseline_detector('Ar40', 'H1')
            self.assertEqual(det, e.peak_hop_detector)

    def test_baseline(self):
        e = self.spec
        with e.open_file():
            det = 'H1'
            tb, vb = e.get_baseline_data('Ar40', det)
            self.assertEqual(len(tb), 10)

    def test_iter_isotopes(self):
        with self.spec.open_file():
            e = self.spec
            gen = e.iter_isotopes()
            iso, det = gen.next()
            self.assertEqual(iso, 'Ar36')
            self.assertEqual(det, 'CDD')

            iso, det = gen.next()
            self.assertEqual(iso, 'Ar37')
            self.assertEqual(det, 'CDD')

            iso, det = gen.next()
            self.assertEqual(iso, 'Ar38')
            self.assertEqual(det, 'CDD')

            iso, det = gen.next()
            self.assertEqual(iso, 'Ar39')
            self.assertEqual(det, 'CDD')

            iso, det = gen.next()
            self.assertEqual(iso, 'Ar40')
            self.assertEqual(det, 'CDD')


if __name__ == '__main__':
    unittest.main()
