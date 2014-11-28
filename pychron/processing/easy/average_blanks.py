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

#============= enthought library imports =======================

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.regression.mean_regressor import WeightedMeanRegressor
from pychron.experiment.utilities.identifier import make_runid
from pychron.processing.easy.base_easy import BaseEasy


class EasyAverageBlanks(BaseEasy):
    def _make(self, ep):
        project = 'Minna Bluff'
        db = self.db
        with db.session_ctx():
            prj = db.get_project(project)
            Ar40, Ar39, Ar38, Ar37, Ar36 = [], [], [], [], []
            for dev in (('Eurotherm', 'Furnace'), ('CO2')):
                for si in prj.samples:
                    for li in si.labnumbers:
                        self.debug('blanks for {},{}'.format(si.name, li.identifier))
                        for ai in li.analyses:
                            if ai.extraction.extraction_device.name in dev:
                                bs = self._extract_blanks(ai)
                                if bs is not None:
                                    r = make_runid(li.identifier, ai.aliquot, ai.step)
                                    # self.debug('blanks for {} {}'.format(r,bs))
                                    Ar40.append(bs[0])
                                    Ar39.append(bs[1])
                                    Ar38.append(bs[2])
                                    Ar37.append(bs[3])
                                    Ar36.append(bs[4])

                reg = WeightedMeanRegressor()
                print 'blanks for {}'.format(dev)
                for iso in (Ar40, Ar39, Ar38, Ar37, Ar36):
                    ys, es = zip(*iso)

                    reg.trait_set(ys=ys, yserr=es)
                    print reg.predict()

    def _extract_blanks(self, meas_analysis):
        if meas_analysis.selected_histories:
            history = meas_analysis.selected_histories.selected_blanks
            # keys = isodict.keys()
            keys = ['Ar40', 'Ar39', 'Ar38', 'Ar37', 'Ar36']
            okeys = ['Ar40', 'Ar39', 'Ar38', 'Ar37', 'Ar36']
            blanks = [(0, 0), (0, 0), (0, 0), (0, 0), (0, 0)]
            if history:
                for ba in history.blanks:
                    isok = ba.isotope

                    if isok in keys:
                        blanks[okeys.index(isok)] = (ba.user_value,
                                                     ba.user_error)

                        keys.remove(isok)
                        if not keys:
                            break
            return blanks

# ============= EOF =============================================

