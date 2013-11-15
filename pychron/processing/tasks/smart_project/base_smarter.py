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
from traits.api import Instance
# from traitsui.api import View, Item
#============= standard library imports ========================
from sqlalchemy.sql.expression import and_
#============= local library imports  ==========================
from pychron.loggable import Loggable
# from pychron.database.orms.isotope_orm import meas_AnalysisTable, \
#     meas_MeasurementTable, gen_AnalysisTypeTable
from pychron.database.orms.isotope.gen import gen_AnalysisTypeTable
from pychron.database.orms.isotope.meas import meas_AnalysisTable, meas_MeasurementTable
import time


class BaseSmarter(Loggable):
    processor = Instance('pychron.processing.processor.Processor')

    def _get_analysis_date_range(self, start, end, atypes):
        sess = self.processor.db.sess
        q = sess.query(meas_AnalysisTable)
        q = q.join(meas_MeasurementTable)
        q = q.join(gen_AnalysisTypeTable)


        q = q.filter(and_(meas_AnalysisTable.analysis_timestamp <= end,
                          meas_AnalysisTable.analysis_timestamp >= start,
                          meas_AnalysisTable.status == 0))

#         print atypes
        q = q.filter(gen_AnalysisTypeTable.name.in_(atypes))

        return q.all()

    def _block_analyses(self, n, ans, func, args=None, kw=None):
        if args is None:
            args = tuple()
        if kw is None:
            kw = dict()

        ai = ans.next()
        pt = ai.analysis_timestamp
        g = [ai]
        tol = 60 * 60

        cnt = 0
        acnt = 0
        st = time.time()
        while 1:
            try:
                ai = ans.next()
                dev = ai.analysis_timestamp - pt
                self.debug('{} {} dev: {}'.format(ai.labnumber.identifier,
                                                  ai.analysis_timestamp,
                                                  dev))

                pt = ai.analysis_timestamp
                if dev.total_seconds() > tol:

#                     self._do_fit_blanks(g, fits, 'unknown', root,
#                                         save_figure, with_table)
                    func(g, *args, **kw)

                    et = time.time() - st
                    ed = n * et / float(acnt)
                    er = (ed - et) / 60.

                    p = acnt / float(n) * 100

                    self.debug('new group. completed {}/{} ({:0.2f}) {:0.1f} (min)'.format(acnt, n, p, er))

                    g = [ai]

                    cnt += 1

                else:
                    g.append(ai)
                acnt += 1

            except StopIteration:
                break

            if cnt > 0:
                g = None
                break

        if g:
            func(g, *args, **kw)
#             self._do_fit_blanks(g, fits, 'unknown', root,
#                                 save_figure, with_table)


#============= EOF =============================================
