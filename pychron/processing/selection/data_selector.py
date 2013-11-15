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
from traits.api import Any, List, \
     Enum, Button, Property, Int, Str, Tuple, Instance
from pyface.api import FileDialog

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.processing.analysis import NonDBAnalysis

class FileSelector(Loggable):
    records = List
    num_records = Property(depends_on='records')
    limit = Int
    id_string = Str('')

    mass_spectrometers = Tuple(('Spectrometers',))
    analysis_types = Tuple(('Analysis Types'))

    queries = List

    def open_file(self, p=None):
#         p = '/Users/ross/Documents/william_smith2013/fc-2whopper.xls'
        p = '/Users/ross/Documents/william_smith2013/tray_comparison_with_cocktail.xls'
#         p = '/Users/ross/Sandbox/import_template.xls'
        if p is None:
            dlg = FileDialog(action='open')
            if dlg.open():
                p = dlg.path

        if p:

            self._open_xls(p)

            tol = 50
            if len(p) > tol:
                p = '...{}'.format(p[-tol:])

            self.id_string = 'File: {}'.format(p)

    def _open_xls(self, path):
        import xlrd
        wb = xlrd.open_workbook(path)
        for si in range(wb.nsheets):
            sheet = wb.sheet_by_index(0)
            self._load_xls_sheet(sheet)

    def _get_column_idx(self, names, header):
        if not isinstance(names, (list, tuple)):
            names = (names,)

        for attr in names:
            for ai in (attr, attr.lower(), attr.upper()):
                if ai in header:
                    return header.index(ai)

    def _load_xls_sheet(self, sheet, header_offset=1):
        header = sheet.row_values(0)
        record_idx = self._get_column_idx('RunID', header)

        records = []
        groupid = 0
        graphid = 0
        for ri in range(sheet.nrows - header_offset):
            ri += header_offset
            rid = sheet.cell_value(ri, record_idx)
            rid = str(rid).strip()
            if rid in ('<group>', ''):
                groupid += 1
            elif rid in ('<graph>', ''):
                graphid += 1
            else:
                rec = self._make_xls_analysis(sheet.row_values(ri), header)
                rec.group_id = groupid
                rec.graph_id = graphid

                records.append(rec)

        self.records = records

    def _make_xls_analysis(self, rs, header):
        an = NonDBAnalysis()

        names = 'Age'
        age_idx = self._get_column_idx(names, header)

        names = 'Age_Error'
        error_idx = self._get_column_idx(names, header)
        an.age = (rs[age_idx], rs[error_idx])

        names = 'Status'
        idx = self._get_column_idx(names, header)
        an.status = int(rs[idx])

        names = 'RunID'
        idx = self._get_column_idx(names, header)
        v = rs[idx]
        if isinstance(v, float):
            v = int(v)
        an.record_id = str(v)



        return an

    def _get_num_records(self):
        return 'Number Results: {}'.format(len(self.records))

class DataSelector(Loggable):

    database_selector = Any
    file_selector = Instance(FileSelector)

    selector = Any
#     selectors = List
    kind = Enum('Database', 'File')
#     kind = Str('Database', enter_set=True, auto_set=False)
    open_button = Button('open')

    def _kind_changed(self):
        if self.kind == 'Database':
            self.selector = self.database_selector
        else:
            self.selector = self.file_selector
        self.selector.id_string = ''

    def _open_button_fired(self):
        selector = self.selector
        selector.open_file()

    def _selector_default(self):
        return self.database_selector

    def _file_selector_default(self):
        return FileSelector()

#     def _selectors_default(self):
#         return [self.database_selector, self.file_selector]

#     def __getattr__(self, attr):
#         print attr
#         if hasattr(self.selector, attr):
#             return getattr(self.selector, attr)


#============= EOF =============================================
