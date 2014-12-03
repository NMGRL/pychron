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
from pyface.action.menu_manager import MenuManager
from traits.api import List, Property, Int, HasTraits

# ============= standard library imports ========================
# ============= local library imports  ==========================

# ============= EOF =============================================
from traitsui.menu import Action
from traitsui.tabular_adapter import TabularAdapter


class ConfigurableAdapterMixin(HasTraits):
    all_columns = List
    all_columns_dict = Property

    def _get_all_columns_dict(self):
        return dict(self.all_columns)


class BrowserAdapter(TabularAdapter, ConfigurableAdapterMixin):
    font = 'arial 10'

    def get_tooltip(self, obj, trait, row, column):
        name = self.column_map[column]
        # name='_'.join(name.split('_')[:-1])
        return '{}= {}'.format(name, getattr(self.item, name))


class ProjectAdapter(BrowserAdapter):
    columns = [('Name', 'name')]

    def get_menu(self, obj, trait, row, column):
        return MenuManager(Action(name='Unselect', action='unselect_projects'))


class SampleAdapter(BrowserAdapter):
    columns = [('Sample', 'name'),
               ('Material', 'material'),
               ('Project', 'project')]

    all_columns = [('Sample', 'name'),
                   ('Material', 'material'),
                   ('Project', 'project')]
    #     material_text = Property
    odd_bg_color = 'lightgray'

    name_width = Int(125)
    labnumber_width = Int(60)
    material_width = Int(75)


class LabnumberAdapter(BrowserAdapter):
    columns = [('Sample', 'name'),
               ('Identifier', 'labnumber'),
               ('Material', 'material')]
    all_columns = [('Sample', 'name'),
                   ('Identifier', 'labnumber'),
                   ('Material', 'material'),
                   ('Project', 'project'),
                   ('Irradiation', 'irradiation'),
                   ('Level', 'irradiation_and_level'),
                   ('Irrad. Pos.', 'irradiation_pos')]
    #     material_text = Property
    odd_bg_color = 'lightgray'

    name_width = Int(125)
    labnumber_width = Int(60)
    material_width = Int(75)

    def get_menu(self, obj, trait, row, column):
        from pychron.processing.tasks.figures.figure_task import FigureTask

        if obj.selected_samples:
            psenabled = isinstance(obj, FigureTask)
            return MenuManager(Action(name='Unselect', action='unselect_samples'),
                               Action(name='Time View', action='on_time_view'),
                               Action(name='Plot Selected (Grouped)',
                                      enabled=psenabled,
                                      action='plot_selected_grouped'),
                               Action(name='Plot Selected',
                                      enabled=psenabled,
                                      action='plot_selected'))