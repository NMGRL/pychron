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
from traits.api import Instance, Unicode, Property, DelegatesTo, Color, Bool
from traitsui.api import View, UItem

# ============= standard library imports ========================
import os
# ============= local library imports  ==========================
from pychron.core.ui.qt.tabular_editor import TabularEditorHandler
from pychron.core.ui.table_configurer import TableConfigurer, ExperimentTableConfigurer
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.experiment.automated_run.tabular_adapter import AutomatedRunSpecAdapter, UVAutomatedRunSpecAdapter, \
    ExecutedAutomatedRunSpecAdapter, ExecutedUVAutomatedRunSpecAdapter
from pychron.experiment.queue.experiment_queue import ExperimentQueue
from pychron.envisage.tasks.base_editor import BaseTraitsEditor
from pychron.core.helpers.filetools import add_extension


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
        obj.end_after()

    def toggle_skip(self, info, obj):
        obj.toggle_skip()


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

    def show_table_configurer(self):
        t = self.table_configurer
        t.edit_traits()

    def refresh(self):
        self.queue.refresh_table_needed = True

    def setup_tabular_adapters(self, c, ec):
        self.bgcolor = c
        self.tabular_adapter = self.tabular_adapter_klass()
        self.executed_tabular_adapter = self.executed_tabular_adapter_klass()

        self.tabular_adapter.odd_bg_color = c
        self.executed_tabular_adapter.odd_bg_color = c
        self.tabular_adapter.even_bg_color = ec
        self.executed_tabular_adapter.even_bg_color = ec

        v = ExperimentTableConfigurer(adapter=self.tabular_adapter,
                                      children=[self.executed_tabular_adapter],
                                      auto_set=True,
                                      refresh_func=self.refresh,
                                      id='experiment.table')

        self.table_configurer = v

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
        return ExperimentQueue(**kw)

    def save(self, path, queues=None):
        if queues is None:
            queues = [self.queue]

        if self._validate_experiment_queues(queues):
            path = self._dump_experiment_queues(path, queues)
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
                                                bgcolor=self.bgcolor,
                                                editable=True,
                                                mime_type='pychron.automated_run_spec',
                                                # show_row_titles=True,
                                                dclicked='dclicked',
                                                selected='selected',
                                                paste_function='paste_function',
                                                refresh='refresh_table_needed',
                                                scroll_to_row='automated_runs_scroll_to_row',
                                                # copy_cache='linked_copy_cache',
                                                stretch_last_section=False,
                                                multi_select=True),
                         height=200)

        executed_grp = UItem('executed_runs',
                             editor=myTabularEditor(adapter=self.executed_tabular_adapter,
                                                    bgcolor=self.bgcolor,
                                                    editable=False,
                                                    auto_update=True,
                                                    selectable=True,
                                                    pastable=False,
                                                    mime_type='pychron.automated_run_spec',
                                                    # link_copyable=False,
                                                    paste_function='executed_paste_function',
                                                    # copy_cache='linked_copy_cache',
                                                    selected='executed_selected',
                                                    multi_select=True,
                                                    stretch_last_section=False,
                                                    scroll_to_row='executed_runs_scroll_to_row'),
                             height=500,
                             visible_when='executed')

        v = View(
            executed_grp,
            arun_grp,
            handler=ExperimentEditorHandler(),
            resizable=True)
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
    def _dirty_changed(self):
        self.debug('dirty changed {}'.format(self.dirty))

    def _queue_changed(self):
        f = self._set_queue_dirty
        self.queue.on_trait_change(f, 'automated_runs[]')
        self.queue.on_trait_change(f, 'changed')
        self.queue.path = self.path

    def _path_changed(self):
        self.queue.path = self.path

    def _set_queue_dirty(self, obj, name, old, new):
        if not self.queue._no_update and self.queue.initialized:
            self.dirty = True

    def _validate_experiment_queues(self, eqs):
        # check runs
        for qi in eqs:
            hec = qi.human_error_checker

            qi.executable = True
            qi.initialized = True

            err = hec.check_runs(qi.cleaned_automated_runs, test_all=True,
                                 test_scripts=True)
            if err:
                qi.executable = False
                qi.initialized = False
                hec.report_errors(err)
                # self.information_dialog(err)
                break

            err = hec.check_queue(qi)
            if err:
                break

        else:
            return True

    def _dump_experiment_queues(self, p, queues):

        if not p:
            return

        p = add_extension(p)

        self.info('saving experiment to {}'.format(p))
        with open(p, 'wb') as fp:
            n = len(queues)
            for i, exp in enumerate(queues):
                exp.path = p
                exp.dump(fp)
                if i < (n - 1):
                    fp.write('\n')
                    fp.write('*' * 80)

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
