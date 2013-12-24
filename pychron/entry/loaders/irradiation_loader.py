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
from traits.api import Any

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.managers.data_managers.xls_data_manager import XLSDataManager


class XLSIrradiationLoader(Loggable):
    columns = ('position', 'sample', 'material', 'weight', 'project', 'level', 'note')
    db = Any
    progress = Any
    canvas = Any

    def load(self, p, positions, irradiation, level):
        with self.db.session_ctx():
            self._load_level_from_file(p, positions, irradiation, level)

    def make_template(self, p, n, level):
        import xlwt

        wb = xlwt.Workbook()
        sheet = wb.add_sheet('IrradiationLoading')

        s2 = xlwt.XFStyle()
        borders = xlwt.Borders()
        borders.bottom = 2
        s2.borders = borders

        idx = 1
        for i, c in enumerate(self.columns):
            sheet.write(0, i, c, style=s2)
            if c == 'level':
                idx = i

        for i in range(n):
            i += 1
            sheet.write(i, 0, i)
            sheet.write(i, idx, level)

        wb.save(p)

    def _get_idxs(self, dm, sheet):
        idxs = {}
        for i in self.columns:
            idx = dm.get_column_idx(i, sheet=sheet)
            #print i, idx
            if idx is None:
                return

            idxs[i] = idx
        return idxs

    def _load_level_from_file(self, p, positions, irradiation, level):
        """
            use an xls file to enter irradiation positions

            looks for sheet named "IrradiationLoading"
                if not present use 0th sheet
        """

        dm = XLSDataManager()
        dm.open(p)

        header_offset = 1
        sheet = dm.get_sheet(('IrradiationLoading', 0))
        idxs = self._get_idxs(dm, sheet)

        if not idxs:
            return

        rows = [ri for ri in range(sheet.nrows - header_offset)
                if sheet.cell_value(ri + header_offset, idxs['level']) == level]

        prog = self.progress
        if prog:
            prog.max = len(rows) - 1

        for ri in rows:
            ri += header_offset

            project, material = None, None
            sample = sheet.cell_value(ri, idxs['sample'])
            if sample.lower() == 'monitor':
                sample = self.monitor_name

            if sample:
                #is this a sample in the database
                dbsam = self.db.get_sample(sample)
                if dbsam:
                    if dbsam.project:
                        project = dbsam.project.name
                    if dbsam.material:
                        material = dbsam.material.name

            if project is None:
                project = sheet.cell_value(ri, idxs['project'])
            if material is None:
                material = sheet.cell_value(ri, idxs['material'])

            pos = sheet.cell_value(ri, idxs['position'])

            weight = sheet.cell_value(ri, idxs['weight'])
            note = sheet.cell_value(ri, idxs['note'])

            if prog:
                prog.change_message('Importing {}'.format(pos))
                prog.increment()

            ir_pos, canvas_pos = self._get_position(pos, positions)
            if ir_pos:
                ir_pos.trait_set(weight=weight,
                                 project=project,
                                 material=material,
                                 sample=sample,
                                 note=note,
                )
                if sample:
                    canvas_pos.fill = True
            else:
                msg = 'Invalid position for this tray {}'.format(ir_pos)
                #self.warning_dialog()
                self.warning(msg)


    def _get_position(self, pid, positions):
        pid = int(pid)
        ir = next((p for p in positions if int(p.hole) == pid), None)
        cr = None
        if ir:
            cr = self.canvas.scene.get_item(pid)
        return ir, cr

        #============= EOF =============================================
