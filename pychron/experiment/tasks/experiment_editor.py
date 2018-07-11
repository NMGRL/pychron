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

import os

from traits.api import Instance, Unicode, Property, DelegatesTo, Color, Bool
from traitsui.api import View, UItem

from pychron.core.helpers.filetools import add_extension
from pychron.core.ui.qt.tabular_editor import TabularEditorHandler
from pychron.core.ui.table_configurer import ExperimentTableConfigurer
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.envisage.tasks.base_editor import BaseTraitsEditor
from pychron.experiment.bulk_run_fixer import BulkRunFixer
from pychron.experiment.automated_run.tabular_adapter import AutomatedRunSpecAdapter, UVAutomatedRunSpecAdapter, \
    ExecutedAutomatedRunSpecAdapter, ExecutedUVAutomatedRunSpecAdapter
from pychron.experiment.queue.experiment_queue import ExperimentQueue
from pychron.experiment.utilities.repository_identifier import get_curtag, populate_repository_identifiers


class ExperimentEditorHandler(TabularEditorHandler):
    refresh_name = 'refresh_table_needed'

    def select_unknowns(self, info, obj):
        obj.select_unknowns()

    def select_same(self, info, obj):
        obj.select_same()

    def select_same_attr(self, info, obj):
        obj.select_same_attr()

    def make_block(self, info, obj):
        obj.make_run_block()

    def repeat_block(self, info, obj):
        obj.repeat_block()

    def toggle_end_after(self, info, obj):
        obj.toggle_end_after()

    def toggle_skip(self, info, obj):
        obj.toggle_skip()

    def show_summary(self, info, obj):
        obj.show_summary()

    def show_evolutions(self, info, obj):
        obj.show_evolutions()

    def show_evolutions_w_bs(self, info, obj):
        obj.show_evolutions(show_baseline=True)

    def show_evolutions_w_eq_bs(self, info, obj):
        obj.show_evolutions(show_baseline=True, show_equilibration=True)

    def show_evolutions_w_eq(self, info, obj):
        obj.show_evolutions(show_equilibration=True)

    def __getattr__(self, item):
        if item.startswith('show_evolution_'):
            key = item.split('_')[-1]

            def closure(info, obj):
                kw = {}
                if item.startswith('show_evolution_eq_bs'):
                    kw['show_equilibration'] = True
                    kw['show_baseline'] = True
                elif item.startswith('show_evolution_eq'):
                    kw['show_equilibration'] = True
                elif item.startswith('show_evolution_bs'):
                    kw['show_baseline'] = True

                obj.show_evolutions((key,), **kw)

            return closure


class ExperimentEditor(BaseTraitsEditor):
    queue = Instance(ExperimentQueue, ())  # Any
    path = Unicode

    name = Property(Unicode, depends_on='path')
    tooltip = Property(Unicode, depends_on='path')

    executed = DelegatesTo('queue')
    tabular_adapter_klass = AutomatedRunSpecAdapter
    executed_tabular_adapter_klass = ExecutedAutomatedRunSpecAdapter
    bgcolor = Color
    tabular_adapter = Instance(AutomatedRunSpecAdapter)
    executed_tabular_adapter = Instance(ExecutedAutomatedRunSpecAdapter)

    automated_runs_editable = Bool
    table_configurer = Instance(ExperimentTableConfigurer)

    bulk_run_fixer = Instance(BulkRunFixer, ())

    def show_table_configurer(self):
        t = self.table_configurer
        t.edit_traits()

    def refresh(self):
        self.queue.refresh_table_needed = True

    def setup_tabular_adapters(self, c, ec, colors):
        self.bgcolor = c
        self.tabular_adapter = self.tabular_adapter_klass()
        self.executed_tabular_adapter = self.executed_tabular_adapter_klass()

        self.executed_tabular_adapter.colors = colors
        self.tabular_adapter.odd_bg_color = c
        self.executed_tabular_adapter.odd_bg_color = c
        self.tabular_adapter.even_bg_color = ec
        self.executed_tabular_adapter.even_bg_color = ec

        v = ExperimentTableConfigurer(children=[self.executed_tabular_adapter],
                                      auto_set=True,
                                      refresh_func=self.refresh,
                                      id='experiment.table')

        self.table_configurer = v
        v.set_adapter(self.tabular_adapter)

    def new_queue(self, txt=None, **kw):
        queue = self.queue_factory(**kw)
        if txt:
            if queue.load(txt):
                self.queue = queue
            else:
                self.warning('failed to load queue')
        else:
            self.queue = queue

    def queue_factory(self, **kw):
        return ExperimentQueue(application=self.application, **kw)

    def save(self, path):
        if self._validate_experiment_queue():
            path = self._dump_experiment_queue(path)
            if path:
                self.path = path
                self.dirty = False

                return True

    def traits_view(self):
        # show row titles is causing a layout issue when resetting queues
        # disabling show_row_titles for the moment.
        operations = ['delete', 'move']
        if self.automated_runs_editable:
            operations.append('edit')

        arun_grp = UItem('automated_runs',
                         editor=myTabularEditor(adapter=self.tabular_adapter,
                                                operations=operations,
                                                editable=True,
                                                mime_type='pychron.automated_run_spec',
                                                show_row_titles=True,
                                                bgcolor=self.bgcolor,

                                                dclicked='dclicked',
                                                selected='selected',
                                                paste_function='paste_function',
                                                update='refresh_table_needed',
                                                refresh='refresh_table_needed',
                                                scroll_to_row='automated_runs_scroll_to_row',
                                                # copy_cache='linked_copy_cache',
                                                stretch_last_section=False,
                                                multi_select=True))

        executed_grp = UItem('display_executed_runs',
                             editor=myTabularEditor(adapter=self.executed_tabular_adapter,
                                                    bgcolor=self.bgcolor,
                                                    editable=False,
                                                    # auto_update=True,
                                                    selectable=True,
                                                    pastable=False,
                                                    mime_type='pychron.automated_run_spec',
                                                    # link_copyable=False,
                                                    paste_function='executed_paste_function',
                                                    # copy_cache='linked_copy_cache',
                                                    update='refresh_table_needed',
                                                    refresh='refresh_table_needed',
                                                    selected='executed_selected',
                                                    multi_select=True,
                                                    stretch_last_section=False,
                                                    scroll_to_row='executed_runs_scroll_to_row'),
                             height=-300,
                             visible_when='executed')

        v = View(executed_grp, arun_grp, handler=ExperimentEditorHandler())
        return v

    def trait_context(self):
        """ Use the model object for the Traits UI context, if appropriate.
        """
        if self.queue:
            return {'object': self.queue}
        return super(ExperimentEditor, self).trait_context()

    # ===============================================================================
    # handlers
    # ===============================================================================
    # def _dirty_changed(self):
    #     self.debug('dirty changed {}'.format(self.dirty))
    def _queue_changed(self, old, new):
        f = self._set_queue_dirty
        if old:
            old.on_trait_change(f, 'automated_runs[]', remove=True)
            old.on_trait_change(f, 'changed', remove=True)
        new.on_trait_change(f, 'automated_runs[]')
        new.on_trait_change(f, 'changed')
        new.path = self.path

    def _path_changed(self):
        self.queue.path = self.path

    def _set_queue_dirty(self, obj, name, old, new):
        if not self.queue.no_update and self.queue.initialized:
            self.dirty = True

    def _validate_experiment_queue(self):
        # check runs
        qi = self.queue

        curtag = get_curtag()
        runs = qi.cleaned_automated_runs
        no_repo = []
        overriden_special = []
        for i, ai in enumerate(runs):
            if not ai.repository_identifier:
                self.warning('No repository identifier for i={}, {}'.format(i + 1, ai.runid))
                no_repo.append(ai)
            elif ai.is_special() \
                    and ai.repository_identifier \
                    and not ai.is_default_repository(qi.mass_spectrometer, curtag):
                overriden_special.append(ai)

        if no_repo:
            if self.confirmation_dialog('Missing repository identifiers. Automatically populate?'):
                populate_repository_identifiers(runs, qi.mass_spectrometer, curtag, debug=self.debug)
                self.refresh()

        if overriden_special:
            if not self.confirmation_dialog('You have reference analyses with non-standard repositories. '
                                            'Are you sure you want to do this? If you are confused or are '
                                            'unsure then the answer is "NO"'):
                for ai in runs:
                    if ai.is_special():
                        ai.repository_identifier = ''

                populate_repository_identifiers(runs, qi.mass_spectrometer, curtag, debug=self.debug)
                self.refresh()

        qi.executable = True
        qi.initialized = True

        self.bulk_run_fixer.patterns = qi.patterns
        self.bulk_run_fixer.fix(runs)

        hec = qi.human_error_checker
        info = hec.check_runs_non_fatal(runs)
        if info:
            if not self.confirmation_dialog('There is a nonfatal issue.\n\n{}\n\n Are you sure you want to '
                                            'continue?'.format(info)):
                return

        err = hec.check_runs(runs, test_all=True, test_scripts=True)
        if err:
            qi.executable = False
            qi.initialized = False
            hec.report_errors(err)
            # self.information_dialog(err)
            return

        err = hec.check_queue(qi)
        if err:
            return
        else:
            return True

    def _dump_experiment_queue(self, p):

        if not p:
            return

        p = add_extension(p)

        self.info('saving experiment to {}'.format(p))
        with open(p, 'w') as wfile:
            self.queue.path = p
            self.queue.dump(wfile)

        return p

    # ===============================================================================
    # property get/set
    # ===============================================================================
    def _get_tooltip(self):
        return self.path

    def _get_name(self):
        if self.path:
            name = os.path.basename(self.path)
            name, _ = os.path.splitext(name)
        else:
            name = 'Untitled'
        return name


class UVExperimentEditor(ExperimentEditor):
    tabular_adapter_klass = UVAutomatedRunSpecAdapter
    executed_tabular_adapter_klass = ExecutedUVAutomatedRunSpecAdapter

# ============= EOF =============================================
