# # ===============================================================================
# # Copyright 2012 Jake Ross
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #   http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.
# # ===============================================================================
#
# # ============= enthought library imports =======================
# from traits.api import HasTraits, Property, List, Button, Str, File, Any
# from traitsui.api import View, Item, HGroup, TabularEditor
# from traitsui.tabular_adapter import TabularAdapter
# # ============= standard library imports ========================
# from uncertainties import ufloat
# import xlrd
# # ============= local library imports  ==========================
# from pychron.processing.argon_calculations import calculate_arar_age
#
#
# class ExcelMixin(object):
# def _make_row(self, sheet, ri, cast=str):
# return [cast(sheet.cell(ri, ci).value) for ci in range(sheet.ncols)]
#
# class Constants(ExcelMixin):
#     age_units = 'Ma'
#     def __init__(self, sheet):
#         self.sheet = sheet
#         lambda_e = self._get_constant('lambda_e', 5.81e-11, 1.6e-13)
#         lambda_b = self._get_constant('lambda_b', 4.962e-10, 9.3e-13)
#
#         self.lambda_k = lambda_e + lambda_b
#
#         self.lambda_Ar37 = self._get_constant('lambda_Ar37', 0.01975, 0)  # per day
#         self.lambda_Ar39 = self._get_constant('lambda_Ar39', 7.068000e-6, 0)  # per day
#         self.lambda_Cl36 = self._get_constant('lambda_Cl36', 6.308000e-9, 0)  # per day
#
#         # atmospheric ratios
#         self.atm4036 = self._get_constant('Ar40_Ar36_atm', 295.5, 0)
#         self.atm4038 = self._get_constant('Ar40_Ar38_atm', 1575, 2)
#
#         # atm4038 = ufloat((1575, 2))
#         self.atm3638 = self.atm4038 / self.atm4036
#         self.atm3836 = self.atm4036 / self.atm4038
#
#     def _get_constant(self, name, value, error):
#         sheet = self.sheet
#         header = self._make_row(sheet, 0)
#         idx = header.index(name)
#         idx_err = header.index('{}_err'.format(name))
#         try:
#             value = sheet.cell(1, idx).value
#         except Exception, e:
#             print 'exception', e
#
#         try:
#             error = sheet.cell(1, idx_err).value
#         except Exception, e:
#             print 'exception', e
#
# #        print type(value)
#         return ufloat(value, error)
#
#
# class Result(HasTraits):
#     age = Any
#     identifier = Str
#
# class ResultAdapter(TabularAdapter):
#     columns = [
#              ('Identifier', 'identifier'),
#              ('Age', 'age'),
#              ('Error', 'age_error'),
#              ]
#     age_text = Property
#     age_error_text = Property
#
#     def _float_fmt(self, v, n):
#         return '{{:0.{}f}}'.format(n).format(v)
#
#     def _get_value(self, attr):
#         v = getattr(self.item, attr)
#         return self._float_fmt(v.nominal_value, 5)
#
#     def _get_error(self, attr):
#         v = getattr(self.item, attr)
#         return self._float_fmt(v.std_dev, 6)
#
#     def _get_age_text(self):
#         return self._get_value('age')
#
#     def _get_age_error_text(self):
#         return self._get_error('age')
#
# class AgeCalculator(HasTraits, ExcelMixin):
#     calc_button = Button
#     results = List
#     path = File
#     def _load_irrad_info_from_file(self, sheet):
#         ir_header = self._make_row(sheet, 0)
#
#         idx_k4039 = ir_header.index('k4039')
#         idx_k4039err = ir_header.index('k4039_err')
#         idx_k3839 = ir_header.index('k3839')
#         idx_k3839err = ir_header.index('k3839_err')
#         idx_k3739 = ir_header.index('k3839')
#         idx_k3739err = ir_header.index('k3839_err')
#
#         idx_ca3937 = ir_header.index('ca3937')
#         idx_ca3937err = ir_header.index('ca3937_err')
#         idx_ca3837 = ir_header.index('ca3837')
#         idx_ca3837err = ir_header.index('ca3837_err')
#         idx_ca3637 = ir_header.index('ca3637')
#         idx_ca3637err = ir_header.index('ca3637_err')
#
#         idx_cl3638 = ir_header.index('cl3638')
#         idx_cl3638err = ir_header.index('cl3638_err')
#
#         row = self._make_row(sheet, 1, cast=float)
#         irrad_info = [(row[idx_k4039], row[idx_k4039err]),
#                                (row[idx_k3839], row[idx_k3839err]),
#                                (row[idx_k3739], row[idx_k3739err]),
#                                (row[idx_ca3937], row[idx_ca3937err]),
#                                (row[idx_ca3837], row[idx_ca3837err]),
#                                (row[idx_ca3637], row[idx_ca3637err]),
#                                (row[idx_cl3638], row[idx_cl3638err])
#                                ]
#
#         return irrad_info + [[], 1]
#
#     def _calc_from_file(self, path):
#         self.results = []
#
#         workbook = xlrd.open_workbook(path)
#         ir_s = workbook.sheet_by_name('irradiation')
#         irrad_info = self._load_irrad_info_from_file(ir_s)
#
#         i_s = workbook.sheet_by_name('intensities')
#         header = self._make_row(i_s, 0)
#
#         try:
#             bl_s = workbook.sheet_by_name('blanks')
#             bl_header = self._make_row(bl_s, 0)
#         except xlrd.XLRDError:
#             bl_s = None
#             bl_header = None
#         try:
#             bg_s = workbook.sheet_by_name('backgrounds')
#             bg_header = self._make_row(bg_s, 0)
#         except xlrd.XLRDError:
#             bg_header = None
#             bg_s = None
#
#         try:
#             bs_s = workbook.sheet_by_name('baselines')
#             bs_header = self._make_row(bs_s, 0)
#         except xlrd.XLRDError:
#             bs_header = None
#             bs_s = None
#
#         idx_j = header.index('j')
#         idx_jerr = header.index('j_err')
#         idx_ic = header.index('ic')
#         idx_ic_err = header.index('ic_err')
#
#         c_s = workbook.sheet_by_name('constants')
#         constants_obj = Constants(c_s)
#
#         for ri in range(1, i_s.nrows):
#             signals = self._load_signals(header, i_s, ri)
#             blanks = self._load_signals(bl_header, bl_s, ri)
#             baselines = self._load_signals(bs_header, bs_s, ri)
#             backgrounds = self._load_signals(bg_header, bg_s, ri)
#
#             row = self._make_row(i_s, ri)
#             idn = row[0]
#             j = map(float, (row[idx_j], row[idx_jerr]))
#             ic = map(float, (row[idx_ic], row[idx_ic_err]))
#             arar_result = calculate_arar_age(signals, baselines, blanks, backgrounds, j, irrad_info,
#                                            a37decayfactor=1, a39decayfactor=1,
#                                            ic=ic,
#                                            arar_constants=constants_obj)
#
#             self.results.append(Result(identifier=idn,
#                                        age=arar_result['age'] / 1e6))
#
#     def _load_signals(self, header, sheet, ri):
#         if sheet is not None:
#             row = self._make_row(sheet, ri)
#             idn = row[0]
#             row = [idn] + map(float, row[1:])
#
#             idx_40 = header.index('Ar40')
#             idx_40err = header.index('Ar40_err')
#             idx_39 = header.index('Ar39')
#             idx_39err = header.index('Ar39_err')
#             idx_38 = header.index('Ar38')
#             idx_38err = header.index('Ar38_err')
#             idx_37 = header.index('Ar37')
#             idx_37err = header.index('Ar37_err')
#             idx_36 = header.index('Ar36')
#             idx_36err = header.index('Ar36_err')
#             signals = [(row[idx_40], row[idx_40err]),
#                      (row[idx_39], row[idx_39err]),
#                      (row[idx_38], row[idx_38err]),
#                      (row[idx_37], row[idx_37err]),
#                      (row[idx_36], row[idx_36err])]
#
#         else:
#             signals = [(0, 0), (0, 0), (0, 0), (0, 0), (0, 0)]
#         return signals
#
#     def _calc_button_fired(self):
#         path = self.path
#         self._calc_from_file(path)
#
#     def traits_view(self):
#         v = View(
#                HGroup(Item('path', springy=True, show_label=False),
#                       Item('calc_button', enabled_when='path', show_label=False)),
#                Item('results', editor=TabularEditor(adapter=ResultAdapter(),
#                                                     editable=False
#                                                     ),
#
#                     show_label=False, style='custom'),
#                title='Age Calculator',
#                width=500,
#                height=300,
#                )
#         return v
#
# if __name__ == '__main__':
#     ag = AgeCalculator()
#     ag.path = '/Users/argonlab2/Sandbox/age_calculator_template.xls'
#     ag.configure_traits()
# # ============= EOF =============================================
