# ===============================================================================
# Copyright 2019 ross
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
import io
import traceback

from traits.api import Instance, Button, Str
from traitsui.api import View, Item, Readonly, UItem, TextEditor, Tabbed, VGroup, Group

from pychron.core.file_listener import FileListener
from pychron.core.pychron_traits import BorderVGroup
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.envisage.tasks.base_editor import BaseTraitsEditor

from pychron.pyscripts.pipeline_pyscript import PipelinePyScript


class PipelinePyScriptEditor(BaseTraitsEditor):
    script = Instance(PipelinePyScript)
    execute_button = Button

    file_listener = None
    exception_trace = Str
    output = Str
    results = Str

    def destroy(self):
        super(PipelinePyScriptEditor, self).destroy()
        if self.file_listener:
            self.file_listener.stop()

    def init(self, path, auto_execute):
        self.file_listener = FileListener(path=path, callback=self._refresh_from_disk)

        script = self.script
        script.display_state = 'not run'
        if auto_execute:
            script.bootstrap()
            self._execute()
        else:
            script.bootstrap()

    def _execute(self):
        script = self.script

        output = io.StringIO()
        import sys
        oout = sys.stdout
        sys.stdout = output
        script.execute(test=False, bootstrap=False)

        if script.execution_error:
            script.display_state = 'failed'
            self.exception_trace = script.exception_trace
        else:
            script.display_state = 'completed'
            self.exception_trace = ''
            self.output = output.getvalue()
            output.close()

        sys.stdout = oout

    def _refresh_from_disk(self):
        self.script.bootstrap()

    def _execute_button_fired(self):
        self._execute()

    def traits_view(self):
        error_grp = VGroup(Readonly('object.script.execution_error'),
                           BorderVGroup(UItem('exception_trace', style='custom', editor=TextEditor(read_only=True)),
                                        label='Exception'),
                           label='Errors')

        main_grp = VGroup(icon_button_editor('execute_button', 'start'),
                          Readonly('object.script.display_state'),
                          BorderVGroup(UItem('object.script.text', style='custom'), label='Text'),
                          label='Main')

        results_grp = Group(UItem('results'), label='Results')
        output_grp = Group(UItem('output', style='custom', editor=TextEditor(read_only=True)), label='Output')
        v = View(Tabbed(main_grp, results_grp, error_grp, output_grp))

        return v
# ============= EOF =============================================
