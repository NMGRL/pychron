from pychron.experiment.importer.mass_spec_binary_extractor import MassSpecBinaryExtractor

__author__ = 'ross'

import unittest


class Expected(object):
    runid = '59273-01A'
    project = 'Zimmerer'
    sample = 'ORGAN-8'
    material = 'Biotite'
    investigator = 'Zimmerer'
    fits = 'LLLLLL'
    locality = ''
    rundate = '3/3/2010'
    irradlabel = 'NM-227L'
    runhour = 2.0
    version = 7.875
    emv = [1.4503029584884644, 0.0]
    optemp = 0
    history = 'Multiplier Baseline = L @ --- @ ---; Ar40 = L @ --- @ ---; Ar39 = L @ --- @ ---; ' \
              'Ar38 = L @ --- @ ---; Ar36 = L @ --- @ ---; Ar37 = L @ --- @ ---; ' \
              'argonlab - 3/11/2010 @ 10:08:42 AM @ --- @ ---; Ar40 bk val,er = Bracketing blanks @ --- @ ---; ' \
              'Ar39 bk val,er = Bracketing blanks @ --- @ ---; Ar38 bk val,er = Bracketing blanks @ --- @ ---; ' \
              'Ar36 bk val,er = Bracketing blanks @ --- @ ---; Ar37 bk val,er = Bracketing blanks @ --- @ ---'
    scalefactor=1000000000.0, 1000000000.0
    extract_device='CO2'
    extract_value=0.0
    final_set_power=0.5
    totdur_heating = 0
    totdur_atsetpoint=0
    gain = [166124.90625, 0.0]
    calc_with_ratio = False
    system_number = 3
    mol_ref_iso = 8.004109832880028e-16
    disc=1.00600004196167
    disc_err=0.0010000000474974513
    j=0.002384300110861659
    j_err=2.048499936790904e-06
    resistor_values =[1.0,0,0]
    isogrp = 'Ar'
    niso = 5
    nratio=0
    detectors=[1,1,1,1,1]
    ndet = 1
    refdetnum=1
    signormfactor=1
    ncyc=0
    isokeys=['Ar40', 'Ar39', 'Ar38', 'Ar36', 'Ar37']
    runday=8462.0
    ncnts=[48, 72, 24, 120, 24]

class MassSpecBinaryExtractorTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.extractor = MassSpecBinaryExtractor()
        cls.specs = cls.extractor.import_file('./data/MSDataFile_7875')
        cls.expected = Expected()

    def test_runid(self):
        self._test_spec_attr('runid')

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
    # self._test_spec_attr('comment', '1350; 1800/20')

    def test_runhour(self):
        self._test_spec_attr('runhour')

    def test_version(self):
        self._test_spec_attr('version')

    def test_optemp(self):
        self._test_spec_attr('optemp')

    def test_emv(self):
        self._test_spec_attr('emv')

    def test_history(self):
        self._test_spec_attr('history')

    def test_scalefactor(self):
        self._test_spec_attr('scalefactor')

    def test_extract_device(self):
        self._test_spec_attr('extract_device')

    def test_extract_value(self):
        self._test_spec_attr('extract_value')

    def test_final_set_power(self):
        self._test_spec_attr('final_set_power')

    def test_totdur_heating(self):
        self._test_spec_attr('totdur_heating')

    def test_totdur_atsetpoint(self):
        self._test_spec_attr('totdur_atsetpoint')

    def test_gain(self):
        self._test_spec_attr('gain')

    def test_calc_with_ratio(self):
        self._test_spec_attr('calc_with_ratio')

    def test_system_number(self):
        self._test_spec_attr('system_number')

    def test_mol_ref_iso(self):
        self._test_spec_attr('mol_ref_iso')

    def test_disc(self):
        self._test_spec_attr('disc')

    def test_disc_err(self):
        self._test_spec_attr('disc_err')

    def test_j(self):
        self._test_spec_attr('j')

    def test_j_err(self):
        self._test_spec_attr('j_err')

    def test_resistor_values(self):
        self._test_spec_attr('resistor_values')

    def test_isogrp(self):
        self._test_spec_attr('isogrp')

    def test_niso(self):
        self._test_spec_attr('niso')

    def test_nratio(self):
        self._test_spec_attr('nratio')

    def test_detectors(self):
        self._test_spec_attr('detectors')

    def test_ndet(self):
        self._test_spec_attr('ndet')

    def test_refdet_num(self):
        self._test_spec_attr('refdetnum')

    def test_signormfactor(self):
        self._test_spec_attr('signormfactor')

    def test_ncyc(self):
        self._test_spec_attr('ncyc')

    def test_isokeys(self):
        self._test_spec_attr('isokeys')

    def test_runday(self):
        self._test_spec_attr('runday')

    def test_ncnts(self):
        self._test_spec_attr('ncnts')

    def _test_spec_attr(self, attr, idx=0):
        self.assertEqual(getattr(self.specs[idx], attr),
                         getattr(self.expected, attr))


if __name__ == '__main__':
    unittest.main()
