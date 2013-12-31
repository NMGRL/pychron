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
from pyface.action.action import Action
from pyface.image_resource import ImageResource
from pyface.tasks.action.task_action import TaskAction

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.paths import paths


class VCSAction(Action):
    pass

class PushVCSAction(VCSAction):
    image = ImageResource(name='arrow_up.png', search_path=paths.icon_search_path)
    name='Push'
    def perform(self, event):
        app=event.task.window.application
        task=app.open_task('pychron.processing.vcs')
        task.initiate_push()


class PullVCSAction(Action):
    name='Pull'
    image = ImageResource(name='arrow_down.png', search_path=paths.icon_search_path)

    def perform(self, event):
        app = event.task.window.application
        task = app.open_task('pychron.processing.vcs')
        task.initiate_pull()


class CommitVCSAction(TaskAction):
    name='Commit'
    method='commit'

#============= EOF =============================================

