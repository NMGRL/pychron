# ===============================================================================
# Copyright 2018 ross
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
import os

import xlrd

from pychron.loggable import Loggable

DATA_FILE_COL = 1
SAMPLE_COL = 5
MATERIAL_COL = 7

J_COL = 1
JERR_COL = 2
IRRADIATION_COL = 18


class WiscArMetaParser(Loggable):

    def populate_spec(self, path, spec):
        if path.endswith('.xls'):
            self._populate_xls(path, spec)
        else:
            self._populate_txt(path, spec)

    def _populate_txt(self, path, spec):
        delim = ' '
        with open(path, 'r') as wfile:
            line = next(wfile)
            # line 1: sample
            spec.run_spec.sample = line.split(':')[1].strip()

            # line 2: lat
            line = next(wfile)

            # line 3: long
            line = next(wfile)

            # line 4: elevation
            line = next(wfile)

            # line 5: pi
            line = next(wfile)

            # line 6-8 blank
            next(wfile)
            next(wfile)
            next(wfile)

            # line 9 irradiation
            irrad = next(wfile)
            ln = next(wfile)
            level = next(wfile)
            position = next(wfile)
            if not spec.run_spec.labnumber:
                # for airs and blanks labnumber and irradiation already set
                spec.run_spec.irradiation = irrad.split(':')[1].strip()

                spec.run_spec.labnumber = ln.split(':')[1].strip()
                spec.run_spec.irradiation_level = level.split(':')[1].strip()
                spec.run_spec.irradiation_position = int(position.split(':')[1].strip())

            spec.j = 0
            spec.j_err = 0

    def _populate_xls(self, path, spec):
        # load the metadata located in an xls file
        wb = xlrd.open_workbook(path)
        datasheet = wb.sheet_by_name('Data')

        name = os.path.basename(path)
        r = datasheet.row(0)
        spec.run_spec.irradiation = r[IRRADIATION_COL].value
        spec.run_spec.irradiation_level = 'A'

        for row in datasheet.get_rows():
            if row[0].value == 'J':
                spec.j = float(row[J_COL].value)
                spec.j_err = float(row[JERR_COL].value)

            if row[DATA_FILE_COL].value == name:
                break

        else:
            return spec

        spec.run_spec.sample = row[SAMPLE_COL].value
        spec.run_spec.material = row[MATERIAL_COL].value
        spec.run_spec.project = 'NoProject'


# ============= EOF =============================================
