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
from envisage.ui.tasks.task_factory import TaskFactory
from envisage.ui.tasks.task_extension import TaskExtension
from pyface.tasks.action.schema_addition import SchemaAddition
from pyface.tasks.action.task_action import TaskAction
from pyface.tasks.action.schema import SMenu
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.pyscripts.tasks.pyscript_task import PyScriptTask
from pychron.pyscripts.tasks.pyscript_actions import OpenPyScriptAction, \
    NewPyScriptAction
from pychron.pyscripts.tasks.pyscript_preferences import PyScriptPreferencesPane


class PyScriptPlugin(BaseTaskPlugin):
    def _my_task_extensions_default(self):
        def _replace_action():
            return TaskAction(name='Replace',
                              method='replace')

        exts = [
            TaskExtension(
                task_id='pychron.pyscript',
                actions=[SchemaAddition(
                    id='Edit',
                    factory=lambda: SMenu(id='Edit', name='Edit'),
                    path='MenuBar'),
                         SchemaAddition(id='replace',
                                        path='MenuBar/Edit',
                                        factory=_replace_action)]),

            TaskExtension(
                actions=[
                    SchemaAddition(id='open_script',
                                   path='MenuBar/File/Open',
                                   factory=OpenPyScriptAction),
                    SchemaAddition(id='new_script',
                                   path='MenuBar/File/New',
                                   factory=NewPyScriptAction)])]
        return exts

    def _tasks_default(self):
        return [TaskFactory(
            id='pychron.pyscript',
            name='PyScript',
            factory=self._task_factory,
            task_group='experiment',
            image='script.png')]

    def _task_factory(self):
        return PyScriptTask()

    def _preferences_panes_default(self):
        return [PyScriptPreferencesPane]

#============= EOF =============================================
