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
from traits.api import Instance
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.processing.tasks.batch_edit.batch_edit_task import BatchEditTask
from pychron.processing.tasks.batch_edit.smart_batch_editor import SmartBatchEditor
from pychron.processing.tasks.batch_edit.smart_panes import SmartBatchEditPane
from pychron.processing.tasks.browser.browser_task import BaseBrowserTask


class SmartBatchEditTask(BatchEditTask):
    central_pane_klass = SmartBatchEditPane
    name = 'Smart Batch Edit'
    batch_editor = Instance(SmartBatchEditor, ())

    def prepare_destroy(self):
        pass

    def activated(self):
        BaseBrowserTask.activated(self)

        #============= EOF =============================================
