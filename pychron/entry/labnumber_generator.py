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
from traits.api import Any, Float, Str

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.loggable import Loggable


class LabnumberGenerator(Loggable):
    db = Any
    default_j = Float(1e-4)
    default_j_err = Float(1e-7)

    monitor_name = Str

    def generate_labnumbers(self, irradiation, prog, overwrite):
        db = self.db
        with db.session_ctx(commit=True):
            self._generate_labnumbers(irradiation, overwrite, prog)


    def _generate_labnumbers(self, ir, overwrite=False, prog=None, offset=1, level_offset=10000):
        """
            get last labnumber

            start numbering at 1+offset

            add level_offset between each level
        """

        mongen, unkgen = self._labnumber_generator(ir,
                                                   overwrite,
                                                   offset,
                                                   level_offset)
        mongen = list(mongen)
        unkgen = list(unkgen)
        n = len(mongen) + len(unkgen)
        if n:
            prog.max = n - 1
            for gen in (mongen, unkgen):
                for pos, ln in gen:
                    pos.labnumber.identifier = ln

                    le = pos.level.name
                    pi = pos.position
                    self._add_default_flux(pos)
                    msg = 'setting irrad. pos. {} {}-{} labnumber={}'.format(ir, le, pi, ln)
                    self.info(msg)
                    if prog:
                        prog.change_message(msg)

    def _add_default_flux(self, pos):
        db = self.db
        j, j_err = self.default_j, self.default_j_err
        dbln = pos.labnumber

        def add_flux():
            hist = db.add_flux_history(pos)
            dbln.selected_flux_history = hist
            f = db.add_flux(j, j_err)
            f.history = hist

        if dbln.selected_flux_history:
            tol = 1e-10
            flux = dbln.selected_flux_history.flux
            if abs(flux.j - j) > tol or abs(flux.j_err - j_err) > tol:
                add_flux()
        else:
            add_flux()

    def _labnumber_generator(self, irradiation, overwrite, offset, level_offset):
        """
            return 2 generators
            monitors, unknowns
        """
        db = self.db
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

        def monkey(invert=False):
            def _monkey(x):
                r = None
                try:
                    r = x.labnumber.sample.name == self.monitor_name
                except AttributeError, e:
                    pass

                if invert:
                    r = not r
                return r

            return _monkey

        return self._ln_gen(irradiation, levels, last_mon_ln, monkey(), overwrite, offset, level_offset), \
               self._ln_gen(irradiation, levels, last_unk_ln, monkey(True), overwrite, offset, level_offset)

    def _ln_gen(self, irrad, levels, start, key, overwrite, offset, level_offset):
        offset = max(1, offset)
        level_offset = max(1, level_offset)
        sln = start + offset
        for level in levels:
            i = 0
            for position in level.positions:
                if not key(position):
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

