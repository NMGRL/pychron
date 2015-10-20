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

from pychron.paths import paths

paths.build('dev')

# ============= enthought library imports =======================
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change, Instance, Button
from traitsui.api import View, UItem, Item, HGroup, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.handler import Handler
from pychron.dvc.dvc import DVC
from pychron.graph.stacked_regression_graph import StackedRegressionGraph
from pychron.loggable import Loggable


class KlassHandler(Handler):
    def object_good_button_changed(self, info):
        info.object.klass = 1
        info.ui.dispose()

    def object_bad_button_changed(self, info):
        info.object.klass = 0
        info.ui.dispose()


class IsotopeTrainer(Loggable):
    graph = Instance(StackedRegressionGraph)
    good_button = Button
    bad_button = Button
    test = Button
    klass = None

    def setup_graph(self, iso):
        self.is_good = None

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
        dvc = DVC(bind=False)
        ans = dvc.get_analyses_date_range()

        isos = []
        klasses = []

        for dbai in ans:
            ai = dvc.make_analyses((dbai,))
            for iso in ai.isotopes.values():

                klass = self._get_klass(iso)
                if klass is not None:
                    isos.append(iso)
                    klasses.append(klass)

        self.clf.add_isotopes(isos, klasses)

    def _get_klass(self, iso):
        self.setup_graph(iso)
        bgrp = HGroup(UItem('good_button'), UItem('bad_button'))
        self.edit_traits(view=View(VGroup(bgrp, UItem('graph', style='custom')),
                                   buttons=['Cancel']),
                         kind='livemodal',
                         handler=KlassHandler())
        return self.klass

    def _test_fired(self):
        self._get_klass(None)


if __name__ == '__main__':
    t = IsotopeTrainer()
    t.configure_traits(view=View('test'))

# ============= EOF =============================================
