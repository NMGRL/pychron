# ===============================================================================
# Copyright 2014 Jake Ross
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
from pychron.core.ui import set_qt

set_qt()

# ============= enthought library imports =======================
# ============= standard library imports ========================
import csv
import os
import yaml
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import unique_path
from pychron.database.isotope_database_manager import IsotopeDatabaseManager
from pychron.paths import paths
from pychron.pychron_constants import ARGON_KEYS


class RawExporter(IsotopeDatabaseManager):
    def export_csv(self):
        ans = self._get_analyses('export_apis')
        ans = self.make_analyses(ans, unpack=True)
        root = os.path.join(paths.data_dir, 'apis')
        p, _ = unique_path(root, 'data', extension='.csv')
        with open(p, 'w') as wfile:
            writer = csv.writer(wfile)
            for ai in ans:
                self._write_analysis(ai, writer)

    def _write_analysis(self, ai, writer):
        writer.writerow([ai.record_id, ai.sample])
        writer.writerow(['time'] + list(ARGON_KEYS))
        for data in self._gen_rows(ai, 'sniff'):
            writer.writerow(data)

        writer.writerow([])

        for data in self._gen_rows(ai, 'signal'):
            writer.writerow(data)
        writer.writerow([])

    def _gen_rows(self, ai, kind):
        def get_iso(isok, kind):
            if kind == 'sniff':
                return ai.isotopes[isok].sniff
            else:
                return ai.isotopes[isok]

        d = {}
        for isok in ARGON_KEYS:
            ys = ai.isotopes[isok].baseline.ys
            iso = get_iso(isok, kind)
            d[isok] = iso.ys - ys.mean()

        def gen():
            xs = get_iso('Ar40', kind).xs

            for i, xi in enumerate(xs):
                data = [xi]
                for isok in ARGON_KEYS:
                    data.append(d[isok][i])
                yield data

        return gen()

    def _get_analyses(self, name):
        p = os.path.join(paths.data_dir, 'apis', '{}.yaml'.format(name))
        with open(p, 'r') as rfile:
            yd = yaml.load(rfile)

        def gen():
            db = self.db
            with db.session_ctx():
                for yi in yd:
                    args = yi.split('-')
                    ln, al = '-'.join(args[:-1]), args[-1]
                    ai = db.get_unique_analysis(ln, al)
                    print ai, ln, al
                    yield ai

        return gen()


# ============= EOF =============================================

