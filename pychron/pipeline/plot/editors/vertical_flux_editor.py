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

# ============= standard library imports ========================
import json
import os
from operator import attrgetter

from traits.api import Str, List, HasTraits, Int, Float
# ============= enthought library imports =======================
from traitsui.api import View, UItem, TabularEditor, HSplit
from traitsui.tabular_adapter import TabularAdapter
from uncertainties import nominal_value, std_dev

from pychron.core.helpers.iterfuncs import groupby_key
from pychron.core.utils import alpha_to_int
from pychron.paths import paths
from pychron.pipeline.plot.editors.figure_editor import FigureEditor
from pychron.pipeline.plot.models.vertical_flux_model import VerticalFluxModel
from pychron.processing.flux import mean_j
from pychron.pychron_constants import PLUSMINUS_ONE_SIGMA, SEM, MSEM


# ============= local library imports  ==========================


class VerticalFluxTabularAdapter(TabularAdapter):
    columns = [('Level', 'level'), ('J', 'j'),
               (PLUSMINUS_ONE_SIGMA, 'j_err'), ('Height', 'z')]


class VerticalFluxItem(HasTraits):
    level = Str
    position = Int
    j = Float
    j_err = Float
    z = Float


class VerticalFluxEditor(FigureEditor):
    figure_model_klass = VerticalFluxModel
    irradiation = Str
    levels = List

    def _populate_zs(self, d, level):
        p = os.path.join(paths.meta_root, self.irradiation, '{}.json'.format(level))
        with open(p, 'r') as rfile:
            obj = json.load(rfile)

        d[level] = obj.get('z', alpha_to_int(level))

    def set_items(self, items, as_analyses=False):
        nitems = []
        if as_analyses:

            use_weights = True
            error_kind = MSEM
            monitor_age = 28.201e6

            zs = {}
            items = [i for i in items if not i.is_omitted()]
            for ip, ans in groupby_key(items, key=attrgetter('identifier')):
                ans = list(ans)
                ref = ans[0]
                j, mswd = mean_j(ans, use_weights, error_kind, monitor_age, ref.lambda_k)

                level = ref.irradiation_level
                try:
                    z = zs[level]
                except KeyError:
                    self._populate_zs(zs, level)
                    z = zs[level]

                vi = VerticalFluxItem(j=nominal_value(j), j_err=std_dev(j),
                                      level=level,
                                      position=ref.irradiation_position,
                                      z=z)
                nitems.append(vi)
        else:
            for i, level in enumerate(items):
                p = os.path.join(paths.meta_root, self.irradiation, '{}.json'.format(level))
                with open(p, 'r') as rfile:
                    obj = json.load(rfile)

                    positions = obj['positions']
                    d = next((o for o in positions if o['position'] == 1), None)
                    if d:
                        vi = VerticalFluxItem(level=level, position=1,
                                              j=d['mean_j'],
                                              j_err=d['mean_j_err'],
                                              z=obj['z'])
                        nitems.append(vi)

        self.items = nitems

    def _figure_model_factory(self):
        model = self.figure_model
        if model is None:
            model = self.figure_model_klass()
            self.figure_model = model

        model.trait_set(plot_options=self.plotter_options,
                        irradiation=self.irradiation,
                        items=self.items)
        return model

    def _set_name(self):
        pass

    def traits_view(self):
        g = self.get_component_view()
        g.width = 0.75

        v = View(HSplit(g,
                        UItem('items',
                              width=0.25,
                              editor=TabularEditor(adapter=VerticalFluxTabularAdapter()))),
                 resizable=True)
        return v
# ============= EOF =============================================
