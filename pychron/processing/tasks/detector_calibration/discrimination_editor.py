# ===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import on_trait_change

from pychron.processing.tasks.analysis_edit.interpolation_editor import InterpolationEditor

# ============= standard library imports ========================
from pychron.core.helpers.isotope_utils import sort_isotopes
# ============= local library imports  ==========================

class DiscriminationEditor(InterpolationEditor):

    @on_trait_change('unknowns[]')
    def _update_unknowns(self):

        '''
            TODO: find reference analyses using the current _unknowns
        '''
        self._make_unknowns()
        self.rebuild_graph()

    def _make_references(self):
        keys = set([ki  for ui in self._references
                        for ki in ui.isotope_keys])
        keys = sort_isotopes(keys)
        if 'Ar40' in keys and 'Ar36' in keys:
            self.tool.load_fits(['Ar40/Ar36'])

    def _rebuild_graph(self):
        pass
#        g = self.graph
#        gen = self._graph_generator()
#
#        rxs = [xi.timestamp for xi in self._references]
#        uxs = [xi.timestamp for xi in self._unknowns]
#        start, end = self._get_start_end(rxs, uxs)
#
#        rxs = self.normalize(rxs, start)
#        uxs = self.normalize(uxs, start)
#
#        set_x_flag = False
#        for fit in gen:
# #            n, d = fit.name.split('/')
#            p = g.new_plot(ytitle=fit.name)
#            p.value_range.tight_bounds = False
#            # plot ref
# #            nys = array([ri.isotopes[n].uvalue for ri in self._references])
# #            dys = array([ri.isotopes[d].uvalue for ri in self._references])
# #            rys = nys / dys
#
# #            rys = [ri.nominal_value for ri in rys]
# #            g.new_series(rxs, rys, fit=fit.fit)
#
# #            uys = array([ri.ic_factor.nominal_value for ri in self._unknowns])
#
#            # plot unknown
# #            g.new_series(uxs, uys, fit=False, type='scatter')
#
#        if set_x_flag:
#            g.set_x_limits(0, end , pad='0.1')
#            g.refresh()


# ============= EOF =============================================
