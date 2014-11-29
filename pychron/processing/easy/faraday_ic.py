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

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.processing.easy.base_easy import BaseEasy


class EasyFaradayIC(BaseEasy):
    def _make(self, ep, *args, **kw):
        project = 'Minna Bluff'
        v, e = 116.0954, 0

        db = self.db
        with db.session_ctx():
            prj = db.get_project(project)
            for si in prj.samples:
                for li in si.labnumbers:
                    for ai in li.analyses:
                        for iso in ai.isotopes:
                            if iso.kind == 'signal':
                                if iso.detector and \
                                                iso.detector.name == 'Faraday':
                                    self.debug('set ic for {}'.format(si.name,
                                                                      li.identifier,
                                                                      iso.molecular_weight.name))
                                    self._set_ic(ai, iso.detector, v, e)

    def _set_ic(self, analysis, det, v, e):
        db = self.db
        history = db.add_detector_intercalibration_history(analysis)
        #         db.flush()
        dbdet = db.get_detector(det)
        if dbdet is None:
            self.warning_dialog('Could not find Detector database entry for {}'.format(det))
            return

        dets = ['Faraday']
        # copy previous intercalibrations for other detectors
        phist = analysis.selected_histories.selected_detector_intercalibration
        if phist is not None:
            for ics in phist.detector_intercalibrations:
                if not ics.detector == dbdet and ics.detector.name not in dets:
                    db.add_detector_intercalibration(history, ics.detector,
                                                     user_value=ics.user_value,
                                                     user_error=ics.user_error,
                                                     sets=ics.sets,
                                                     fit=ics.fit)

        db.add_detector_intercalibration(history, dbdet,
                                         user_value=v, user_error=e)
        analysis.selected_histories.selected_detector_intercalibration = history


# ============= EOF =============================================
