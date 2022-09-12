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
import csv

from apptools.preferences.preference_binding import bind_preference
from sqlalchemy import and_

from pychron.classifier.orm import ArgonIntelligenceTbl
from pychron.dvc.dvc_database import DVCDatabase
from pychron.dvc.dvc_orm import AnalysisTbl
from pychron.dvc.tasks.dvc_preferences import DVCConnectionItem
from pychron.experiment.utilities.identifier import strip_runid
from pychron.paths import paths
from pychron.pychron_constants import ARGON_KEYS


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

    def get_isotopes(self):
        with self.session_ctx() as sess:
            q = sess.query(ArgonIntelligenceTbl)
            q = q.join(AnalysisTbl)
            return self._query_all(q)

    def get_isotope(self, analysis, isotope):
        iso = isotope
        name = iso
        klass = None
        if isinstance(iso, str) and not isinstance(analysis, AnalysisTbl):
            try:
                iso = analysis.get_isotope(isotope)
                if iso is None:
                    iso = analysis.get_isotope(detector=isotope)
                iso = iso.name
                klass = iso.klass
            except AttributeError:
                self.debug_exception()

        return iso, name, klass

    def get_classification(self, analysis, isotope):
        iso, name, klass = self.get_isotope(analysis, isotope)

        if iso:
            with self.session_ctx() as sess:
                q = sess.query(ArgonIntelligenceTbl)
                q = q.join(AnalysisTbl)
                q = q.filter(
                    and_(
                        AnalysisTbl.uuid == analysis.uuid,
                        ArgonIntelligenceTbl.isotope == iso,
                    )
                )
                return self._query_one(q, verbose_query=False)

    def add_classification(self, analysis, isotope, klass=None):
        if isinstance(analysis, str):
            # analysis is a runid
            l, a, s = strip_runid(analysis)
            analysis = self.get_analysis_runid(l, a, s)

        self.debug(
            f"add classification: {analysis.uuid}, {analysis.record_id}, {isotope}"
        )
        with self.session_ctx() as sess:
            iso, name, isoklass = self.get_isotope(analysis, isotope)
            if isoklass:
                klass = isoklass
            # if isinstance(iso, str):
            #     try:
            #         iso = analysis.get_isotope(isotope)
            #         if iso is None:
            #             iso = analysis.get_isotope(detector=isotope)
            #
            #         klass = iso.klass
            #         name = iso.name
            #     except AttributeError:
            #         self.debug_exception()

            if iso:
                co = self.get_classification(analysis, iso)
                if co is None:
                    dbanalysis = self.get_analysis_uuid(analysis.uuid)
                    obj = ArgonIntelligenceTbl(
                        analysisID=dbanalysis.id,
                        klass=klass,
                        isotope=name,
                    )

                    self.add_item(obj)
                else:
                    co.klass = klass
                    sess.flush()
                    sess.commit()
            else:
                self.warning(f"failed to located isotope {isotope}")

    def upload_file(self, p):
        with open(p, "r") as rfile:
            reader = csv.DictReader(rfile)
            for row in reader:

                for k in ARGON_KEYS:
                    klass = int(k not in ("Ar40", "Ar36"))
                    self.add_classification(row["runid"], k, klass)


if __name__ == "__main__":
    from pychron.core.helpers.logger_setup import logging_setup

    paths.build("~/PychronDev")
    logging_setup("argonintel")

    d = ArgonIntelligenceDatabase(bind=False)
    d.host = "129.138.12.160"
    d.name = "pychrondvc"
    d.username = "jross"
    d.password = "argon4039"
    d.kind = "mysql"

    # d.upload_file('./example_upload2.csv')

# ============= EOF =============================================
