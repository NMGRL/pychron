# ===============================================================================
# Copyright 2017 ross
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
from __future__ import absolute_import
import xlrd
import os
from traits.api import File
from pychron.data_mapper.sources.nu_source import NuFileSource

DATA_FILE_COL = 1
SAMPLE_COL = 5
MATERIAL_COL = 7

J_COL = 1
JERR_COL = 2
IRRADIATION_COL = 18

class WiscArNuSource(NuFileSource):
    metadata_path = File

    def get_analysis_import_spec(self, delimiter=None):
        spec = super(WiscArNuSource, self).get_analysis_import_spec(delimiter=delimiter)

        # load the metadata located in an xls file
        wb = xlrd.open_workbook(self.metadata_path)
        datasheet = wb.sheet_by_name('Data')

        name = os.path.basename(self.path)
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
        return spec
    
# ============= EOF =============================================
