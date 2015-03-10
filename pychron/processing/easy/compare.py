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

# ============= enthought library imports =======================
import os

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import unique_path
from pychron.core.helpers.formatting import calc_percent_error
from pychron.core.helpers.iterfuncs import partition
from pychron.paths import paths
from pychron.processing.argon_calculations import calculate_isochron
from pychron.processing.easy.base_easy import BaseEasy
from pychron.processing.tasks.figures.editors.isochron_editor import InverseIsochronEditor


class CompareIsochronSpec(BaseEasy):
    def _make(self, ep):
        opt = ep.doc(0)
        db = self.db
        with db.session_ctx():
            ids = opt['identifiers']
            progress = self.open_progress(n=len(ids), close_at_end=False)

            editor = InverseIsochronEditor(processor=self)
            editor.plotter_options_manager.set_plotter_options('Default')
            p, _ = unique_path(os.path.join(paths.dissertation, 'data', 'minnabluff'),
                               'compare_iso_spec')
            wfile = open(p, 'w')
            for i in ids:

                hist = db.get_interpreted_age_histories((i,))[-1]

                li = db.get_labnumber(i)
                ans = self._get_analyses(li)
                if ans:
                    progress.change_message('Calculating isochron for {}'.format(i))

                    unks = self.make_analyses(ans,
                                              use_progress=False,
                                              use_cache=False)
                    age, reg, _ = calculate_isochron(unks)
                    # print self._calculate_intercept(reg)
                    iaage = hist.interpreted_age.age
                    iaerr = hist.interpreted_age.age_err

                    ii, ee = self._calculate_intercept(reg)
                    ee2 = 2 * ee * (reg.mswd ** 0.5 if reg.mswd > 1 else 1)
                    comp = 'EQ'
                    if ii - ee2 > 295.5:
                        comp = 'GT'
                    elif ii + ee2 < 295.5:
                        comp = 'LT'
                    t0 = 'Identifier:        {}'.format(li.identifier)
                    t00 = 'Sample:            {}'.format(li.sample.name)
                    t1 = 'InterpretedAge:    {}+/-{}'.format(iaage, iaerr)
                    t2 = 'IsochronAge:       {}'.format(age)
                    t3 = 'Dev:               {} ({:0.2f}%)'.format(age - iaage, (age - iaage) / iaage * 100)
                    t4 = 'TrappedComponent:  {:0.2f}+/-{:0.3f}'.format(ii, ee)
                    t5 = 'TrappedComparison: {}'.format(comp)
                    t = '\n'.join((t0, t00, t1, t2, t3, t4, t5))
                    # print t
                    wfile.write(t + '\n---\n')
                    # editor.set_items(unks)
                    # editor.rebuild()
                    # print editor.get_trapped_component()
            wfile.close()
            progress.close()

    def _calculate_intercept(self, reg):
        intercept = reg.predict(0)
        err = reg.get_intercept_error()

        inv_intercept = intercept ** -1
        p = calc_percent_error(intercept, err, scale=1)

        err = inv_intercept * p
        return inv_intercept, err

    def _get_analyses(self, li):
        #filter invalid analyses
        ans = filter(lambda x: not x.tag == 'invalid', li.analyses)

        #group by stepheat vs fusion
        pred = lambda x: bool(x.step)

        ans = sorted(ans, key=pred)
        stepheat, fusion = map(list, partition(ans, pred))
        return stepheat

# ============= EOF =============================================

