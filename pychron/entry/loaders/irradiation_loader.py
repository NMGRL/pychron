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
from traits.api import Any, Instance, List, Dict
# ============= standard library imports ========================
import os
from xlrd.sheet import ctype_text

# ============= local library imports  ==========================
from pychron.core.helpers.filetools import to_bool
from pychron.loggable import Loggable
from pychron.managers.data_managers.xls_data_manager import XLSDataManager


NAME = ('Name', 'irradiation', 'irrad')
PR = ('ProductionRatio', 'PR', 'Production Ratios', 'ProductionRatios', 'Production Ratio')
LEVEL = ('Level', 'Tray')
HOLDER = ('Holder', )


class XLSIrradiationLoader(Loggable):
    # columns = ('position', 'sample', 'material', 'weight', 'project', 'level', 'note')
    db = Any
    progress = Any
    canvas = Any
    dm = Instance(XLSDataManager)

    # configuation attributes
    autogenerate_labnumber = False
    base_irradiation_offset = 0
    base_level_offset = 0
    quiet = False

    # when adding a new level bump identifier by irradiation_offset+level_offset
    # if offset is zero bump by 1
    irradiation_offset = 0
    level_offset = 0

    _added_levels = List
    _added_irradiations = List
    _added_positions = List
    _added_chronologies = List

    _user_confirmation = Dict
    def open(self, p):
        self.dm = self._dm_factory(p)
        self.load_configuration()

    def load_configuration(self):
        dm = self.dm
        sheet = dm.get_sheet(('Configuration', 4))
        for ri in dm.iterrows(sheet, 1):
            name = ri[0].value
            v = ri[1].value
            if name == 'autogenerate_labnumber':
                v = to_bool(v)

            self.debug('setting "{}"={}'.format(name, v))
            if not hasattr(self, name):
                self.warning('Invalid configuration option "{}"'.format(name))
            else:
                setattr(self, name, v)

    def load_irradiation(self, p, dry_run=True):
        if not os.path.isfile(p):
            self.warning('{} does not exist'.format(p))
            return

        self.info('loading irradiation file. {}'.format(p))
        self.info('dry= {}'.format(dry_run))
        try:
            with self.db.session_ctx(commit=not dry_run):
                self._load_irradiation_from_file(p, dry_run)
                return True
        except BaseException, e:
            print e

    def identifier_generator(self):
        """
        make a new generator after each irradiation+set of levels.



        :return: generator
        """

        def func():
            self.update_offsets()
            offset = max(1, self.irradiation_offset + self.level_offset)
            db = self.db

            idn = 0
            if db:
                with db.session_ctx():
                    # get the greatest identifier
                    idn = db.get_greatest_identifier()

            i = 0
            while 1:
                yield idn + i + offset
                i += 1

        return func()

    def update_offsets(self):
        io = self.nadded_irradiations * self.base_irradiation_offset
        lo = self.nadded_levels * self.base_level_offset
        self.irradiation_offset = io
        self.level_offset = lo
        return io, lo

    def add_position(self, pdict, dry=False):
        db = self.db
        with db.session_ctx(commit=not dry):
            self._add_position(pdict)

    def add_irradiation(self, name, chronology=None, dry=False):
        db = self.db
        with db.session_ctx(commit=not dry):
            self._add_irradiation(name, chronology)

    def add_irradiation_level(self, irrad, name, holder, pr, dry=False, add_positions=True):
        db = self.db
        with db.session_ctx(commit=not dry):
            self._add_level(irrad, name, holder, pr, add_positions=add_positions)

    def make_template(self, p):
        from pychron.entry.loaders.irradiation_template import IrradiationTemplate

        i = IrradiationTemplate()
        i.make_template(p)

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
    def nadded_irradiations(self):
        return len(self._added_irradiations)

    @property
    def nadded_levels(self):
        return len(self._added_levels)-1

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

    def sheet_identifier_generator(self, sheet):
        pass

    def add_positions(self, irradiation=None, level=None):

        dm = self.dm
        sheet = dm.get_sheet(('Positions', 2))
        idxdict = self._get_idx_dict(sheet, ('position', 'sample', 'material', 'weight',
                                             'irradiation',
                                             'project', 'level', 'note'))

        if self.autogenerate_labnumber:
            gen = self.identifier_generator()
        else:
            idn_idx = dm.get_column_idx(('labnumber', 'identifier'), sheet=sheet, optional=True)

        for row in dm.iterrows(sheet, 1):
            irrad = row[idxdict['irradiation']].value
            lv = row[idxdict['level']].value
            if (irradiation is None and level is None) or irrad == irradiation and lv == level:
                pos = int(row[idxdict['position']].value)

                idn = None
                if self.autogenerate_labnumber:
                    idn = gen.next()
                else:
                    if idn_idx is not None:
                        idn = row[idn_idx].value

                d = {'irradiation': irrad, 'level': lv, 'position': pos,
                     'identifier': idn}

                for ai in ('sample', 'material', 'weight', 'note', 'project'):
                    d[ai] = row[idxdict[ai]].value
                # d = {'irradiation': irrad, 'level': lv, 'position': pos,
                # 'identifier': gen.next(), 'sample':sample, 'project':''}
                self._add_position(d)

    def add_irradiations(self, dry_run=False):
        """
            calls _add_irradiation
                  _add_chronology
                  _add_level - >
        :return:
        """
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
            self._added_levels = []
            for i, row in enumerate(igen):
                irrad = row[nameidx].value
                if i == 0:
                    chron = self._add_chronology(irrad)
                    self._add_irradiation(irrad, chron)
                    if not dry_run and self.db:
                        self.db.commit()

                self._add_level(irrad, row[levelidx].value,
                                row[pridx].value, row[holderidx].value)

    def _load_irradiation_from_file(self, p, dry_run):
        """

        :param p: abs path to xls file
        :return:
        """

        self.dm = self._dm_factory(p)
        self.add_irradiations(dry_run)
        # self.add_positions()
        # self.set_identifiers()

    def _add_chronology(self, irrad):
        dm = self.dm
        sheet = dm.get_sheet(('Chronologies', 1))

        idx_d = self._get_idx_dict(sheet, ('name', 'start', 'end', 'power'))

        def get_row_value(idx_d):
            def func(row, key):
                return row[idx_d[key]].value

            return func

        gv = get_row_value(idx_d)

        chronblob = []
        for row in dm.iterrows(sheet):
            if not gv(row, 'name') == irrad:
                continue

            sd, ed, power = gv(row, 'start'), gv(row, 'end'), gv(row, 'power')
            sd = dm.strftime(sd, '%Y-%m-%d %H:%M:%S')
            ed = dm.strftime(ed, '%Y-%m-%d %H:%M:%S')
            dose = '{}|{}%{}'.format(power, sd, ed)
            chronblob.append(dose)
            self._added_chronologies.append((irrad, sd, ed, power))

        if self.db:
            return self.db.add_irradiation_chronology('$'.join(chronblob))

    def _add_position(self, pdict):
        irrad, level, pos = pdict['irradiation'], pdict['level'], pdict['position']
        db = self.db
        if db:
            with db.session_ctx():
                labnumber = pdict['identifier']
                if labnumber is not None:
                    dbprj = self._add_project(db, pdict['project'])
                    if dbprj:
                        dbmat = self._add_material(db, pdict['material'])
                        if dbmat:
                            dbsam = self._add_sample(db, pdict['sample'], dbprj, dbmat)
                            if dbsam:
                                db.add_labnumber(labnumber, dbsam)

            if db.add_irradiation_position(pos, labnumber, irrad, level):
                self._added_positions.append((irrad, level, pos))

        else:
            self._added_positions.append((irrad, level, pos))

    def _add_project(self, db, prj):
        return self._user_confirm_add(db,prj, 'project')

    def _add_material(self,db, mat):
        return self._user_confirm_add(db, mat, 'material')

    def _add_sample(self, db, sam, dbprj, dbmat):
        def func(v):
            db.add_sample(v, dbprj, dbmat)

        return self._user_confirm_add(db, sam, 'sample', adder=func)

    def _user_confirm_add(self, db, v, key, adder=None):
        if adder is None:
            adder = getattr(db, 'add_{}'.format(key))

        if not self.quiet:
            obj = getattr(db, 'get_{}'.format(key))(v)
            if not obj:
                try:
                    ret = self._user_confirmation[key]
                except KeyError:
                    ret = self.confirmation_dialog('{} "{}" not in database. Do you want to add it.\n'
                                                   'If "No" a labnumber will not be '
                                                   'generated fro this position'.format(key.capitalize(), v))
                rem = self.confirmation_dialog('Remember decision?')
                if rem:
                    self._user_confirmation[key] = ret

                if ret:
                    obj = adder(v)
                    # dbprj = db.add_project(v)
        else:
            obj = adder(v)
            # dbprj = db.add_project(v)

        return obj

    def _add_level(self, irrad, name, pr, holder, add_positions=True):
        db = self.db
        if db:
            with db.session_ctx():
                if db.add_irradiation_level(name, irrad, holder, pr):
                    self._added_levels.append((irrad, name, pr, holder))
                    if add_positions:
                        self.add_positions(irrad, name)
        else:
            self._added_levels.append((irrad, name, pr, holder))

    def _add_irradiation(self, name, chron):
        db = self.db
        if db:
            with db.session_ctx():
                if db.add_irradiation(name, chron):
                    self._added_irradiations.append(name)
        else:
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
        # dm =self.dm
        # if not dm:
        # raise AttributeError
        #
        # sheet = self.dm.get_sheet(('Irradiations',0))
        # idx = dm.get_column_idx('Name', sheet=sheet)
        # lidx = dm.get_column_idx('Levels', sheet=sheet)
        # for ri, ni in enumerate(sheet.col(idx)):
        # if ni.value==irradname:
        # level_str = sheet.cell(ri, lidx)
        # ps = parse_level_str(level_str.value)
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