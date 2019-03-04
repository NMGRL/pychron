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

from envisage.ui.tasks.task_factory import TaskFactory

from pychron.lasers.tasks.plugins.laser_plugin import BaseLaserPlugin


class ChromiumPlugin(BaseLaserPlugin):

    def test_communication(self):
        man = self._get_manager()
        return man.test_connection()

    def _get_task_klass(self):
        factory = __import__(self.task_klass[0], fromlist=[self.task_klass[1]])
        klassfactory = getattr(factory, self.task_klass[1])
        return klassfactory

    def _task_factory(self):
        klass = self._get_task_klass()
        t = klass(manager=self._get_manager(), application=self.application)
        return t

    def _tasks_default(self):
        return [TaskFactory(id=self.id,
                            task_group='hardware',
                            factory=self._task_factory,
                            name=self.task_name,
                            image='laser',
                            accelerator=self.accelerator)]

    def _task_extensions_default(self):
        exts = self._create_task_extensions()
        self._setup_pattern_extensions(exts)

        return exts
# ============= EOF =============================================
