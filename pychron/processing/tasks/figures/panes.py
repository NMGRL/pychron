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
from traits.api import Any, Property
from traitsui.api import View, UItem, InstanceEditor, TabularEditor, VGroup, HGroup, spring, Spring
from pyface.tasks.traits_dock_pane import TraitsDockPane
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.envisage.icon_button_editor import icon_button_editor


class FigureAdapter(TabularAdapter):
    columns = [('Name', 'name'), ('Project', 'project'),
               ('Samples', 'samples'), ('Kind', 'kind')]
    samples_text = Property

    font = 'arial 10'

    def _get_samples_text(self):
        return ', '.join(self.item.samples)


class FigureSelectorPane(TraitsDockPane):
    id = 'pychron.processing.figures.saved_figures'
    name = 'Saved Figures'

    def traits_view(self):
        v = View(VGroup(
            HGroup(CustomLabel('figures_help', color='maroon'), spring,
                   icon_button_editor('delete_figure_button', 'database_delete',
                                      enabled_when='selected_figures'),
                   Spring(width=-10, springy=False),
                   UItem('figure_kind'),
                   ),
            UItem('figures', editor=TabularEditor(adapter=FigureAdapter(),
                                                  editable=False,
                                                  multi_select=True,
                                                  selected='selected_figures',
                                                  dclicked='dclicked_figure'))))
        return v


class PlotterOptionsPane(TraitsDockPane):
    """
        Pane for displaying the active editor's plotter options manager
    """
    id = 'pychron.processing.figures.plotter_options'

    name = 'Figure Options'
    pom = Any

    def traits_view(self):
        v = View(UItem('pom',
                       editor=InstanceEditor(),
                       style='custom'))
        return v

# ============= EOF =============================================
