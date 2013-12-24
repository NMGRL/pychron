#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Color, Instance, DelegatesTo
from traitsui.api import View, Item, UItem, VGroup, HGroup, spring, \
    EnumEditor, Group, Spring, VFold, Label, InstanceEditor, \
    CheckListEditor, VSplit, TabularEditor
# from pyface.tasks.traits_task_pane import TraitsTaskPane
from pyface.tasks.traits_dock_pane import TraitsDockPane
from traitsui.tabular_adapter import TabularAdapter
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.experiment.utilities.identifier import SPECIAL_NAMES
# from pychron.core.ui.tabular_editor import myTabularEditor
# from pychron.experiment.automated_run.tabular_adapter import AutomatedRunSpecAdapter
from pychron.pychron_constants import MEASUREMENT_COLOR, EXTRACTION_COLOR, \
    NOT_EXECUTABLE_COLOR, SKIP_COLOR, SUCCESS_COLOR, CANCELED_COLOR, \
    TRUNCATED_COLOR, FAILED_COLOR, END_AFTER_COLOR
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.experiment.plot_panel import PlotPanel

#============= standard library imports ========================
#============= local library imports  ==========================

#===============================================================================
# editing
#===============================================================================



def spacer(w):
    return Spring(width=w, springy=False)


def make_qf_name(name):
    return 'object.queue_factory.{}'.format(name)


def make_rf_name(name):
    return 'object.run_factory.{}'.format(name)


def QFItem(name, **kw):
    return Item(make_qf_name(name), **kw)


def RFItem(name, **kw):
    return Item(make_rf_name(name), **kw)


def make_rt_name(name):
    return 'object.experiment_queue.runs_table.{}'.format(name)


def RTItem(name, **kw):
    return Item(make_rt_name(name), **kw)


class ExperimentFactoryPane(TraitsDockPane):
    id = 'pychron.experiment.factory'
    name = 'Experiment Editor'

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

        queue_grp = VGroup(
            QFItem('username'),
            HGroup(
                QFItem('mass_spectrometer',
                       show_label=False,
                       editor=EnumEditor(name=make_qf_name('mass_spectrometers'))),
                QFItem('extract_device',
                       show_label=False,
                       editor=EnumEditor(name=make_qf_name('extract_devices')))),
            QFItem('load_name',
                   show_label=False,
                   editor=EnumEditor(name=make_qf_name('load_names'))),
            QFItem('delay_before_analyses'),
            QFItem('delay_between_analyses'))

        button_bar = HGroup(
            save_button,
            add_button,
            clear_button,
            edit_button,
            CustomLabel(make_rf_name('edit_mode_label'),
                        color='red',
                        width=40),
            spring,
            RFItem('end_after', width=30),
            RFItem('skip'))
        edit_grp = VFold(
            VGroup(
                self._get_info_group(),
                self._get_extract_group(),
                label='General'),
            self._get_script_group(),
            self._get_truncate_group(),
            enabled_when=make_qf_name('ok_make'))

        lower_button_bar = HGroup(
            add_button,
            clear_button,
            Label('Auto Increment'),
            Item('auto_increment_id', label='L#'),
            Item('auto_increment_position', label='Position'))
        v = View(
            VGroup(
                queue_grp,
                button_bar,
                CustomLabel(make_rf_name('info_label')),
                edit_grp,
                lower_button_bar
            ),
            width=225
        )
        return v

    def _get_info_group(self):
        grp = Group(
            #                   HGroup(spring, CustomLabel('help_label', size=14), spring),
            HGroup(
                RFItem('selected_irradiation',
                       #                                 label='Irradiation',

                       show_label=False,
                       editor=EnumEditor(name=make_rf_name('irradiations'))),
                RFItem('selected_level',
                       show_label=False,
                       #                                 label='Level',
                       editor=EnumEditor(name=make_rf_name('levels'))),

                #                          RFItem('project', editor=EnumEditor(name=make_rf_name('projects')),
                #                                 ),

            ),

            HGroup(RFItem('special_labnumber',
                          show_label=False,
                          editor=EnumEditor(values=SPECIAL_NAMES),
            ),
                   RFItem('frequency', width=50),
                   spring
            ),
            HGroup(RFItem('labnumber',
                          tooltip='Enter a Labnumber',
                          width=100,
            ),
                   RFItem('_labnumber', show_label=False,
                          #                              editor=EnumEditor(name=make_rf_name('labnumbers')),
                          editor=CheckListEditor(name=make_rf_name('labnumbers')),
                          width=-20,
                   ),
                   spring,
            ),
            HGroup(RFItem('flux'),
                   Label(u'\u00b1'),
                   RFItem('flux_error', show_label=False),
                   icon_button_editor(make_rf_name('save_flux_button'),
                                      'database_save',
                                      tooltip='Save flux to database'
                   ),
                   enabled_when=make_rf_name('labnumber')
                   #                           spring,
            ),
            HGroup(
                RFItem('aliquot',
                       width=50
                ),
                RFItem('irradiation',
                       tooltip='Irradiation info retreived from Database',
                       style='readonly',
                       width=90,
                ),
                RFItem('sample',
                       tooltip='Sample info retreived from Database',
                       style='readonly',
                       width=100,
                       show_label=False
                ),
                spring
            ),
            HGroup(
                RFItem('weight',
                       label='Weight (mg)',
                       tooltip='(Optional) Enter the weight of the sample in mg. Will be saved in Database with analysis',
                ),
                RFItem('comment',
                       tooltip='(Optional) Enter a comment for this sample. Will be saved in Database with analysis'
                ),
                RFItem('auto_fill_comment',
                       show_label=False,
                       tooltip='Auto fill "Comment" with IrradiationLevel:Hole, e.g A:9'
                )
            ),
            show_border=True,
            label='Sample Info'
        )
        return grp

    def _get_truncate_group(self):
        grp = VGroup(
            HGroup(
                RFItem('trunc_attr', show_label=False),
                RFItem('trunc_comp', show_label=False),
                RFItem('trunc_crit', show_label=False),
                spacer(-10),
                RFItem('trunc_start', label='Start Count'),
                show_border=True,
                label='Simple'
            ),
            HGroup(
                RFItem('truncation_path',
                       editor=EnumEditor(name=make_rf_name('truncations')),
                       label='Path'
                ),
                show_border=True,
                label='File'
            ),
            label='Actions'
        )
        return grp

    def _get_script_group(self):
        script_grp = VGroup(
            RFItem('extraction_script', style='custom', show_label=False),
            RFItem('measurement_script', style='custom', show_label=False),
            RFItem('post_equilibration_script', style='custom', show_label=False),
            RFItem('post_measurement_script', style='custom', show_label=False),
            HGroup(spring, RFItem('load_defaults_button',
                                  tooltip='load the default scripts for this analysis type',
                                  show_label=False,
                                  enabled_when=make_rf_name('labnumber'))),
            show_border=True,
            label='Scripts'
        )
        return script_grp

    def _get_extract_group(self):
        return RFItem('factory_view', style='custom', show_label=False)


#===============================================================================
# execution
#===============================================================================
class WaitPane(TraitsDockPane):
    id = 'pychron.experiment.wait'
    name = 'Wait'

    def traits_view(self):
        v = View(
            #                  UItem('wait_dialog',
            UItem('wait_group',
                  style='custom',
            ),
            #                 height=-100
        )
        return v


class StatsPane(TraitsDockPane):
    id = 'pychron.experiment.stats'
    name = 'Stats'

    def traits_view(self):
        v = View(
            UItem('stats', style='custom')
        )
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
                                   tooltip=start_tt,
                ),
                icon_button_editor('stop_button', 'stop',
                                   enabled_when='not can_start',
                                   tooltip=stop_tt
                ),

                spacer(-20),
                Item('end_at_run_completion',
                     label='Stop at Completion',
                     tooltip=end_tt
                ),
                spacer(-20),
                icon_button_editor('cancel_run_button', 'cancel',
                                   enabled_when='can_cancel',
                                   tooltip=cancel_tt
                ),
                spacer(-20),
                icon_button_editor('truncate_button',
                                   'lightning',
                                   enabled_when='measuring',
                                   tooltip=truncate_tt
                ),
                UItem('truncate_style',
                      enabled_when='measuring',
                      tooltip=truncate_style_tt,
                ),
                spacer(-75),
                CustomLabel('extraction_state_label',
                            color_name='extraction_state_color',
                            size=24,
                            weight='bold'
                ),
            ),
        )
        return v


#class ConsolePane(TraitsDockPane):
#    id = 'pychron.experiment.console'
#    name = 'Console'
#
#    def traits_view(self):
#        v = View(UItem('console_display', style='custom'))
#        return v


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
                       UItem('extraction',
                             style='readonly')
                ),
                HGroup(Label('Measurement'), spring,
                       UItem('measurement',
                             style='readonly')
                ),
                HGroup(Label('Skip'), spring,
                       UItem('skip',
                             style='readonly')
                ),
                HGroup(Label('Success'), spring,
                       UItem('success',
                             style='readonly')
                ),
                HGroup(Label('Truncated'), spring,
                       UItem('truncated',
                             style='readonly')
                ),
                HGroup(Label('Canceled'), spring,
                       UItem('canceled',
                             style='readonly')
                ),
                HGroup(Label('Failed'), spring,
                       UItem('failed',
                             style='readonly')
                ),
                HGroup(Label('Not Executable'), spring,
                       UItem('not_executable',
                             style='readonly')
                ),
                HGroup(Label('End After'), spring,
                       UItem('end_after',
                             style='readonly')
                ),
            )

        )
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
                           Spring(springy=False, width=-5),
                    ),
                    UItem('object.plot_panel.analysis_view',
                          style='custom',
                          height=0.25),
                )
            )
        )
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

                 Item('isotopes', editor=TabularEditor(adapter=AnalysisHealthAdapter()))

        )
        return v

# from pyface.tasks.enaml_dock_pane import EnamlDockPane
# class TestEnamlPane(EnamlDockPane):
#    def create_component(self):
#        pass

#============= EOF =============================================
