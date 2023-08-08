# ===============================================================================
# Copyright 2015 Jake Ross
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
from __future__ import absolute_import

import os

from matplotlib.colors import ListedColormap
from numpy import save, load
from sklearn.model_selection import train_test_split
from traits.api import Instance, Button, Str
from traitsui.api import View, UItem, HGroup, VGroup
from traitsui.handler import Handler

from pychron.classifier.database_adapter import ArgonIntelligenceDatabase
from pychron.classifier.isotope_classifier import IsotopeClassifier, make_sample

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.dvc.dvc import DVC
from pychron.graph.stacked_regression_graph import StackedRegressionGraph
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.pychron_constants import ARGON_KEYS

import matplotlib.pyplot as plt
import numpy as np


class KlassHandler(Handler):
    def object_good_button_changed(self, info):
        info.object.klass = 1
        info.ui.dispose()

    def object_bad_button_changed(self, info):
        info.object.klass = 0
        info.ui.dispose()

    def object_skip_button_changed(self, info):
        info.object.klass = -1
        info.ui.dispose()


class IsotopeTrainer(Loggable):
    db = Instance(ArgonIntelligenceDatabase, ())
    dvc = Instance(DVC, ())
    clf = Instance(IsotopeClassifier, ())

    def load(self):
        sp = os.path.join(paths.hidden_dir, "isotope_training_data_samples.npy")
        kp = os.path.join(paths.hidden_dir, "isotope_training_data_klasses.npy")
        if os.path.isfile(sp) and os.path.isfile(kp):
            samples = load(sp)
            klasses = load(kp)
            return samples, klasses

    def train(self):
        self.db.create_session()

        # rs = self.dvc.make_analyses([record.analysis for record in self.db.get_isotopes()])
        # print(rs)

        clf = self.clf
        loaded = self.load()
        if loaded:
            samples, klasses = loaded
        else:
            made = {}
            samples = []
            klasses = []

            for ri in self.db.get_isotopes():
                if ri.analysis.id in made:
                    ai = made[ri.analysis.id]
                else:
                    ai = self.dvc.make_analysis(ri.analysis, pull_frequency=60)
                    made[ri.analysis.id] = ai
                    ai.load_raw_data()

                iso = ai.get_isotope(ri.isotope)
                samples.append(make_sample(iso))
                klasses.append(ri.klass)

            self.dump(samples, "samples")
            self.dump(klasses, "klasses")

        samples_train, samples_test, klasses_train, klasses_test = train_test_split(
            samples, klasses, test_size=0.4, random_state=0
        )

        clf.new_classifier("SVC", kernel="linear", C=1)
        clf.add_training_data(samples_train, klasses_train, load=False)
        scores = clf.cross_val_score(samples_test, klasses_test, cv=5)
        print(scores, scores.mean(), scores.std())

        results = []
        for nn in range(3, 15):
            for weights in ("uniform", "distance"):
                clf.new_classifier("NearestNeighbors", nn, weights=weights)
                clf.add_training_data(samples_train, klasses_train, load=False)
                scores = clf.cross_val_score(samples_test, klasses_test, cv=5)
                args = nn, weights, scores, scores.mean(), scores.std()
                results.append(args)
                # print(nn, weights, scores, scores.mean(), scores.std())

        for r in sorted(results, key=lambda x: x[-2]):
            print(r)

    def dump(self, arr, tag):
        p = os.path.join(paths.hidden_dir, f"isotope_training_data_{tag}.npy")
        save(p, arr)


if __name__ == "__main__":
    from pychron.core.helpers.logger_setup import logging_setup

    paths.build("~/PychronDev")
    logging_setup("argonintel")

    d = IsotopeTrainer()
    d.db = ArgonIntelligenceDatabase(bind=False)
    d.db.host = "129.138.12.160"
    d.db.name = "pychrondvc"
    d.db.username = "jross"
    d.db.password = "argon4039"
    d.db.kind = "mysql"

    d.dvc = DVC(bind=False, meta_repo_name="NMGRLMetaData")
    d.dvc.db.kind = "mysql"
    d.dvc.db.host = "129.138.12.160"
    d.dvc.db.name = "pychrondvc"
    d.dvc.db.username = "jross"
    d.dvc.db.password = "argon4039"
    d.dvc.repository_root = "~/Users/ross/PychronDev/data/.dvc/repositories"

    d.dvc.initialize()
    d.train()

    # graph = Instance(StackedRegressionGraph)
    # good_button = Button
    # bad_button = Button
    # skip_button = Button
    # test = Button
    # klass = None
    # dvc = Instance("pychron.dvc.dvc.DVC")
    # pklass = Str
    #
    # def setup_graph(self, iso):
    #     self.klass = None
    #     self.pklass = str(self.clf.predict_isotope(iso))
    #
    #     g = StackedRegressionGraph()
    #     g.new_plot(padding=[60, 10, 10, 40])
    #     if iso:
    #         g.new_series(
    #             iso.xs,
    #             iso.ys,
    #             fit=iso.fit,
    #             filter_outliers_dict=iso.filter_outliers_dict,
    #         )
    #         g.set_x_limits(min_=0, max_=iso.xs[-1] * 1.1)
    #         g.set_y_title(iso.name)
    #
    #     g.set_x_title("Time (s)")
    #
    #     g.refresh()
    #     self.graph = g
    #
    # def train(self):
    #     # dvc = DVC(bind=False,
    #     #           organization='NMGRLData')
    #     # dvc.db.trait_set(name='pychrondvc',
    #     #                  username=os.environ.get('ARGONSERVER_DB_USER'),
    #     #                  password=os.environ.get('ARGONSERVER_DB_PWD'),
    #     #                  kind='mysql',
    #     #                  host=os.environ.get('ARGONSERVER_HOST'))
    #     # dvc.connect()
    #     self.clf = clf = IsotopeClassifier()
    #     isos = []
    #     klasses = []
    #     uuids = UUIDS
    #     dvc = self.dvc
    #     with dvc.session_ctx():
    #         ans = dvc.get_last_nhours_analyses(200, mass_spectrometers="jan")
    #         if ans:
    #             # records = [ri for ai in ans for ri in ai.record_views]
    #             for ai in self.dvc.make_analyses(ans):
    #                 broke = False
    #                 # dbai = dvc.get_analysis_uuid(uuid)
    #                 # ai = dvc.make_analyses((dbai,))[0]
    #                 # ai = dvc.make_analysis(dbai.record_view)
    #                 ai.load_raw_data()
    #                 for iso in ai.isotopes.values():
    #
    #                     klass = self._get_klass(iso)
    #                     if klass is -1:
    #                         continue
    #
    #                     if klass is not None:
    #                         isos.append(iso)
    #                         klasses.append(klass)
    #                     else:
    #                         broke = True
    #                         break
    #
    #                 if broke:
    #                     break
    #
    #     if isos:
    #         clf.add_isotopes(isos, klasses)
    #         clf.dump()
    #
    # def _get_klass(self, iso):
    #     self.setup_graph(iso)
    #     bgrp = HGroup(
    #         UItem("good_button"),
    #         UItem("bad_button"),
    #         UItem("skip_button"),
    #         UItem("pklass"),
    #     )
    #     self.edit_traits(
    #         view=View(
    #             VGroup(bgrp, UItem("graph", style="custom")), buttons=["Cancel", "OK"]
    #         ),
    #         kind="livemodal",
    #         handler=KlassHandler(),
    #     )
    #     return self.klass
    #
    # # def _test_fired(self):
    # #     # self._get_klass(None)
    # #     self.train()
    #
# if __name__ == "__main__":
#     t = IsotopeTrainer()
#     t.configure_traits(view=View("test"))

# ============= EOF =============================================
