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
from traits.api import Instance

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.mass_spec.database.massspec_database_adapter import MassSpecDatabaseAdapter
from pychron.loggable import Loggable
from pychron.mass_spec.mass_spec_analysis import MassSpecAnalysis, MassSpecBlank


class MassSpecRecaller(Loggable):
    db = Instance(MassSpecDatabaseAdapter)

    def is_connected(self):
        return self.db.connected

    def connect(self):
        return self.db.connect()

    def find_analysis(self, labnumber, aliquot, step):

        db = self.db
        with db.session_ctx():

            dbrec = db.get_analysis(labnumber, aliquot, step)
            if dbrec:
                # need to handle blanks differently
                # labnumber in mass spec for blanks is -1
                if labnumber == -1:
                    klass = MassSpecBlank
                else:
                    klass = MassSpecAnalysis

                rec = klass()
                rec.sync(dbrec)
                irradpos = db.get_irradiation_position(dbrec.IrradPosition)
                r = irradpos.IrradiationLevel
                n, l = r[:-1], r[-1:]

                dbirrad = db.get_irradiation_level(n, l)

                rec.sync_irradiation(dbirrad)
                for iso in dbrec.isotopes:
                    det = iso.detector
                    c = db.get_baseline_changeable_item(iso.baseline.BslnID)
                    rec.sync_baselines(det.detector_type.Label, c.InfoBlob, c.PDPBlob)

                    c = db.get_pdp(iso.IsotopeID)
                    if c:
                        rec.sync_fn(iso.Label, c.PDPBlob)

                    prefs = db.get_latest_preferences(iso.IsotopeID)

                    riso = rec.isotopes[iso.Label]
                    rec.sync_filtering(riso, prefs)

                    # prefs = db.get_latest_baseline_preferences(iso.baseline.BslnID)
                    # rec.sync_filtering(riso.baseline, prefs)

                return rec

# ============= EOF =============================================
