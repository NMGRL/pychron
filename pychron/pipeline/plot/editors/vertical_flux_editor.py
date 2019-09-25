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

from traits.api import Str, List, HasTraits, Int, Float, Property
# ============= enthought library imports =======================
from traitsui.api import View, UItem, TabularEditor, HSplit, VSplit, Readonly, VGroup, HGroup
from traitsui.tabular_adapter import TabularAdapter
from uncertainties import nominal_value, std_dev

from pychron.core.helpers.formatting import floatfmt
from pychron.core.helpers.iterfuncs import groupby_key
from pychron.core.regression.mean_regressor import WeightedMeanRegressor
from pychron.core.utils import alpha_to_int
from pychron.paths import paths
from pychron.pipeline.plot.editors.figure_editor import FigureEditor
from pychron.pipeline.plot.models.vertical_flux_model import VerticalFluxModel
from pychron.processing.flux import mean_j
from pychron.pychron_constants import PLUSMINUS_ONE_SIGMA, MSEM, DELTA


# ============= local library imports  ==========================

class VerticalFluxTabularAdapter(TabularAdapter):
    columns = [('Level', 'level'),
               ('Position', 'position'),
               ('Identifier', 'identifier'),
               ('Height', 'z'),
               ('J', 'j'),
               (PLUSMINUS_ONE_SIGMA, 'j_err'),
               ('MSWD', 'mswd')
               ]
    level_width = Int(50)
    identifier_width = Int(60)
    position_width = Int(60)
    z_width = Int(60)
    j_width = Int(60)
    j_err_width = Int(60)
    mswd_width = Int(60)

    j_text = Property
    j_err_text = Property
    mswd_text = Property
    font = 'modern 10'

    def _get_mswd_text(self):
        return floatfmt(self.item.mswd, n=2)

    def _get_j_text(self):
        return floatfmt(self.item.j, n=6)

    def _get_j_err_text(self):
        return floatfmt(self.item.j_err, n=8)


class VerticalFluxGroupTabularAdapter(VerticalFluxTabularAdapter):
    columns = [('Level', 'level'),
               ('Z', 'z'),
               ('Mean', 'j'),
               (PLUSMINUS_ONE_SIGMA, 'j_err'),
               ('MSWD', 'mswd'),
               (DELTA, 'delta')]

    delta_text = Property

    def _get_delta_text(self):
        return floatfmt(self.item.delta, n=6)


class VerticalFluxItem(HasTraits):
    level = Str
    position = Int
    identifier = Str
    j = Float
    j_err = Float
    z = Float


class VerticalFluxGroupItem(VerticalFluxItem):
    items = List


class VerticalFluxEditor(FigureEditor):
    figure_model_klass = VerticalFluxModel
    irradiation = Str
    levels = List
    groups = List
    min = Float
    max = Float
    delta = Float
    pdelta = Float

    def _populate_zs(self, d, level):
        p = os.path.join(paths.meta_root, self.irradiation, '{}.json'.format(level))
        with open(p, 'r') as rfile:
            obj = json.load(rfile)

        d[level] = obj.get('z', alpha_to_int(level))

    def set_stats(self):
        js, es = zip(*[(g.j, g.j_err) for g in self.groups])
        reg = WeightedMeanRegressor(ys=js, yserr=es, error_calc_type=MSEM)
        reg.calculate()

        self.min = reg.min
        self.max = reg.max
        self.delta = reg.delta
        self.pdelta = reg.delta / reg.max * 100

    def set_items(self, items, as_analyses=False):
        nitems = []
        if as_analyses:

            use_weights = True
            error_kind = self.plotter_options.error_kind
            lambda_k = self.plotter_options.lambda_k
            monitor_age = None
            if self.plotter_options.use_j:
                monitor_age = self.plotter_options.monitor_age*1e6

            zs = {}
            items = [i for i in items if not i.is_omitted()]
            for ip, ans in groupby_key(items, key=attrgetter('identifier')):
                ans = list(ans)
                ref = ans[0]
                j, mswd = mean_j(ans, use_weights, error_kind, monitor_age, lambda_k)

                level = ref.irradiation_level
                try:
                    z = zs[level]
                except KeyError:
                    self._populate_zs(zs, level)
                    z = zs[level]

                vi = VerticalFluxItem(j=nominal_value(j), j_err=std_dev(j),
                                      level=level,
                                      identifier=ip,
                                      position=ref.irradiation_position,
                                      mswd=mswd,
                                      z=z)
                nitems.append(vi)

            gs = []
            for level, items in groupby_key(nitems, key=attrgetter('level')):
                fs, es, zs = zip(*[(i.j, i.j_err, i.z) for i in items])
                reg = WeightedMeanRegressor(ys=fs, yserr=es, error_calc_type=error_kind)
                reg.calculate()

                gi = VerticalFluxGroupItem(level=level,
                                           j=reg.predict(),
                                           j_err=reg.predict_error(1),
                                           mswd=reg.mswd,
                                           delta=reg.delta,
                                           z=zs[0])
                gs.append(gi)
            self.groups = gs
            self.set_stats()
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
        def freadonly(n, *args, **kw):
            return Readonly(format_str='%0.{}f'.format(n), *args, **kw)

        g = self.get_component_view()
        g.width = 0.65
        items = UItem('items',
                      width=1-g.width,
                      editor=TabularEditor(adapter=VerticalFluxTabularAdapter()))
        groups = VGroup(UItem('groups',
                              width=1-g.width,
                              editor=TabularEditor(adapter=VerticalFluxGroupTabularAdapter())),
                        HGroup(freadonly(6, 'min'),
                               freadonly(6, 'max')),
                        HGroup(freadonly(6,'delta'),
                               freadonly(2, 'pdelta', label='%')))
        v = View(HSplit(g,
                        VSplit(groups, items)))
        return v
# ============= EOF =============================================
