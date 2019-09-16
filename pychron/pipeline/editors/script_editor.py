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

from traits.api import Instance, Button, Str
from traitsui.api import View, Readonly, UItem, TextEditor, Tabbed, VGroup, HGroup

from pychron.core.file_listener import FileListener
from pychron.core.pychron_traits import BorderVGroup
from pychron.core.ui.code_editor import PyScriptCodeEditor
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.envisage.tasks.base_editor import BaseTraitsEditor
from pychron.pyscripts.pipeline_pyscript import PipelinePyScript


class PipelinePyScriptEditor(BaseTraitsEditor):
    script = Instance(PipelinePyScript)
    execute_button = Button

    file_listener = None
    exception_trace = Str
    output = Str

    def destroy(self):
        super(PipelinePyScriptEditor, self).destroy()
        if self.file_listener:
            self.file_listener.stop()

    def init(self, path, auto_execute):
        self.file_listener = FileListener(path=path, callback=self._refresh_from_disk)

        script = self.script
        script.display_state = 'not run'
        script.bootstrap()
        if auto_execute:
            self._execute()

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

        error_grp = BorderVGroup(Readonly('object.script.execution_error'),
                                 BorderVGroup(UItem('exception_trace', style='custom',
                                                    editor=TextEditor(read_only=True)),
                                              label='Exception'),
                                 label='Errors')
        output_grp = VGroup(BorderVGroup(UItem('output', style='custom', editor=TextEditor(read_only=True)),
                                         label='StdOut'),
                            error_grp,
                            label='Output')

        main_grp = VGroup(HGroup(icon_button_editor('execute_button', 'start'),
                                 CustomLabel('object.script.display_state')),
                          BorderVGroup(UItem('object.script.text', style='custom',
                                             editor=PyScriptCodeEditor()), label='Text'),
                          label='Main')

        v = View(Tabbed(main_grp, output_grp))

        return v
# ============= EOF =============================================
