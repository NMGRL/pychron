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
from pychron.core.helpers.strtools import to_bool
from pychron.loggable import Loggable
from pychron.managers.data_managers.xls_data_manager import XLSDataManager

NAME = ('Name', 'irradiation', 'irrad')
PR = ('ProductionRatio', 'PR', 'Production Ratios', 'ProductionRatios', 'Production Ratio')
LEVEL = ('Level', 'Tray')
HOLDER = ('Holder',)


class XLSIrradiationLoader(Loggable):
    # columns = ('position', 'sample', 'material', 'weight', 'project', 'level', 'note')
    dvc = Instance('pychron.dvc.dvc.DVC')
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

    def open(self, p, load_configuration=True):
        self.dm = self._dm_factory(p)
        if load_configuration:
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

    def load_irradiation(self, p, dry_run=False):
        if not os.path.isfile(p):
            self.warning('{} does not exist'.format(p))
            return

        self.info('loading irradiation file. {}'.format(p))
        self.info('dry= {}'.format(dry_run))
        try:
            with self.db.session_ctx(commit=not dry_run):
                self._load_irradiation_from_file(p, dry_run)

                if not dry_run:
                    self.dvc.meta_commit('imported irradiation file {}'.format(p))
                return True
        except BaseException, e:
            print 'exception', e

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
                yield int(idn + i + offset)
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
                if prev is None:
                    prev = ri[nameidx].value

                if ctype_text[ri[0].ctype] != 'empty' \
                        and prev != ri[nameidx].value:
                    prev = ri[nameidx].value
                    # print 'yeild {},{}'.format(s, s + i)
                    yield dm.iterrows(sheet, s, s + i)
                    s = i + 1

            # print 'yeild2 {}'.format(s)
            yield dm.iterrows(sheet, s)

        return func(start)

    @property
    def nadded_irradiations(self):
        return len(self._added_irradiations)

    @property
    def nadded_levels(self):
        return len(self._added_levels) - 1

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
        self.debug('Adding positions')
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

                d = {'irradiation': irrad, 'level': lv, 'position': pos}

                if idn is not None:
                    d['identifier'] = int(idn)

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
                if i == 0:
                    irrad = row[nameidx].value
                    chron = self._add_chronology(irrad)
                    self._add_irradiation(irrad, chron)

                    if not dry_run and self.db:
                        self.db.commit()

                self._add_level(irrad, row[levelidx].value,
                                row[pridx].value, row[holderidx].value)

    # private
    def _load_irradiation_from_file(self, p, dry_run):
        """

        :param p: abs path to xls file
        :return:
        """

        self.dm = self._dm_factory(p)
        self.add_irradiations(dry_run)
        # if self.autogenerate_labnumber:
        # self._add_labnumbers()

        # self.add_positions()
        # self.set_identifiers()

        # def _add_labnumbers(self):
        # for irrad in self.position_iterator():
        # for level in irrad:
        #         for pos in level:
        #             pass

    def _add_irradiation(self, name, chronology=None):
        dvc = self.dvc
        if dvc:
            if dvc.add_irradiation(name, chronology):
                self._added_irradiations.append(name)
        else:
            self._added_irradiations.append(name)

    def _add_level(self, irrad, name, pr, holder, add_positions=True):
        dvc = self.dvc
        if dvc:
            if self.dvc.add_irradiation_level(name, irrad, holder, pr):
                self._added_levels.append((irrad, name, pr, holder))
                if add_positions:
                    self.add_positions()
        else:
            self._added_levels.append((irrad, name, pr, holder))

    def _add_chronology(self, irrad):
        dm = self.dm
        sheet = dm.get_sheet(('Chronologies', 1))

        idx_d = self._get_idx_dict(sheet, ('name', 'start', 'end', 'power'))

        def get_row_value(idx_d):
            def func(row, key):
                return row[idx_d[key]].value

            return func

        gv = get_row_value(idx_d)

        doses = []
        for row in dm.iterrows(sheet):
            if not gv(row, 'name') == irrad:
                continue

            sd, ed, power = gv(row, 'start'), gv(row, 'end'), gv(row, 'power')
            sd = dm.strftime(sd, '%Y-%m-%d %H:%M:%S')
            ed = dm.strftime(ed, '%Y-%m-%d %H:%M:%S')
            dose = '{}|{}%{}'.format(power, sd, ed)
            doses.append(dose)
            self._added_chronologies.append((irrad, sd, ed, power))

        return doses

    def _add_position(self, pdict):
        irrad, level, pos = pdict['irradiation'], pdict['level'], pdict['position']
        db = self.db
        if db:
            dbip = self.dvc.add_irradiation_position(irrad, level, pos)
            if dbip:
                self._added_positions.append((irrad, level, pos))
                labnumber = pdict.get('identifier', None)

                dbprj = self._add_project(db, pdict['project'])
                if dbprj:
                    dbmat = self._add_material(db, pdict['material'])
                    if dbmat:
                        dbsam = self._add_sample(db, pdict['sample'], dbprj, dbmat)
                        dbip.sample = dbsam

                        if dbsam and labnumber is not None:
                            db.add_labnumber(labnumber, dbsam, irradiation_position=dbip)

        else:
            self._added_positions.append((irrad, level, pos))

    def _add_project(self, db, prj):
        return self._user_confirm_add(db, prj, 'project')

    def _add_material(self, db, mat):
        return self._user_confirm_add(db, mat, 'material')

    def _add_sample(self, db, sam, dbprj, dbmat):
        def func(v):
            return db.add_sample(*v)

        return self._user_confirm_add(db, (sam, dbprj.name, dbmat.name), 'sample', adder=func)

    def _user_confirm_add(self, db, v, key, adder=None):
        if adder is None:
            adder = getattr(db, 'add_{}'.format(key))

        if not self.quiet:
            if isinstance(v, tuple):
                obj = getattr(db, 'get_{}'.format(key))(*v)
            else:
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
        else:
            obj = adder(v)

        db.flush()
        return obj

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
