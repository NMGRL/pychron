#===============================================================================
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
#===============================================================================
from pychron.core.ui import set_qt

set_qt()

#============= enthought library imports =======================
from traitsui.api import View
from traits.api import Button
#============= standard library imports ========================
import csv
import os
import yaml
from numpy import polyfit
#============= local library imports  ==========================
from pychron.graph.stacked_graph import StackedGraph
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
        with open(p, 'w') as fp:
            writer = csv.writer(fp)
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
        with open(p, 'r') as fp:
            yd = yaml.load(fp)

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


class SniffInspector(RawExporter):
    test = Button

    def traits_view(self):
        v = View('test')
        return v

    def _test_fired(self):
        self.do()

    def do(self):
        ans = self._get_analyses('ratio')
        ans = self.make_analyses(ans, unpack=True)
        g = StackedGraph()

        for ai in ans:
            g.clear()
            for i, (n, d) in enumerate([('Ar40', 'Ar36'), ('Ar40', 'Ar39')]):
                #iterate sniff
                nbs, dbs = ai.get_isotope(n, kind='baseline').ys.mean(), \
                           ai.get_isotope(d, kind='baseline').ys.mean()
                niso, diso = ai.get_isotope(n, kind='sniff'), ai.get_isotope(d, kind='sniff')

                yns, yds = niso.ys - nbs, diso.ys - nbs
                xs = niso.xs
                rs = []
                nn = niso.n
                rxs = []
                for ri in xrange(nn - 1):
                    r = self._calculate_ratio(ri, xs, yns, yds)
                    rxs.append(ri)
                    rs.append(r)

                p = g.new_plot()
                p.value_range.tight_bounds = False
                g.new_series(rxs, rs)
                g.set_x_title('Exclude points')
                g.set_y_title('{}/{}'.format(n, d), plotid=i)

                niso, diso = ai.get_isotope(n), ai.get_isotope(d)
                nys, dys = niso.ys - nbs, diso.ys - dbs
                signal_ratio = self._calculate_ratio(0, niso.xs, nys, dys, fit=2)
                ymi, yma = g.get_y_limits(plotid=i)
                if signal_ratio > yma:
                    g.set_y_limits(ymi, signal_ratio * 1.1, plotid=i)
                elif signal_ratio < ymi:
                    g.set_y_limits(signal_ratio * 0.9, yma, plotid=i)

                g.add_horizontal_rule(signal_ratio, plotid=i)
            g.set_title('{} {}'.format(ai.record_id, ai.sample))
            g.plotcontainer.padding_top = 50
            # g.edit_traits()
            g.plotcontainer.do_layout(size=(600, 900), force=True)
            p, _ = unique_path(os.path.join(paths.data_dir, 'apis'), 'ratio_evo_{}'.format(ai.record_id),
                               extension='.pdf')
            g.save_pdf(p)

    def _calculate_ratio(self, i, xs, yns, yds, fit=1):
        #truncate data
        xs, yns, yds = xs[i:], yns[i:], yds[i:]

        #fit data
        nintercept = polyfit(xs, yns, fit)[-1]
        dintercept = polyfit(xs, yds, fit)[-1]
        return nintercept / dintercept


if __name__ == '__main__':
    e = SniffInspector(bind=False, connect=False)
    e.db.trait_set(name='pychrondata',
                   kind='mysql',
                   username='root',
                   password='DBArgon',
                   host='129.138.12.160')
    e.connect()
    e.configure_traits()
    # e.do()



#============= EOF =============================================

