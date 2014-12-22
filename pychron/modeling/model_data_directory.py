# ===============================================================================
# Copyright 2011 Jake Ross
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
from traits.api import HasTraits, Bool, List, \
 Property, Str, Any, Color
from traitsui.api import View, Item
# ============= standard library imports ========================
import os
# ============= local library imports  ==========================

# ============= views ===================================

class ModelDataDirectory(HasTraits):
    '''
    '''
    show = Bool
    bind = Bool
    name = Property(depends_on='path')
    path = Str
    id = 0
    modeler = Any
#    primary_color = Str
#    secondary_color = Str
    primary_color = Color
    secondary_color = Color

    model_spectrum_enabled = Bool
    model_arrhenius_enabled = Bool

    inverse_model_spectrum_enabled = Bool
    plots = List

    def traits_view(self):
        v = View(Item('name', style='readonly'),
                 Item('primary_color', style='readonly', label='Primary'),
                 Item('secondary_color', style='readonly', label='Secondary'))
        return v

    def _get_name(self):
        '''
        '''
        return os.path.basename(self.path)

    def _show_changed(self):
        '''
        '''
        if self.modeler:
            for p in self.plots:
                p.visible = self.show

            self.modeler.graph.redraw()

            self.trait_set(
                           model_arrhenius_enabled=self.show,
                           model_spectrum_enabled=self.show,
                           inverse_model_spectrum_enabled=self.show
                           )
            self.modeler.update_graph_title()

    def _model_arrhenius_enabled_changed(self):
        def model_spec_func(modeler):
            plotids = modeler.get_panel_plotids('arrhenius')
            for plotid in plotids:
                p = modeler.graph.plots[plotid]
                plot = p.plots['{}.arr.model'.format(self.name)][0]
                modeler.graph.set_plot_visibility(plot, self.model_arrhenius_enabled)

        self._try(model_spec_func)

        def logr_ro_func(modeler):
            plotids = modeler.get_panel_plotids('logr_ro')
            for plotid in plotids:
                p = modeler.graph.plots[plotid]
                plot = p.plots['{}.logr_ro.model'.format(self.name)][0]
                modeler.graph.set_plot_visibility(plot, self.model_arrhenius_enabled)

        self._try(logr_ro_func)

    def _model_spectrum_enabled_changed(self):
        def ms_func(modeler):
            plotids = modeler.get_panel_plotids('spectrum')
            for plotid in plotids:
                p = modeler.graph.plots[plotid]
                plot = p.plots['{}.spec.model'.format(self.name)][0]
                self.modeler.graph.set_plot_visibility(plot, self.model_spectrum_enabled)
        self._try(ms_func)

    def _inverse_model_spectrum_enabled_changed(self):
        def ims_func(modeler):
            plotids = modeler.get_panel_plotids('spectrum')
            for plotid in plotids:
                p = modeler.graph.plots[plotid]
                for key, plot in p.plots.iteritems():
                    if key.startswith('{}.inverse_spec'.format(self.name)):
                        modeler.graph.set_plot_visibility(plot[0], self.inverse_model_spectrum_enabled)

        self._try(ims_func)

    def _bind_changed(self):
        '''
        '''
        if self.modeler:
            self.modeler.graph.set_group_binding(self.id, self.bind)

#    def update_pcolor(self, new):
#        new = [255 * i for i in new[:2]]
#        c = Color(*new)
#        self.primary_color = ColourDatabase().FindName(c).lower()
# #
#    def update_scolor(self, new):
#        new = [255 * i for i in new]
#        c = Color(*new)
#        self.secondary_color = ColourDatabase().FindName(c).lower()

    def _try(self, func):
        try:
            if self.modeler:
                func(self.modeler)
        except KeyError, e:
            print func.__name__, e
        except Exception, e:
            print func.__name__, e
#    @on_trait_change('primary_color, secondary_color')
#    def _color_changed(self):
#
#
#        try:
#            for k, v in self.modeler.graph.groups.iteritems():
#                if k in ['spectrum', 'logr_ro', 'arrhenius', ]:
#                    v[self.id][0].color = self.primary_color
#                    v[self.id][1].color = self.secondary_color
#                elif k == 'cooling_history':
#                    v[self.id][0].face_color = self.primary_color
#                    v[self.id][0].edge_color = self.primary_color
#
#                    v[self.id][1].face_color = self.secondary_color
#                    v[self.id][1].edge_color = self.secondary_color
#
#        except Exception, err:
#            print err
# ============= EOF ====================================
