# ===============================================================================
# Copyright 2016 ross
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

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pyface.message_dialog import information
from pyface.tasks.action.task_action import TaskAction

from pychron.processing.analyses.analysis_group import AnalysisGroup
from pychron.pychron_constants import DVC_PROTOCOL


class UploadAction(TaskAction):
    name = 'Upload to Geochron...'

    def perform(self, event):
        information(None, 'Upload to Geochron is not fully implemented')

        app = event.task.application
        geochron_service = app.get_service('pychron.geochron.geochron_service.GeochronService')

        dvc = app.get_service(DVC_PROTOCOL)
        with dvc.session_ctx():
            ai = dvc.get_analysis('c038c72a-cf21-49f9-a5b5-1e43bb4a6b93')
            ans = dvc.make_analyses(ai)

            ag = AnalysisGroup()
            ag.analyses = ans
            print geochron_service.assemble_xml(ag)

# ============= EOF =============================================
