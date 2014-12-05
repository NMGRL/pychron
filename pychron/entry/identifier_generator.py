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
from traits.api import Any, Float, Str, List, Bool

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.loggable import Loggable


class IdentifierGenerator(Loggable):
    db = Any
    # default_j = Float(1e-4)
    # default_j_err = Float(1e-7)

    monitor_name = Str

    irradiation_positions = List
    irradiation = Str
    level = Str
    is_preview = Bool
    overwrite = Bool

    def preview(self, prog, positions, irradiation, level):
        self.irradiation_positions = positions
        self.irradiation = irradiation
        self.level = level
        self.is_preview = True

        self.generate_identifiers(prog)

    def generate_identifiers(self, *args, **kw):
        db = self.db
        with db.session_ctx(commit=True):
            self._generate_labnumbers(*args)

    def _generate_labnumbers(self, prog, offset=1, level_offset=10000):
        """
            get last labnumber

            start numbering at 1+offset

            add level_offset between each level
        """
        irradiation = self.irradiation

        mongen, unkgen, n = self._position_generator(offset, level_offset)

        if n:
            prog.max = n - 1
            for gen in (mongen, unkgen):
                for pos, ident in gen:
                    po = pos.position
                    le = pos.level.name
                    if self.is_preview:
                        self._set_position_identifier(pos, ident)
                    else:
                        pos.labnumber.identifier = ident

                    # self._add_default_flux(pos)
                    msg = 'setting irrad. pos. {} {}-{} labnumber={}'.format(irradiation, le, po, ident)
                    self.info(msg)
                    if prog:
                        prog.change_message(msg)
            prog.close()

    def _set_position_identifier(self, dbpos, ident):
        if self.is_preview:
            ipos =self._get_irradiated_position(dbpos)
            if ipos:
                ipos.labnumber = str(ident)

    def _get_irradiated_position(self, dbpos):
        if dbpos.level.name == self.level:
            ipos = next((po for po in self.irradiation_positions
                         if po.hole ==dbpos.position), None)
            return ipos

    # def _add_default_flux(self, pos):
    #     db = self.db
    #     j, j_err = self.default_j, self.default_j_err
    #     dbln = pos.labnumber
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
        last_mon_ln = db.get_last_labnumber(self.monitor_name)
        if last_mon_ln:
            last_mon_ln = int(last_mon_ln.identifier)
        else:
            last_mon_ln = 0

        last_unk_ln = db.get_last_labnumber()
        if last_unk_ln:
            last_unk_ln = int(last_unk_ln.identifier)
        else:
            last_unk_ln = 0

        irrad = db.get_irradiation(irradiation)
        levels = irrad.levels
        overwrite = self.overwrite
        args = (irradiation, levels, overwrite, offset, level_offset)
        mons = self._identifier_generator(last_mon_ln, True, *args)
        unks = self._identifier_generator(last_unk_ln, False, *args)
        n = sum([len([p for p in li.positions
                      if overwrite or (p.labnumber.sample and not p.labnumber.identifier)]) for li in levels])

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

                if not r:
                    try:
                        r = x.labnumber.sample.name == self.monitor_name
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

            try:
                r = x.labnumber.sample.name == self.monitor_name
            except AttributeError, e:
                pass

            return r

        test = monkey(not is_monitor)
        for level in levels:
            i = 0
            for position in level.positions:
                if not has_sample(position):
                    continue

                if not test(position):
                    continue

                if position.labnumber.identifier and not overwrite:
                    le = '{}{}-{}'.format(irrad.name, position.level.name, position.position)
                    ln = position.labnumber.identifier
                    self.warning('skipping position {} already has labnumber {}'.format(le, ln))
                    continue

                yield position, i + sln
                i += 1

            sln = sln + i + level_offset - 1

# ============= EOF =============================================

