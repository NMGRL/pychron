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

from __future__ import absolute_import

from envisage.ui.tasks.task_extension import TaskExtension
from envisage.ui.tasks.task_factory import TaskFactory
from pyface.tasks.action.schema_addition import SchemaAddition
from pyface.tasks.action.task_action import TaskAction

from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.envisage.tasks.list_actions import CancelProcedureAction
from pychron.pyscripts.tasks.pyscript_actions import (
    OpenPyScriptAction,
    NewPyScriptAction,
    OpenHopsEditorAction,
    NewHopsEditorAction,
)
from pychron.pyscripts.tasks.pyscript_preferences import PyScriptPreferencesPane
from pychron.pyscripts.tasks.pyscript_task import ScriptExecutor
from pychron.pyscripts.tasks.visual_el_programmer.actions import (
    OpenVisualELScriptAction,
    NewVisualELScriptAction,
    SwitchRenamerAction,
)


class PyScriptPlugin(BaseTaskPlugin):
    name = "PyScript"
    id = "pychron.pyscript.plugin"

    def _service_offers_default(self):
        so = self.service_offer_factory(
            factory=self._executor_factory, protocol=ScriptExecutor
        )
        return [so]

    def _executor_factory(self):
        return ScriptExecutor(application=self.application)

    def _actions_default(self):
        return [
            ("pychron.open_pyscript", "Ctrl+Shift+O", "Open PyScript"),
            ("pychron.new_pyscript", "Ctrl+Shift+N", "New PyScript"),
        ]

    def _task_extensions_default(self):
        def _replace_action():
            return TaskAction(name="Replace", method="replace")

        exts = [
            TaskExtension(
                task_id="pychron.pyscript.task",
                actions=[
                    SchemaAddition(
                        id="replace", path="MenuBar/edit.menu", factory=_replace_action
                    )
                ],
            ),
            TaskExtension(
                actions=[
                    SchemaAddition(
                        id="open_hops_editor",
                        path="MenuBar/file.menu/Open",
                        factory=OpenHopsEditorAction,
                    ),
                    SchemaAddition(
                        id="new_hops_editor",
                        path="MenuBar/file.menu/New",
                        factory=NewHopsEditorAction,
                    ),
                    SchemaAddition(
                        id="open_script",
                        path="MenuBar/file.menu/Open",
                        factory=OpenPyScriptAction,
                    ),
                    SchemaAddition(
                        id="new_script",
                        path="MenuBar/file.menu/New",
                        factory=NewPyScriptAction,
                    ),
                    SchemaAddition(
                        id="new_visual",
                        path="MenuBar/file.menu/New",
                        factory=NewVisualELScriptAction,
                    ),
                    SchemaAddition(
                        id="open_visual",
                        path="MenuBar/file.menu/Open",
                        factory=OpenVisualELScriptAction,
                    ),
                    SchemaAddition(
                        id="switch_renamer",
                        path="MenuBar/tools.menu",
                        factory=SwitchRenamerAction,
                    ),
                    SchemaAddition(
                        id="cancel_procedure",
                        path="MenuBar/tools.menu",
                        factory=CancelProcedureAction,
                    ),
                ]
            ),
        ]
        return exts

    def _tasks_default(self):
        return [
            TaskFactory(
                id="pychron.pyscript.task",
                name="PyScript",
                factory=self._task_factory,
                task_group="experiment",
                image="script",
            ),
            TaskFactory(
                id="pychron.pyscript.visual_el_programmer",
                name="Visual Programmer",
                factory=self._visual_task_factory,
                task_group="experiment",
            ),
        ]

    def _visual_task_factory(self):
        from pychron.pyscripts.tasks.visual_el_programmer.visual_el_programmer_task import (
            VisualElProgrammerTask,
        )

        return VisualElProgrammerTask(application=self.application)

    def _task_factory(self):
        from pychron.pyscripts.tasks.pyscript_task import PyScriptTask

        return PyScriptTask(application=self.application)

    def _preferences_panes_default(self):
        return [PyScriptPreferencesPane]

    def _preferences_default(self):
        return self._preferences_factory("script")


# ============= EOF =============================================
