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
from traits.api import Color, Instance, DelegatesTo
from traitsui.api import View, Item, UItem, VGroup, HGroup, spring, \
    EnumEditor, Group, Spring, VFold, Label, InstanceEditor, \
    CheckListEditor, VSplit, TabularEditor, UReadonly
from pyface.tasks.traits_dock_pane import TraitsDockPane
from traitsui.editors import TableEditor
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn
from traitsui.tabular_adapter import TabularAdapter
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.experiment.utilities.identifier import SPECIAL_NAMES
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.pychron_constants import MEASUREMENT_COLOR, EXTRACTION_COLOR, \
    NOT_EXECUTABLE_COLOR, SKIP_COLOR, SUCCESS_COLOR, CANCELED_COLOR, \
    TRUNCATED_COLOR, FAILED_COLOR, END_AFTER_COLOR
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.experiment.plot_panel import PlotPanel


#===============================================================================
# editing
#===============================================================================
def spacer(w):
    return Spring(width=w, springy=False)


class ExperimentFactoryPane(TraitsDockPane):
    id = 'pychron.experiment.factory'
    name = 'Experiment Editor'

    def trait_context(self):
        if self.model:
            return {'object': self.model,
                    'rfac': self.model.run_factory,
                    'qfac': self.model.queue_factory,
                    'pane': self}

    def traits_view(self):
        add_button = icon_button_editor('add_button', 'add',
                                        enabled_when='ok_add',
                                        tooltip='Add run')

        save_button = icon_button_editor('save_button', 'disk',
                                         tooltip='Save queue to file')

        edit_button = icon_button_editor('edit_mode_button', 'table_edit',
                                         enabled_when='edit_enabled',
                                         tooltip='Toggle edit mode')

        clear_button = icon_button_editor('clear_button',
                                          'table_row_delete',
                                          tooltip='Clear all runs added using "frequency"')

        user_grp = HGroup(Item('qfac.username'),
                          Item('qfac.username',
                               editor=EnumEditor(name='qfac.usernames'),
                               width=-25, show_label=False),
                          icon_button_editor('qfac.edit_user', 'database_edit'),
                          Spring(width=-5, springy=False),
                          Item('qfac.use_email_notifier', show_label=False),
                          Item('qfac.email', enabled_when='qfac.use_email_notifier'))

        meta1 = HGroup(
            Item('qfac.mass_spectrometer',
                 show_label=False,
                 editor=EnumEditor(name='qfac.mass_spectrometers')),
            Item('qfac.extract_device',
                 show_label=False,
                 editor=EnumEditor(name='qfac.extract_devices')))

        meta2 = HGroup(Item('qfac.use_queue_conditions'),
                       UItem('qfac.queue_conditions_name',
                             enabled_when='qfac.use_queue_conditions',
                             editor=EnumEditor(name='qfac.available_conditions')))

        queue_grp = VGroup(user_grp, meta1, meta2,
                           Item('qfac.load_name',
                                # show_label=False,
                                editor=EnumEditor(name='qfac.load_names')),
                           Item('qfac.delay_before_analyses'),
                           Item('qfac.delay_between_analyses'))

        button_bar = HGroup(save_button,
                            add_button,
                            clear_button,
                            edit_button,
                            CustomLabel('rfac.edit_mode_label',
                                        color='red',
                                        width=40),
                            spring,
                            Item('rfac.end_after', width=30),
                            Item('rfac.skip'))

        edit_grp = VFold(VGroup(self._get_info_group(),
                                Item('rfac.factory_view',
                                     style='custom',
                                     show_label=False),
                                label='General'),
                         self._get_script_group(),
                         self._get_truncate_group(),
                         enabled_when='qfac.ok_make')

        lower_button_bar = HGroup(add_button,
                                  clear_button,
                                  Label('Auto Increment'),
                                  Item('auto_increment_id', label='L#'),
                                  Item('auto_increment_position', label='Position'))
        v = View(VGroup(queue_grp,
                        button_bar,
                        CustomLabel('rfac.info_label', size=14, color='green'),
                        edit_grp,
                        lower_button_bar),
                 width=225)
        return v

    def _get_info_group(self):
        grp = Group(
            HGroup(
                Item('rfac.selected_irradiation',
                     show_label=False,
                     editor=EnumEditor(name='rfac.irradiations')),
                Item('rfac.selected_level',
                     show_label=False,
                     editor=EnumEditor(name='rfac.levels'))),

            HGroup(Item('rfac.special_labnumber',
                        show_label=False,
                        editor=EnumEditor(values=SPECIAL_NAMES)),
                   Item('rfac.run_block', show_label=False,
                        editor=EnumEditor(name='rfac.run_blocks')),
                   Item('rfac.frequency', width=50),
                   Item('rfac.freq_before', label='Before'),
                   Item('rfac.freq_after', label='After'),
                   spring),
            HGroup(Item('rfac.labnumber',
                        tooltip='Enter a Labnumber',
                        width=100, ),
                   Item('rfac._labnumber', show_label=False,
                        editor=CheckListEditor(name='rfac.labnumbers'),
                        width=-20),
                   Item('rfac.aliquot',
                        width=50),
                   spring),

            HGroup(Item('rfac.flux'),
                   Label(u'\u00b1'),
                   Item('rfac.flux_error', show_label=False),
                   icon_button_editor('rfac.save_flux_button',
                                      'database_save',
                                      tooltip='Save flux to database'),
                   enabled_when='rfac.labnumber'),
            HGroup(
                Item('rfac.weight',
                     label='Weight (mg)',
                     tooltip='(Optional) Enter the weight of the sample in mg. '
                             'Will be saved in Database with analysis'),
                Item('rfac.comment',
                     tooltip='(Optional) Enter a comment for this sample. '
                             'Will be saved in Database with analysis'),
                Item('rfac.auto_fill_comment',
                     show_label=False,
                     tooltip='Auto fill "Comment" with IrradiationLevel:Hole, e.g A:9')),
            show_border=True,
            label='Sample Info')
        return grp

    def _get_truncate_group(self):
        grp = VGroup(
            HGroup(
                Item('rfac.trunc_attr',
                     editor=EnumEditor(name='rfac.trunc_attrs'),
                     show_label=False),
                Item('rfac.trunc_comp', show_label=False),
                Item('rfac.trunc_crit', show_label=False),
                spacer(-10),
                Item('rfac.trunc_start', label='Start Count'),
                icon_button_editor('rfac.clear_truncation',
                                   'delete',
                                   enabled_when='rfac.edit_mode'),
                show_border=True,
                label='Simple'),
            HGroup(
                Item('rfac.truncation_path',
                     editor=EnumEditor(name='rfac.truncations'),
                     label='Path'),

                icon_button_editor('rfac.edit_truncation_button', 'table_edit',
                                   enabled_when='rfac.truncation_path',
                                   tooltip='Edit the selected action file'),
                icon_button_editor('rfac.new_truncation_button', 'table_add',
                                   tooltip='Add a new action file. Duplicated currently selected file if applicable'),
                show_border=True,
                label='File'),
            label='Actions')
        return grp

    def _get_script_group(self):
        script_grp = VGroup(
            Item('rfac.extraction_script', style='custom', show_label=False),
            Item('rfac.measurement_script', style='custom', show_label=False),
            Item('rfac.post_equilibration_script', style='custom', show_label=False),
            Item('rfac.post_measurement_script', style='custom', show_label=False),
            Item('rfac.script_options', style='custom', show_label=False),
            HGroup(spring,
                   Item('rfac.default_fits_button',
                        show_label=False,
                        enabled_when='rfac.default_fits_enabled',
                        label='Default Fits'),
                   Item('rfac.load_defaults_button',
                        tooltip='load the default scripts for this analysis type',
                        show_label=False,
                        enabled_when='rfac.labnumber')),
            show_border=True,
            label='Scripts')
        return script_grp


#===============================================================================
# execution
#===============================================================================
class WaitPane(TraitsDockPane):
    id = 'pychron.experiment.wait'
    name = 'Wait'

    def traits_view(self):
        v = View(
            UItem('wait_group',
                  style='custom'))
        return v


class ConnectionStatusPane(TraitsDockPane):
    id = 'pychron.experiment.connection_status'
    name = 'Connection Status'

    def traits_view(self):
        cols = [ObjectColumn(name='name'),
                CheckboxColumn(name='connected')]
        v = View(UItem('connectables',
                       editor=TableEditor(editable=False,
                                          sortable=False,
                                          columns=cols)))
        return v


class StatsPane(TraitsDockPane):
    id = 'pychron.experiment.stats'
    name = 'Stats'

    def traits_view(self):
        v = View(
            UItem('stats', style='custom'))
        return v


class ControlsPane(TraitsDockPane):
    #     name = 'Controls'
    id = 'pychron.experiment.controls'

    movable = False
    closable = False
    floatable = False

    def traits_view(self):
        cancel_tt = '''Cancel current run and continue to next run'''
        stop_tt = '''Cancel current run and stop queue'''
        start_tt = '''Start current experiment queue. 
Will continue to next opened queue when completed'''
        truncate_tt = '''Stop the current measurement process and continue to 
the next step in the measurement script'''
        truncate_style_tt = '''Normal= measure_iteration stopped at current step
    script continues
Quick=   measure_iteration stopped at current step
    script continues using abbreviated_count_ratio*counts'''
        end_tt = '''Stop the queue and the end of the current run'''

        v = View(
            HGroup(
                spacer(-20),
                icon_button_editor('start_button',
                                   'start',
                                   enabled_when='can_start',
                                   tooltip=start_tt),
                icon_button_editor('stop_button', 'stop',
                                   enabled_when='not can_start',
                                   tooltip=stop_tt),

                spacer(-20),
                Item('end_at_run_completion',
                     label='Stop at Completion',
                     tooltip=end_tt),
                spacer(-20),
                icon_button_editor('cancel_run_button', 'cancel',
                                   enabled_when='can_cancel',
                                   tooltip=cancel_tt),
                spacer(-20),
                icon_button_editor('truncate_button',
                                   'lightning',
                                   enabled_when='measuring',
                                   tooltip=truncate_tt),
                UItem('truncate_style',
                      enabled_when='measuring',
                      tooltip=truncate_style_tt),
                UItem('show_conditions_button', enabled_when='measuring'),
                spacer(-75),
                CustomLabel('extraction_state_label',
                            color_name='extraction_state_color',
                            size=24,
                            weight='bold')))
        return v


class ExplanationPane(TraitsDockPane):
    id = 'pychron.experiment.explanation'
    name = 'Explanation'
    measurement = Color(MEASUREMENT_COLOR)
    extraction = Color(EXTRACTION_COLOR)
    success = Color(SUCCESS_COLOR)
    skip = Color(SKIP_COLOR)
    canceled = Color(CANCELED_COLOR)
    truncated = Color(TRUNCATED_COLOR)
    failed = Color(FAILED_COLOR)
    not_executable = Color(NOT_EXECUTABLE_COLOR)
    end_after = Color(END_AFTER_COLOR)

    def traits_view(self):
        v = View(
            VGroup(
                HGroup(Label('Extraction'), spring,
                       UReadonly('extraction', )),
                HGroup(Label('Measurement'), spring,
                       UReadonly('measurement', )),
                HGroup(Label('Skip'), spring,
                       UReadonly('skip', )),
                HGroup(Label('Success'), spring,
                       UReadonly('success', )),
                HGroup(Label('Truncated'), spring,
                       UReadonly('truncated', )),
                HGroup(Label('Canceled'), spring,
                       UReadonly('canceled', )),
                HGroup(Label('Failed'), spring,
                       UReadonly('failed', )),
                HGroup(Label('Not Executable'), spring,
                       UReadonly('not_executable', )),
                HGroup(Label('End After'), spring,
                       UReadonly('end_after', ))))
        return v


class IsotopeEvolutionPane(TraitsDockPane):
    id = 'pychron.experiment.isotope_evolution'
    name = 'Isotope Evolutions'
    plot_panel = Instance(PlotPanel, ())
    is_peak_hop = DelegatesTo('plot_panel')

    def traits_view(self):
        v = View(
            VSplit(
                UItem('object.plot_panel.graph_container',
                      style='custom',
                      height=0.75),
                VGroup(
                    HGroup(Spring(springy=False, width=-5),
                           Item('object.plot_panel.ncycles', label='Cycles',
                                tooltip='Set the number of measurement cycles',
                                visible_when='is_peak_hop',
                                width=-100),
                           Spring(springy=False, width=-10),
                           CustomLabel('object.plot_panel.current_cycle',
                                       color='blue',
                                       color_name='object.plot_panel.current_color',
                                       width=175,
                                       visible_when='is_peak_hop'),
                           Spring(springy=False, width=-10),
                           Item('object.plot_panel.ncounts', label='Counts',
                                tooltip='Set the number of measurement points'),
                           Spring(springy=False, width=-5)),
                    UItem('object.plot_panel.analysis_view',
                          style='custom',
                          height=0.25))))
        return v


class SummaryPane(TraitsDockPane):
    id = 'pychron.experiment.summary'
    name = 'Summary'
    plot_panel = Instance('pychron.experiment.plot_panel.PlotPanel')

    def traits_view(self):
        v = View(UItem('plot_panel', editor=InstanceEditor(view='summary_view'),
                       style='custom'))
        return v


class AnalysisHealthAdapter(TabularAdapter):
    columns = [('Isotope', 'name'),
               ('Min.', 'health_min'),
               ('Health', 'health'),
               ('Max.', 'health_max')]


class AnalysisHealthPane(TraitsDockPane):
    id = 'pychron.experiment.analysis_health'
    name = 'Health'

    def traits_view(self):
        v = View(UItem('analysis_type', style='readonly'),

                 Item('isotopes', editor=TabularEditor(adapter=AnalysisHealthAdapter())))
        return v


#============= EOF =============================================
