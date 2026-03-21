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
import os

from traits.api import File, Str, List, Bool
from traitsui.api import ListStrEditor, Item

from pychron.core.helpers.filetools import list_directory
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.paths import paths
from pychron.pipeline.editors.script_editor import PipelinePyScriptEditor
from pychron.pipeline.nodes.base import BaseNode
from pychron.pyscripts.pipeline_pyscript import PipelinePyScript


class PyScriptNode(BaseNode):
    path = File
    selected = Str
    available_scripts = List
    auto_execute = Bool(False)
    name = "PyScript"

    def _configure_hook(self):
        # load available scripts
        self.available_scripts = list_directory(
            paths.pipeline_script_dir, extension=".py", remove_extension=True
        )
        if self.available_scripts:
            self.selected = self.available_scripts[0]

    def run(self, state):
        spath = self._get_path()
        if spath and os.path.isfile(spath):
            root = os.path.dirname(spath)
            name = os.path.basename(spath)
            script = PipelinePyScript(root=root, name=name)

            script.setup_context(unknowns=state.unknowns, state=state)
            editor = PipelinePyScriptEditor(script=script, name=name)

            try:
                editor.init(spath, self.auto_execute)

            except BaseException as e:
                state.veto_message = str(e)
                state.veto = self
                return

            state.editors.append(editor)

    def _get_path(self):
        s = self.selected
        if s:
            path = os.path.join(paths.pipeline_script_dir, "{}.py".format(s))
        else:
            path = self.path

        # path = '/Users/ross/PychronDev/scripts/pipeline/test.py'
        return path

    def traits_view(self):
        v = okcancel_view(
            Item(
                "available_scripts",
                editor=ListStrEditor(selected="selected", editable=False),
            ),
            Item("path", label="Script Location"),
            Item("auto_execute"),
            title="Select Script",
        )
        return v


# ============= EOF =============================================
