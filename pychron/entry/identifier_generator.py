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
from traits.api import Any, Str, List, Bool, Int, CInt, Instance
from traitsui.api import View
from traitsui.item import Item

from pychron.core.progress import open_progress
from pychron.core.ui.combobox_editor import ComboboxEditor
from pychron.loggable import Loggable
from pychron.persistence_loggable import PersistenceMixin


def get_maxs(lns):
    def func(li):
        try:
            x = int(li)
        except ValueError:
            x = 0
        return x

    lns = map(func, lns)

    return map(max, group_runs(lns))


def group_runs(li, tolerance=1000):
    out = []
    last = li[0]

    for x in li:
        if abs(x - last) > tolerance:
            yield out
            out = []
        out.append(x)
        last = x
    yield out


class IdentifierGenerator(Loggable, PersistenceMixin):
    db = Any
    dvc = Instance('pychron.dvc.dvc.DVC')
    # default_j = Float(1e-4)
    # default_j_err = Float(1e-7)

    monitor_name = Str

    irradiation_positions = List
    irradiation = Str
    level = Str
    is_preview = Bool
    overwrite = Bool

    level_offset = Int(0)
    offset = Int(5)
    mon_start = CInt(5000)
    unk_start = CInt(1000)

    pattributes = ('level_offset', 'offset')
    persistence_path = 'identifier_generator'
    mon_maxs = List
    unk_maxs = List

    def setup(self):
        self.load()
        monlns = self.db.get_last_identifiers(self.monitor_name)
        unklns = self.db.get_last_identifiers(excludes=(self.monitor_name,))

        if monlns:
            self.mon_maxs = get_maxs(monlns)
        if unklns:
            self.unk_maxs = get_maxs(unklns)

        info = self.edit_traits(view=View(Item('offset'), Item('level_offset'),
                                          Item('mon_start', label='Starting Monitor L#',
                                               editor=ComboboxEditor(name='mon_maxs')),
                                          Item('unk_start', label='Starting Unknown L#',
                                               editor=ComboboxEditor(name='unk_maxs')),
                                          kind='livemodal',
                                          title='Configure Identifier Generation',
                                          buttons=['OK', 'Cancel']), )
        if info.result:
            self.dump()
            return True

    def preview(self, positions, irradiation, level):
        self.irradiation_positions = positions
        self.irradiation = irradiation
        self.level = level
        self.is_preview = True

        self.generate_identifiers()

    def generate_identifiers(self, *args, **kw):
        self._generate_labnumbers(*args)

        if not self.is_preview:
            self.dvc.meta_commit('Generate identifiers')

    def _generate_labnumbers(self, offset=None, level_offset=None):
        """
            get last labnumber

            start numbering at 1+offset

            add level_offset between each level
        """
        if offset is None:
            offset = self.offset
        if level_offset is None:
            level_offset = self.level_offset

        irradiation = self.irradiation

        mongen, unkgen, n = self._position_generator(offset, level_offset)

        if n:
            prog = open_progress(n)
            # prog.max = n - 1
            for gen in (mongen, unkgen):
                for pos, ident in gen:
                    po = pos.position
                    le = pos.level.name
                    if self.is_preview:
                        self._set_position_identifier(pos, ident)
                    else:
                        pos.identifier = ident
                        self.dvc.set_identifier(pos.level.irradiation.name,
                                                pos.level.name,
                                                pos.position, ident)

                    # self._add_default_flux(pos)
                    msg = 'setting irrad. pos. {} {}-{} labnumber={}'.format(irradiation, le, po, ident)
                    self.info(msg)
                    if prog:
                        prog.change_message(msg)
            prog.close()

    def _set_position_identifier(self, dbpos, ident):
        ipos = self._get_irradiated_position(dbpos)
        if ipos:
            ident = str(ident)
            ipos.identifier = ident

    def _get_irradiated_position(self, dbpos):
        if dbpos.level.name == self.level:
            ipos = next((po for po in self.irradiation_positions
                         if po.hole == dbpos.position), None)
            return ipos

    # def _add_default_flux(self, pos):
    # db = self.db
    # j, j_err = self.default_j, self.default_j_err
    # dbln = pos.labnumber
    #
    #     def add_flux():
    #         hist = db.add_flux_history(pos)
    #         dbln.selected_flux_history = hist
    #         f = db.add_flux(j, j_err)
    #         f.history = hist
    #
    #     if dbln.selected_flux_history:
    #         tol = 1e-10
    #         flux = dbln.selected_flux_history.flux
    #         if abs(flux.j - j) > tol or abs(flux.j_err - j_err) > tol:
    #             add_flux()
    #     else:
    #         add_flux()

    def _position_generator(self, offset, level_offset):
        """
            return 2 generators
            monitors, unknowns
        """
        db = self.db
        irradiation = self.irradiation
        if not self.mon_start:
            last_mon_ln = db.get_last_identifier(self.monitor_name)
            if last_mon_ln:
                last_mon_ln = int(last_mon_ln.identifier)
            else:
                last_mon_ln = 0
        else:
            last_mon_ln = self.mon_start

        if not self.unk_start:
            last_unk_ln = db.get_last_identifier()
            if last_unk_ln:
                last_unk_ln = int(last_unk_ln.identifier)
            else:
                last_unk_ln = 0
        else:
            last_unk_ln = self.unk_start

        irrad = db.get_irradiation(irradiation)
        levels = irrad.levels
        overwrite = self.overwrite
        args = (irradiation, levels, overwrite, offset, level_offset)
        mons = self._identifier_generator(last_mon_ln, True, *args)
        unks = self._identifier_generator(last_unk_ln, False, *args)
        n = sum([len([p for p in li.positions
                      if overwrite or (p.sample and not p.identifier)]) for li in levels])

        return mons, unks, n

    def _get_position_is_monitor(self, dbpos):
        ipos = self._get_irradiated_position(dbpos)
        if ipos:
            return ipos.sample == self.monitor_name

    def _get_position_sample(self, dbpos):
        ipos = self._get_irradiated_position(dbpos)
        if ipos:
            return ipos.sample

    def _identifier_generator(self, start, is_monitor, irrad, levels, overwrite, offset, level_offset):
        offset = max(1, offset)
        level_offset = max(1, level_offset)
        sln = start + offset

        def monkey(invert=False):
            def _monkey(x):
                r = None
                if self.is_preview:
                    r = self._get_position_is_monitor(x)
                else:
                    if not r:
                        try:
                            r = x.sample.name == self.monitor_name
                        except AttributeError, e:
                            pass

                if invert:
                    r = not r
                return r

            return _monkey

        def has_sample(x):
            r = None
            if self.is_preview:
                r = self._get_position_sample(x)
            else:
                try:
                    r = x.sample.name  # == self.monitor_name
                except AttributeError, e:
                    pass

            return r

        test = monkey(not is_monitor)
        for level in levels:
            i = 0
            for position in sorted(level.positions, key=lambda x: x.position):
                if not has_sample(position):
                    continue

                if not test(position):
                    continue
                if position.identifier and not overwrite:
                    le = '{}{}-{}'.format(irrad, position.level.name, position.position)
                    ln = position.identifier
                    self.warning('skipping position {} already has labnumber {}'.format(le, ln))
                    continue

                yield position, i + sln
                i += 1

            sln = sln + i + level_offset - 1


if __name__ == '__main__':
    lns = [22923126,
           22923083,
           22923066,
           22923051,
           22923045,
           22923034,
           22923016,
           22923001,
           22922001,
           22921003,
           22921002,
           22921001,
           22191022,
           22191021,
           22191020,
           22191019,
           22191018,
           22191017,
           22191016,
           22191015,
           22191014,
           22191013,
           22191012,
           22191011,
           22191010,
           22191009,
           22191008,
           22191007,
           22191006,
           22191005,
           22191004,
           623410,
           623409,
           623408,
           623407,
           623406,
           623404,
           623403,
           623402,
           623401,
           92596,
           92595,
           69156,
           63249,
           63248,
           63247,
           63246,
           63245,
           63244,
           63243,
           63242,
           63241,
           63240,
           63239,
           63238,
           63237,
           63236,
           63235,
           63234,
           63233,
           63232,
           63231,
           63230,
           63229,
           63228,
           63227,
           63225,
           63224,
           63223,
           63222,
           63221,
           63220,
           63219,
           63218,
           63217,
           63216,
           63215,
           63214,
           63213,
           63212,
           63211,
           63210,
           63209,
           63208,
           63207,
           63206,
           63205,
           63204,
           63203,
           63202,
           63201,
           63200,
           63199,
           63198,
           63197,
           63196,
           63195,
           63194,
           63193,
           63192,
           63191,
           63190,
           63189,
           63188,
           63187,
           63186]
    print get_maxs(lns)


# ============= EOF =============================================

