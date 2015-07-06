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
from traits.api import Color, Instance, DelegatesTo, List, Any, Property
from traitsui.api import View, Item, UItem, VGroup, HGroup, spring, \
    EnumEditor, Group, Spring, VFold, Label, InstanceEditor, \
    VSplit, TabularEditor, UReadonly, ListEditor, RangeEditor, Readonly
from pyface.tasks.traits_dock_pane import TraitsDockPane
from traitsui.editors import TableEditor, CheckListEditor
from traitsui.table_column import ObjectColumn
from traitsui.tabular_adapter import TabularAdapter
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.ui.combobox_editor import ComboboxEditor
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.experiment.utilities.identifier import SPECIAL_NAMES
from pychron.pychron_constants import MEASUREMENT_COLOR, EXTRACTION_COLOR, \
    NOT_EXECUTABLE_COLOR, SKIP_COLOR, SUCCESS_COLOR, CANCELED_COLOR, \
    TRUNCATED_COLOR, FAILED_COLOR, END_AFTER_COLOR
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.experiment.plot_panel import PlotPanel


# ===============================================================================
# editing
# ===============================================================================
def spacer(w):
    return Spring(width=w, springy=False)


def queue_factory_name(name):
    return 'object.queue_factory.{}'.format(name)


def run_factory_name(name):
    return 'object.run_factory.{}'.format(name)


def queue_factory_item(name, **kw):
    return Item(queue_factory_name(name), **kw)


def run_factory_item(name, **kw):
    return Item(run_factory_name(name), **kw)


class ExperimentFactoryPane(TraitsDockPane):
    id = 'pychron.experiment.factory'
    name = 'Experiment Editor'
    info_label = Property(depends_on='model.run_factory.info_label')

    def _get_info_label(self):
        return '<font size="12" color="green"><b>{}</b></font>'.format(self.model.run_factory.info_label)

    def traits_view(self):
        # QLabel {font-size: 10px}

        ss = '''
QLineEdit {font-size: 10px}
QGroupBox {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #E0E0E0, stop: 1 #FFFFFF);
    border: 2px solid gray;
    border-radius: 5px;
    margin-top: 1ex; /* leave space at the top for the title */
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left; /* position at the top center */
    padding: 0 3px;
    color: blue;
}
QComboBox {font-size: 10px}

'''

        add_button = icon_button_editor('add_button', 'add',
                                        # enabled_when='ok_add',
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
            HGroup(UItem(queue_factory_name('username'),
                         show_label=False,
                         editor=ComboboxEditor(name=queue_factory_name('usernames'))),
                   icon_button_editor(queue_factory_name('edit_user'), 'database_edit'),
                   # Spring(width=-5, springy=False),
                   queue_factory_item('use_email',
                                      tooltip='Send email notifications',
                                      show_label=False),
                   Item(queue_factory_name('email')),
                   queue_factory_item('use_group_email',
                                      tooltip='Email a group of users',
                                      label='Group'),
                   icon_button_editor(queue_factory_name('edit_emails'), 'cog',
                                      tooltip='Edit user group')),
            HGroup(
                queue_factory_item('mass_spectrometer',
                                   show_label=False,
                                   editor=EnumEditor(name=queue_factory_name('mass_spectrometers'))),
                queue_factory_item('extract_device',
                                   show_label=False,
                                   editor=EnumEditor(name=queue_factory_name('extract_devices'))),
                queue_factory_item('load_name',
                                   width=150,
                                   label='Load',
                                   editor=ComboboxEditor(name=queue_factory_name('load_names'))),
                icon_button_editor('generate_queue_button', 'brick-go',
                                   tooltip='Generate a experiment queue from the selected load',
                                   enabled_when='load_name'),
                icon_button_editor('edit_queue_config_button', 'cog',
                                   tooltip='Configure experiment queue generation')),
            HGroup(queue_factory_item('queue_conditionals_name',
                                      label='Queue Conditionals',
                                      editor=EnumEditor(name=queue_factory_name('available_conditionals')))),
            queue_factory_item('delay_before_analyses'),
            queue_factory_item('delay_between_analyses'),
            show_border=True,
            label='Queue')

        button_bar = HGroup(
            save_button,
            add_button,
            clear_button,
            edit_button,
            CustomLabel(run_factory_name('edit_mode_label'),
                        color='red',
                        width=40),
            spring,
            run_factory_item('end_after', width=30),
            run_factory_item('skip'))
        button_bar2 = HGroup(Item('auto_increment_id', label='Auto Increment L#'),
                             Item('auto_increment_position', label='Position'), )
        edit_grp = VFold(
            queue_grp,
            VGroup(
                self._get_info_group(),
                self._get_extract_group(),
                label='General'),
            self._get_script_group(),
            self._get_truncate_group(),
            enabled_when=queue_factory_name('ok_make'))

        # lower_button_bar = HGroup(
        # add_button,
        # clear_button,
        # Label('Auto Increment'),
        # Item('auto_increment_id', label='L#'),
        # Item('auto_increment_position', label='Position'))
        v = View(
            VGroup(
                # queue_grp,
                button_bar,
                button_bar2,
                UItem('pane.info_label', style='readonly'),
                # CustomLabel(run_factory_name('info_label'), size=14, color='green'),
                edit_grp,

                # lower_button_bar,
                style_sheet=ss),
            kind='live',
            width=225)
        return v

    def _get_info_group(self):
        grp = Group(
            HGroup(
                run_factory_item('selected_irradiation',
                                 show_label=False,
                                 editor=EnumEditor(name=run_factory_name('irradiations'))),
                run_factory_item('selected_level',
                                 show_label=False,
                                 editor=EnumEditor(name=run_factory_name('levels')))),

            HGroup(run_factory_item('special_labnumber',
                                    show_label=False,
                                    editor=EnumEditor(values=SPECIAL_NAMES)),
                   run_factory_item('run_block', show_label=False,
                                    editor=EnumEditor(name=run_factory_name('run_blocks'))),
                   icon_button_editor(run_factory_name('edit_run_blocks'), 'cog'),
                   run_factory_item('frequency_model.frequency_int', width=50),
                   icon_button_editor(run_factory_name('edit_frequency_button'), 'cog'),
                   # run_factory_item('freq_before', label='Before'),
                   # run_factory_item('freq_after', label='After'),
                   spring),

            # HGroup(run_factory_item('labnumber',
            # tooltip='Enter a Labnumber',
            # width=100, ),
            #        run_factory_item('_labnumber', show_label=False,
            #                         editor=CheckListEditor(name=run_factory_name('labnumbers')),
            #                         width=-20),
            #        run_factory_item('aliquot',
            #                         width=50),
            #        spring),

            HGroup(run_factory_item('labnumber',
                                    tooltip='Enter a Labnumber',
                                    width=100,
                                    editor=ComboboxEditor(name=run_factory_name('labnumbers'))),
                   run_factory_item('aliquot',
                                    width=50),
                   spring),

            HGroup(
                run_factory_item('weight',
                                 label='Weight (mg)',
                                 tooltip='(Optional) Enter the weight of the sample in mg. '
                                         'Will be saved in Database with analysis'),
                run_factory_item('comment',
                                 tooltip='(Optional) Enter a comment for this sample. '
                                         'Will be saved in Database with analysis'),
                run_factory_item('auto_fill_comment',
                                 show_label=False,
                                 tooltip='Auto fill "Comment" with IrradiationLevel:Hole, e.g A:9'),
                # run_factory_item('comment_template',
                # editor=EnumEditor(name=run_factory_name('comment_templates')),
                # show_label=False),
                icon_button_editor(run_factory_name('edit_comment_template'), 'cog',
                                   tooltip='Edit comment template')),
            HGroup(run_factory_item('flux'),
                   Label(u'\u00b1'),
                   run_factory_item('flux_error', show_label=False),
                   icon_button_editor(run_factory_name('save_flux_button'),
                                      'database_save',
                                      tooltip='Save flux to database'),
                   enabled_when=run_factory_name('labnumber')),

            show_border=True,
            label='Sample Info')
        return grp

    def _get_truncate_group(self):
        grp = VGroup(
            HGroup(run_factory_item('use_simple_truncation', label='Use Simple'),
                   icon_button_editor(run_factory_name('clear_conditionals'),
                                      'delete',
                                      tooltip='Clear Conditionals from selected runs'
                                      # enabled_when=run_factory_name('edit_mode')
                   )),
            HGroup(
                run_factory_item('trunc_attr',
                                 editor=EnumEditor(name=run_factory_name('trunc_attrs')),
                                 show_label=False),
                run_factory_item('trunc_comp', show_label=False),
                run_factory_item('trunc_crit', show_label=False),
                spacer(-10),
                run_factory_item('trunc_start', label='Start Count'),
                show_border=True,
                # enabled_when = run_factory_name('use_simple_truncation'),
                label='Simple'),
            HGroup(
                run_factory_item('conditionals_path',
                                 editor=EnumEditor(name=run_factory_name('conditionals')),
                                 label='Path'),

                icon_button_editor(run_factory_name('edit_conditionals_button'), 'table_edit',
                                   enabled_when=run_factory_name('conditionals_path'),
                                   tooltip='Edit the selected conditionals file'),
                icon_button_editor(run_factory_name('new_conditionals_button'), 'table_add',
                                   tooltip='Add a new conditionals file. Duplicated currently '
                                           'selected file if applicable'),
                show_border=True,
                label='File'),
            label='Run Conditionals')
        return grp

    def _get_script_group(self):
        script_grp = VGroup(
            run_factory_item('extraction_script', style='custom', show_label=False),
            run_factory_item('measurement_script', style='custom', show_label=False),
            run_factory_item('post_equilibration_script', style='custom', show_label=False),
            run_factory_item('post_measurement_script', style='custom', show_label=False),
            run_factory_item('script_options', style='custom', show_label=False),
            HGroup(spring,
                   run_factory_item('default_fits_button',
                                    show_label=False,
                                    enabled_when=run_factory_name('default_fits_enabled'),
                                    label='Default Fits'),
                   run_factory_item('load_defaults_button',
                                    tooltip='load the default scripts for this analysis type',
                                    show_label=False,
                                    enabled_when=run_factory_name('labnumber'))),
            show_border=True,
            label='Scripts')
        return script_grp

    def _get_extract_group(self):
        return run_factory_item('factory_view', style='custom', show_label=False)


# ===============================================================================
# execution
# ===============================================================================
class WaitPane(TraitsDockPane):
    id = 'pychron.experiment.wait'
    name = 'Wait'

    def traits_view(self):
        cview = View(VGroup(
            CustomLabel('message',
                        size=14,
                        weight='bold',
                        color_name='message_color'),

            HGroup(Spring(width=-5, springy=False),
                   Item('high', label='Set Max. Seconds'),
                   spring,
                   CustomLabel('current_time',
                               size=14,
                               weight='bold'),
                   UItem('continue_button')),
            HGroup(Spring(width=-5, springy=False),
                   Item('current_time', show_label=False,
                        editor=RangeEditor(mode='slider', low=1, high_name='duration')))))

        v = View(UItem('active_control',
                       style='custom',
                       visible_when='single',
                       editor=InstanceEditor(view=cview)),
                 UItem('controls',
                       editor=ListEditor(
                           use_notebook=True,
                           selected='active_control',
                           page_name='.page_name',
                           view=cview),
                       style='custom',
                       visible_when='not single'))
        return v

        # def traits_view(self):
        # v = View(
        # UItem('wait_group',
        #               style='custom'))
        #     return v


class ConnectionStatusPane(TraitsDockPane):
    id = 'pychron.experiment.connection_status'
    name = 'Connection Status'

    def traits_view(self):
        cols = [ObjectColumn(name='name', editable=False),
                ObjectColumn(name='connected', editable=False)]
        v = View(UItem('connectables',
                       editor=TableEditor(editable=False,
                                          sortable=False,
                                          columns=cols)))
        return v


class StatsPane(TraitsDockPane):
    id = 'pychron.experiment.stats'
    name = 'Stats'
    def traits_view(self):
        v = View(VGroup(Readonly('nruns', label='Total Runs'),
                        Readonly('nruns_finished', label='Completed'),
                        Readonly('total_time'),
                        Readonly('start_at'),
                        Readonly('end_at'),
                        Readonly('run_duration'),
                        Readonly('current_run_duration', ),
                        Readonly('etf', label='Est. finish'),
                        Readonly('elapsed'),
                        Readonly('run_elapsed'),
                        show_border=True))
        return v

    # def traits_view(self):
    #     v = View(UItem('stats', style='custom'))
    #     return v


class ControlsPane(TraitsDockPane):
    # name = 'Controls'
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
                UItem('show_conditionals_button',
                      # enabled_when='measuring'
                ),
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
                           Spring(springy=False, width=-10),
                           CustomLabel('object.plot_panel.display_counts',
                                       color='red',
                                       size=14,
                                       width=100),
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


class LoggerPane(TraitsDockPane):
    loggers = List
    selected = Any
    name = 'Logger'
    id = 'pychron.experiment.logger'

    def __init__(self, *args, **kw):
        super(LoggerPane, self).__init__(*args, **kw)
        from pychron.displays.gdisplays import gWarningDisplay, gLoggerDisplay

        self.loggers = [gLoggerDisplay, gWarningDisplay]

    def traits_view(self):
        v = View(UItem('loggers',
                       editor=ListEditor(use_notebook=True,
                                         page_name='.title',
                                         selected='selected'),
                       style='custom'))

        return v

# ============= EOF =============================================
