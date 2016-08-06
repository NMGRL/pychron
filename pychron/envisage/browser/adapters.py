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
from traits.api import Int, Property, Str
from traitsui.menu import Action
from traitsui.tabular_adapter import TabularAdapter

from pychron.core.configurable_tabular_adapter import ConfigurableMixin
from pychron.envisage.resources import icon


class BrowserAdapter(TabularAdapter, ConfigurableMixin):
    font = 'arial 10'

    def get_tooltip(self, obj, trait, row, column):
        name = self.column_map[column]
        # name='_'.join(name.split('_')[:-1])
        item = getattr(obj, trait)[row]

        return '{}= {}'.format(name, getattr(self.item, name))


class ProjectAdapter(BrowserAdapter):
    columns = [('Name', 'name')]

    def get_menu(self, obj, trait, row, column):
        return MenuManager(Action(name='Unselect', action='unselect_projects'))


class SampleAdapter(BrowserAdapter):
    columns = [('Sample', 'name'),
               ('Material', 'material'),
               ('Project', 'project'),
               ]

    all_columns = [('Sample', 'name'),
                   ('Material', 'material'),
                   ('Project', 'project'),
                   ('Note', 'note')]
    #     material_text = Property
    odd_bg_color = 'lightgray'

    name_width = Int(125)
    labnumber_width = Int(60)
    material_width = Int(75)


class SampleImageAdapter(BrowserAdapter):
    columns = [('Sample', 'name'),
               ('Identifier', 'identifier'),
               ('Material', 'material'),
               ('Project', 'project')]


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
        if obj.selected_samples:
            # psenabled = obj.current_task_name in ('Ideogram', 'Spectrum')
            # psenabled = isinstance(obj, FigureTask)
            return MenuManager(Action(name='Unselect', action='unselect_samples'),
                               # Action(name='Chronological View', action='on_chrono_view'),
                               Action(name='Configure', action='configure_sample_table'), )
            # Action(name='Plot Selected (Grouped)',
            #        enabled=psenabled,
            #        action='plot_selected_grouped'),
            # Action(name='Plot Selected',
            #        enabled=psenabled,
            #        action='plot_selected'))


REVIEW_STATUS_ICONS = {'Default': icon('gray_ball'),
                       'Intermediate': icon('orange_ball'),
                       'All': icon('green_ball')}


class AnalysisAdapter(BrowserAdapter):
    all_columns = [('Review', 'review_status'),
                   ('Run ID', 'record_id'),
                   ('Tag', 'tag'),
                   ('RunDate', 'rundate'),
                   ('Dt', 'delta_time'),
                   # ('Iso Fits', 'iso_fit_status'),
                   # ('Blank', 'blank_fit_status'),
                   # ('IC', 'ic_fit_status'),
                   # ('Flux', 'flux_fit_status'),
                   ('Spec.', 'mass_spectrometer'),
                   ('Meas.', 'meas_script_name'),
                   ('Ext.', 'extract_script_name'),
                   ('EVal.', 'extract_value'),
                   ('Cleanup', 'cleanup'),
                   ('Dur', 'duration'),
                   ('Device', 'extract_device'),
                   ('Comment', 'comment')]

    columns = [('Run ID', 'record_id'),
               ('Tag', 'tag'),
               ('Dt', 'delta_time')]

    review_status_width = Int(50)
    review_status_image = Property
    review_status_text = Str('')
    rundate_width = Int(125)
    delta_time_width = Int(65)
    delta_time_text = Property
    record_id_width = Int(70)
    tag_width = Int(65)
    odd_bg_color = 'lightgray'
    font = 'arial 10'

    def _get_review_status_image(self):
        s = self.item.review_status
        return REVIEW_STATUS_ICONS.get(s)

    def _get_delta_time_text(self):
        dt = self.item.delta_time
        if dt > 60:
            units = '(h)'
            dt /= 60.
            if dt > 24:
                units = '(d)'
                dt /= 24.
        else:
            units = ''
        return '{:0.1f} {}'.format(dt, units)

    def get_menu(self, obj, trait, row, column):
        e = obj.append_replace_enabled
        actions = [Action(name='Configure', action='configure_analysis_table'),
                   Action(name='Unselect', action='unselect_analyses'),
                   # Action(name='Replace', action='replace_items', enabled=e),
                   # Action(name='Append', action='append_items', enabled=e),
                   Action(name='Open', action='recall_items'),
                   Action(name='Review Status Details', action='review_status_details')
                   # Action(name='Open Copy', action='recall_copies'),
                   # Action(name='Find References', action='find_refs')
                   ]

        return MenuManager(*actions)

    def get_bg_color(self, obj, trait, row, column=0):
        color = 'white'
        item = getattr(obj, trait)[row]

        if item.delta_time > 1440:  # 24 hours
            color = '#76C1E2'
        elif row % 2:
            color = 'lightgray'
        return color


class InterpretedAgeAdapter(TabularAdapter):
    columns = [('Identifier', 'identifier'),
               ('Name', 'name')]

    font = 'arial 10'
    name_width = 100
    identifier_width = 100

# ============= EOF =============================================
