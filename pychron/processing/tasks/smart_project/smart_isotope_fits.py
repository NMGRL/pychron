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

#============= enthought library imports =======================
from pychron.processing.tasks.smart_project.base_smarter import BaseSmarter
#============= standard library imports ========================
#============= local library imports  ==========================

class SmartIsotopeFits(BaseSmarter):
    def fit_date_range(self, start, end, atypes, dry_run):
        with self.processor.db.session_ctx():
            ans = self._get_analysis_date_range(start, end, atypes)
            print ans
            if ans:
#             for i, ai in enumerate(ans):
#                 print i, ai.measurement.analysis_type.name
                self._refit_analyses(ans, dry_run)
            else:
                self.debug('not analyses found matching criteria \
                            start:{} end:{} analysis_types:{}'.format(start, end, atypes))

    def fit_irradiations(self, irradiations, projects, dry_run):
        db = self.processor.db
        for irrad, levels in irradiations:
            for level in levels:
                self.info('extracting positions from {} {}'.format(irrad, level))
                with db.session_ctx() as sess:
                    level = db.get_irradiation_level(irrad, level)
                    for pi in level.positions:
                        ln = pi.labnumber
                        sample = ln.sample
                        if sample.project.name in projects:
                            self.info('extracting analyses from {}'.format(ln.identifier))
                            self._refit_analyses(ln.analyses, dry_run)

    def _refit_analyses(self, ans, dry_run):
        for ai in ans:
            if ai.status == 0:
                try:
                    self.processor.refit_isotopes(ai)
                except Exception:
                    import traceback
                    traceback.print_exc()
                    ai.status = 10

        db = self.processor.db
        if not dry_run:
            msg = 'changes committed'
            db.sess.commit()
#             db.commit()
        else:
            msg = 'dry run- not changes committed'
            db.sess.rollback()
#             db.rollback()

        self.info(msg)
# ============= EOF =============================================
