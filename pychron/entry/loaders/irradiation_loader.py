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
from traits.api import Any, Instance, List
# ============= standard library imports ========================
import os
from xlrd.sheet import ctype_text

# ============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.managers.data_managers.xls_data_manager import XLSDataManager


NAME = ('Name', 'irradiation', 'irrad')
PR = ('ProductionRatio', 'PR', 'Production Ratios', 'ProductionRatios', 'Production Ratio')
LEVEL = ('Level', 'Tray')
HOLDER = ('Holder', )


class XLSIrradiationLoader(Loggable):
    columns = ('position', 'sample', 'material', 'weight', 'project', 'level', 'note')
    db = Any
    progress = Any
    canvas = Any
    dm = Instance(XLSDataManager)

    _added_levels = List
    _added_irradiations = List
    _added_positions = List
    _added_chronologies = List

    def iterate_irradiations(self, start=1):
        """
        usage

        for igen in self.iterate_irradiations:
            for irow in igen:
                self._add_level(row)

        :return: a generator of generators
        """
        dm = self.dm
        sheet = dm.get_sheet(('Irradiations', 0))
        nameidx = dm.get_column_idx(NAME, sheet)

        def func(s):
            prev = None
            for i, ri in enumerate(dm.iterrows(sheet, s)):
                if not prev:
                    prev = ri[nameidx].value

                if ctype_text[ri[0].ctype] == 'empty' \
                        or prev != ri[nameidx].value:
                    prev = ri[nameidx].value
                    # print s, i
                    yield dm.iterrows(sheet, s, s + i)
                    s = i

            yield dm.iterrows(sheet, s + 1)

        return func(start)

    @property
    def added_irradiations(self):
        return self._added_irradiations

    @property
    def added_levels(self):
        return self._added_levels

    @property
    def added_positions(self):
        return self._added_positions

    @property
    def added_chronologies(self):
        return self._added_chronologies

    def add_positions(self):
        dm = self.dm
        sheet = dm.get_sheet(('Positions', 2))
        # nameidx = dm.get_column_idx(NAME, sheet)
        # levelidx = dm.get_column_idx(LEVEL, sheet)
        idxdict = self._get_idx_dict(sheet, ('position', 'sample', 'material', 'weight',
                                             'irradiation',
                                             'project', 'level', 'note'))
        for row in dm.iterrows(sheet, 1):
            self._add_position(row, idxdict)

    def add_irradiations(self):
        self._added_irradiations = []
        self._added_levels = []
        self._added_positions = []
        self._added_chronologies = []

        dm = self.dm
        sheet = dm.get_sheet(('Irradiations', 0))

        nameidx = dm.get_column_idx(NAME, sheet)
        pridx = dm.get_column_idx(PR, sheet)
        levelidx = dm.get_column_idx(LEVEL, sheet)
        holderidx = dm.get_column_idx(HOLDER, sheet)
        for igen in self.iterate_irradiations():
            for i, row in enumerate(igen):
                irrad = row[nameidx].value
                if i == 0:
                    self._add_irradiation(irrad)
                    self._add_chronology(irrad)

                self._add_level(irrad, row[levelidx].value,
                                row[pridx].value, row[holderidx].value)

    def open(self, p):
        self.dm = self._dm_factory(p)

    def load_irradiation(self, p, dry_run=False):
        with self.db.session_ctx(commit=not dry_run):
            self._load_irradiation_from_file(p)

    def load_level(self, p, positions, irradiation, level):
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

    # def _get_idxs(self, dm, sheet):
    # idxs = {}
    #     for i in self.columns:
    #         idx = dm.get_column_idx(i, sheet=sheet)
    #         if idx is None:
    #             return
    #
    #         idxs[i] = idx
    #     return idxs
    def _load_irradiation_from_file(self, p):
        """

        :param p: abs path to xls file
        :return:
        """
        if not os.path.isfile(p):
            return

        self.dm = self._dm_factory(p)
        self.add_irradiations()
        self.add_positions()

    def _add_chronology(self, irrad):
        dm = self.dm
        sheet = dm.get_sheet(('Chronology', 1))

        idx_d = self._get_idx_dict(sheet, ('name', 'start', 'end', 'power'))

        def get_row_value(idx_d):
            def func(row, key):
                return row[idx_d[key]].value

            return func

        gv = get_row_value(idx_d)

        for row in dm.iterrows(sheet):
            if not gv(row, 'name') == irrad:
                continue

            sd, ed = gv(row, 'start'), gv(row, 'end')
            sd = dm.strftime(sd, '%Y-%m-%d %H:%M:%S')
            ed = dm.strftime(ed, '%Y-%m-%d %H:%M:%S')
            self._added_chronologies.append((irrad, sd, ed, gv(row, 'power')))

    def _add_position(self, row, idxs):
        irrad = row[idxs['irradiation']].value
        level = row[idxs['level']].value
        pos = int(row[idxs['position']].value)
        self._added_positions.append((irrad, level, pos))

    def _add_level(self, irrad, name, pr, holder):
        self._added_levels.append((irrad, name, pr, holder))

    def _add_irradiation(self, name):
        self._added_irradiations.append(name)

    def _get_idx_dict(self, sheet, columns):
        dm = self.dm
        idx_d = {}
        for i in columns:
            idx_d[i] = dm.get_column_idx(i, sheet)
        return idx_d

    def _get_position(self, pid, positions):
        pid = int(pid)
        ir = next((p for p in positions if int(p.hole) == pid), None)
        cr = None
        if ir:
            cr = self.canvas.scene.get_item(pid)
        return ir, cr

    def _dm_factory(self, p):
        dm = XLSDataManager()
        dm.open(p)
        return dm

        # ============= EOF =============================================
        # def get_nlevels(self, irradname):
        #     dm =self.dm
        #     if not dm:
        #         raise AttributeError
        #
        #     sheet = self.dm.get_sheet(('Irradiations',0))
        #     idx = dm.get_column_idx('Name', sheet=sheet)
        #     lidx = dm.get_column_idx('Levels', sheet=sheet)
        #     for ri, ni in enumerate(sheet.col(idx)):
        #         if ni.value==irradname:
        #             level_str = sheet.cell(ri, lidx)
        #             ps = parse_level_str(level_str.value)
        #             return len(ps) if ps else 0
        # def iterate_irradiations2(self):
        #         dm = self.dm
        #         sheet = dm.get_sheet(('Irradiations', 0))
        #
        #         irrads=[]
        #         rows = []
        #         for ri in dm.iterrows(sheet):
        #             # for ji in dm.iterrows(sheet):
        #             if ctype_text[ri[1].ctype]=='empty':
        #                 irrads.append(rows)
        #                 rows=[]
        #             else:
        #                 rows.append(ri)
        #
        #         if rows:
        #             irrads.append(rows)
        #         return irrads
        #
        #

        # def _load_level_from_file(self, p, positions, irradiation, level):
        #         """
        #             use an xls file to enter irradiation positions
        #
        #             looks for sheet named "IrradiationLoading"
        #                 if not present use 0th sheet
        #         """
        #
        #         # dm = XLSDataManager()
        #         # dm.open(p)
        #         dm = self._dm_factory(p)
        #
        #         header_offset = 1
        #         sheet = dm.get_sheet(('IrradiationLoading', 0))
        #         idxs = self._get_idxs(dm, sheet)
        #
        #         if not idxs:
        #             return
        #
        #         rows = [ri for ri in range(sheet.nrows - header_offset)
        #                 if sheet.cell_value(ri + header_offset, idxs['level']) == level]
        #
        #         prog = self.progress
        #         if prog:
        #             prog.max = len(rows) - 1
        #
        #         for ri in rows:
        #             ri += header_offset
        #
        #             project, material = None, None
        #             sample = sheet.cell_value(ri, idxs['sample'])
        #             if sample.lower() == 'monitor':
        #                 sample = self.monitor_name
        #
        #             if sample:
        #                 #is this a sample in the database
        #                 dbsam = self.db.get_sample(sample)
        #                 if dbsam:
        #                     if dbsam.project:
        #                         project = dbsam.project.name
        #                     if dbsam.material:
        #                         material = dbsam.material.name
        #
        #             if project is None:
        #                 project = sheet.cell_value(ri, idxs['project'])
        #             if material is None:
        #                 material = sheet.cell_value(ri, idxs['material'])
        #
        #             pos = sheet.cell_value(ri, idxs['position'])
        #
        #             weight = sheet.cell_value(ri, idxs['weight'])
        #             note = sheet.cell_value(ri, idxs['note'])
        #
        #             if prog:
        #                 prog.change_message('Importing {}'.format(pos))
        #                 prog.increment()
        #
        #             ir_pos, canvas_pos = self._get_position(pos, positions)
        #             if ir_pos:
        #                 ir_pos.trait_set(weight=weight,
        #                                  project=project,
        #                                  material=material,
        #                                  sample=sample,
        #                                  note=note)
        #                 if sample:
        #                     canvas_pos.fill = True
        #             else:
        #                 msg = 'Invalid position for this tray {}'.format(ir_pos)
        #                 #self.warning_dialog()
        #                 self.warning(msg)