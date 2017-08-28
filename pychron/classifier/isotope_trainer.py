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
from traits.api import Instance, Button, Str
from traitsui.api import View, UItem, HGroup, VGroup
from traitsui.handler import Handler

from pychron.classifier.isotope_classifier import IsotopeClassifier
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.graph.stacked_regression_graph import StackedRegressionGraph
from pychron.loggable import Loggable

UUIDS = (

)


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
    graph = Instance(StackedRegressionGraph)
    good_button = Button
    bad_button = Button
    skip_button = Button
    test = Button
    klass = None
    dvc = Instance('pychron.dvc.dvc.DVC')
    pklass = Str

    def setup_graph(self, iso):
        self.klass = None
        self.pklass = str(self.clf.predict_isotope(iso))

        g = StackedRegressionGraph()
        g.new_plot(padding=[60, 10, 10, 40])
        if iso:
            g.new_series(iso.xs, iso.ys,
                         fit=iso.fit,
                         filter_outliers_dict=iso.filter_outliers_dict)
            g.set_x_limits(min_=0, max_=iso.xs[-1] * 1.1)
            g.set_y_title(iso.name)

        g.set_x_title('Time (s)')

        g.refresh()
        self.graph = g

    def train(self):
        # dvc = DVC(bind=False,
        #           organization='NMGRLData')
        # dvc.db.trait_set(name='pychrondvc',
        #                  username=os.environ.get('ARGONSERVER_DB_USER'),
        #                  password=os.environ.get('ARGONSERVER_DB_PWD'),
        #                  kind='mysql',
        #                  host=os.environ.get('ARGONSERVER_HOST'))
        # dvc.connect()
        self.clf =clf= IsotopeClassifier()
        isos = []
        klasses = []
        uuids = UUIDS
        dvc = self.dvc
        with dvc.session_ctx():
            ans = dvc.get_last_nhours_analyses(200, mass_spectrometers='jan')
            if ans:
                records = [ri for ai in ans for ri in ai.record_views]

                for ai in self.dvc.make_analyses(records):
                    broke = False
                    # dbai = dvc.get_analysis_uuid(uuid)
                    # ai = dvc.make_analyses((dbai,))[0]
                    # ai = dvc.make_analysis(dbai.record_view)
                    ai.load_raw_data()
                    for iso in ai.isotopes.values():

                        klass = self._get_klass(iso)
                        if klass is -1:
                            continue

                        if klass is not None:
                            isos.append(iso)
                            klasses.append(klass)
                        else:
                            broke = True
                            break

                    if broke:
                        break

        if isos:

            clf.add_isotopes(isos, klasses)
            clf.dump()

    def _get_klass(self, iso):
        self.setup_graph(iso)
        bgrp = HGroup(UItem('good_button'), UItem('bad_button'), UItem('skip_button'), UItem('pklass'))
        self.edit_traits(view=View(VGroup(bgrp, UItem('graph', style='custom')),
                                   buttons=['Cancel', 'OK']),
                         kind='livemodal',
                         handler=KlassHandler())
        return self.klass

    # def _test_fired(self):
    #     # self._get_klass(None)
    #     self.train()


if __name__ == '__main__':
    t = IsotopeTrainer()
    t.configure_traits(view=View('test'))

# ============= EOF =============================================
