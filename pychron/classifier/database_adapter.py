# ===============================================================================
# Copyright 2022 ross
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
from apptools.preferences.preference_binding import bind_preference

from pychron.classifier.orm import ArgonIntelligenceTbl
from pychron.dvc.dvc_database import DVCDatabase
from pychron.dvc.dvc_orm import AnalysisTbl
from pychron.dvc.tasks.dvc_preferences import DVCConnectionItem


class ArgonIntelligenceDatabase(DVCDatabase):
    def __init__(self, bind=True, *args, **kw):
        super(ArgonIntelligenceDatabase, self).__init__(*args, **kw)
        if bind:
            self.bind_preferences()

    def bind_preferences(self):
        # prefid = "pychron.dvc.connection"
        # bind_preference(self, "favorites", "{}.favorites".format(prefid))
        # self._favorites_changed(self.favorites)
        favorites = eval(
            self.application.preferences.get("pychron.dvc.connection.favorites")
        )
        ds = [DVCConnectionItem(attrs=f, load_names=False) for f in favorites]
        data_source = next((d for d in ds if d.default and d.enabled), None)
        self.host = data_source.host
        self.kind = data_source.kind
        self.password = data_source.password
        self.username = data_source.username
        self.name = data_source.dbname

    def get_classification(self, analysis, isotope):
        iso = isotope
        if isinstance(iso, str):
            iso = analysis.get_isotope(isotope)
            if iso is None:
                iso = analysis.get_isotope(detector=isotope)

        if iso:
            with self.session_ctx() as sess:
                q = sess.query(ArgonIntelligenceTbl)
                q = q.join(AnalysisTbl)
                q = q.filter(
                    AnalysisTbl.uuid == analysis.uuid
                    and ArgonIntelligenceTbl.isotope == iso.name
                )
                return self._query_one(q, verbose_query=False)

    def add_classification(self, analysis, isotope, class_=None):
        self.debug(
            f"add classification: {analysis.uuid}, {analysis.record_id}, {isotope}"
        )
        with self.session_ctx() as sess:
            iso = isotope
            if isinstance(iso, str):
                iso = analysis.get_isotope(isotope)
                if iso is None:
                    iso = analysis.get_isotope(detector=isotope)

            if iso:
                co = self.get_classification(analysis, iso)
                if co is None:
                    dbanalysis = self.get_analysis_uuid(analysis.uuid)
                    obj = ArgonIntelligenceTbl(
                        analysisID=dbanalysis.id,
                        class_=class_ or iso.class_,
                        isotope=iso.name,
                    )

                    self.add_item(obj)
                else:
                    co.class_ = class_ or iso.class_
                    sess.flush()
                    sess.commit()
            else:
                self.warning(f"failed to located isotope {isotope}")


# ============= EOF =============================================
