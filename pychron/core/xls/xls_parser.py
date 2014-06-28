#===============================================================================
# Copyright 2013 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================

#============= enthought library imports =======================

#============= standard library imports ========================
#============= local library imports  ==========================
import xlrd

from pychron.core.csv.csv_parser import BaseColumnParser



# @provides(IColumnParser)
class XLSParser(BaseColumnParser):
    # def load(self, p, header_idx=0):
    # wb = xlrd.open_workbook(p)
    # sheet = wb.sheet_by_index(0)
    # self._sheet = sheet
    # self._header = map(str.strip, map(str, sheet.row_values(header_idx)))
    # self._header_offset=header_idx+1
    def _load(self, p, header_idx, sheet=None):
        wb = xlrd.open_workbook(p)

        if sheet is None:
            sheet = 0

        if isinstance(sheet, int):
            sheet = wb.sheet_by_index(sheet)
        else:
            sheet = wb.sheet_by_name(sheet)

        self.workbook = wb
        self._sheet = sheet
        self._header = map(str.strip, map(str, sheet.row_values(header_idx)))

    # def has_key(self, key):
    #     """
    #         if key is an int return true if key valid index
    #         if key is a str return true if key in _header
    #     """
    #     if isinstance(key, int):
    #         return 0<=key<len(self._header)
    #     else:
    #         return key in self._header
    #
    # def itervalues(self, keys=None):
    #     """
    #         returns a row iterator
    #         each iteration is a dictionary containing "keys"
    #         if keys is None return all values
    #
    #     """
    #     if keys is None:
    #         keys=self._header
    #
    #     return (dict([(ki,self.get_value(ri, ki)) for ki in keys]) for ri in self.iternrows())
    #
    # def iternrows(self):
    #     return xrange(self._header_offset, self._sheet.nrows, 1)

    def get_value(self, ri, ci):
        if not isinstance(ci, int):
            ci = self._get_index(ci)

        return self._sheet.cell_value(ri, ci)

    # def _get_index(self, ks):
    #
    #     if not isinstance(ks, (list, tuple)):
    #         ks = (ks,)
    #
    #     for k in ks:
    #         for ki in (k, k.upper(), k.lower(), k.capitalize(), k.replace('_', '')):
    #             try:
    #                 return self._header.index(ki)
    #             except ValueError, e:
    #                 print 'exep',e

    @property
    def nrows(self):
        return self._sheet.nrows

#============= EOF =============================================

