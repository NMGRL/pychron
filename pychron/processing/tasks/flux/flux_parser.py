# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from collections import namedtuple
import csv

from traits.api import Str


# ============= standard library imports ========================
# ============= local library imports  ==========================
import xlrd
from pychron.loggable import Loggable


Position = namedtuple('Position', 'hole_id, identifier, j, je')


class FluxParser(Loggable):
    path = Str

    def get_npositions(self):
        return len(list(self.iterpositions()))

    def iterpositions(self):
        return self._iter_positions()

    def _get_index(self, header, ks):
        if not isinstance(ks, (list, tuple)):
            ks = (ks,)

        for k in ks:
            for ki in (k, k.upper(), k.lower(), k.capitalize(), k.replace('_', '')):
                try:
                    return header.index(ki)
                except ValueError:
                    pass

    def get_irradiation(self):
        """
         return irradiation, level
        """
        return self._get_irradiation()

    def _get_irradiation(self):
        return '', ''


class XLSFluxParser(FluxParser):
    def _get_irradiation(self):
        wb = xlrd.open_workbook(self.path)
        sheet = wb.sheet_by_index(0)

        row = sheet.row_values(0)
        return row[0], row[1]

    def _iter_positions(self):

        header_offset = 2
        wb = xlrd.open_workbook(self.path)
        sheet = wb.sheet_by_index(0)

        header = sheet.row_values(1)
        hole_idx = self._get_index(header, 'hole')
        i_idx = self._get_index(header, ('runid', 'labnumber', 'l#', 'identifier'))
        j_idx = self._get_index(header, 'j')
        j_err_idx = self._get_index(header, ('j_error', 'j err'))

        for ri in xrange(sheet.nrows - header_offset):
            ri += header_offset

            hole = sheet.cell_value(ri, hole_idx)
            if hole:
                hole = int(hole)
                ident = sheet.cell_value(ri, i_idx)
                j = sheet.cell_value(ri, j_idx)
                je = sheet.cell_value(ri, j_err_idx)
                j, je = float(j), float(je)
                yield Position(hole, '{:n}'.format(ident), j, je)


class CSVFluxParser(FluxParser):
    def _get_irradiation(self):
        with open(self.path, 'r') as fp:
            reader = csv.reader(fp)
            return reader.next()

    def _iter_positions(self):
        with open(self.path, 'r') as fp:
            reader = csv.reader(fp)
            _ = reader.next()
            header = reader.next()

            hidx = self._get_index(header, 'hole')
            ididx = self._get_index(header, ('runid', 'labnumber', 'l#', 'identifier'))
            jidx = self._get_index(header, 'j')
            jeidx = self._get_index(header, 'j_err')

            for line in reader:
                if line:
                    yield Position(line[hidx],
                                   line[ididx],
                                   line[jidx], line[jeidx])


# =============EOF =============================================
