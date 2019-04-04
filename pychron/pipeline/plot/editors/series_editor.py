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
from traits.api import List, Event
from traitsui.api import View, UItem, Group, VSplit
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.editors import TabularEditor
from traitsui.tabular_adapter import TabularAdapter

from pychron.pipeline.plot.editors.figure_editor import FigureEditor
from pychron.pipeline.plot.models.series_model import SeriesModel


class SeriesStatsTabularAdapter(TabularAdapter):
    columns = [('Mean', 'mean'),
               ('StdDev', 'std'),
               ('Mean MSWD', 'mean_mswd'),
               ('Min', 'min'),
               ('Max', 'max'),
               ('Dev.', 'dev'), ]


class SeriesStatistics:
    def __init__(self, reg):
        self._reg = reg

    def __getattr__(self, attr):
        if hasattr(self._reg, attr):
            return getattr(self._reg, attr)


class SeriesEditor(FigureEditor):
    figure_model_klass = SeriesModel
    pickle_path = 'series'
    basename = 'Series'
    statistics = List
    update_needed = Event

    def _get_component_hook(self, model=None):
        if model is None:
            model = self.figure_model

        ss = []
        for p in model.panels:
            g = p.figures[-1].graph
            if self.plotter_options.show_statistics_as_table:
                g.on_trait_change(self._handle_reg, 'regression_results')
                for plot in g.plots:
                    for k, v in plot.plots.items():
                        if k.startswith('fit'):
                            ss.append(SeriesStatistics(v[0].regressor))

            else:
                g.on_trait_change(self._handle_reg, 'regression_results', remove=True)
        self.statistics = ss

    def _handle_reg(self, new):
        self.update_needed = True

    def traits_view(self):
        tblgrp = Group(UItem('statistics',
                             height=100,
                             editor=TabularEditor(adapter=SeriesStatsTabularAdapter(),
                                                  update='update_needed')),
                       visible_when='object.plotter_options.show_statistics_as_table',
                       label='Stats.')

        v = View(VSplit(self.get_component_view(), tblgrp),
                 resizable=True)
        return v

# ============= EOF =============================================
