# ===============================================================================
# Copyright 2013 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
from datetime import datetime

import xlrd
from xlrd.biffh import XLRDError


# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.managers.data_managers.data_manager import DataManager


class XLSDataManager(DataManager):
    wb = None

    def open(self, p):
        self.wb = xlrd.open_workbook(p)

    def strftime(self, d, f):
        d = datetime(*xlrd.xldate_as_tuple(d, self.wb.datemode))
        return d.strftime(f)

    def iterrows(self, sheet, start=None, end=None):
        if start is None:
            start = 0
        if end is None:
            end = sheet.nrows

        # print start, end
        return (sheet.row(i) for i in xrange(start, end, 1))

    def get_sheet(self, names):
        if self.wb:
            if not isinstance(names, (list, tuple)):
                names = [names]

            for ni in names:
                try:
                    if isinstance(ni, str):
                        sheet = self.wb.sheet_by_name(ni)
                    elif isinstance(ni, int):
                        sheet = self.wb.sheet_by_index(ni)
                    else:
                        sheet = ni
                except XLRDError:
                    continue

                return sheet

    def get_column_idx(self, names, sheet=None, optional=False):
        sheet = self.get_sheet(sheet)
        if sheet:
            header = sheet.row_values(0)
            if not isinstance(names, (list, tuple)):
                names = (names,)

            header = map(str.lower, map(str, header))
            for attr in names:
                for ai in (attr, attr.lower(), attr.upper(), attr.capitalize()):
                    if ai in header:
                        return header.index(ai)

            if not optional:
                cols = ','.join(names)
                self.warning_dialog('Invalid sheet. No column named "{}"'.format(cols))

# ============= EOF =============================================
