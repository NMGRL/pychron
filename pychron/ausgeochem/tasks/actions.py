# ===============================================================================
# Copyright 2024 Pychron Developers
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

from __future__ import absolute_import

from pyface.message_dialog import information
from pyface.tasks.action.task_action import TaskAction


class UploadAusGeochemAction(TaskAction):
    name = "Test AusGeochem EarthData Connection..."

    def perform(self, event):
        app = event.task.application
        service = app.get_service(
            "pychron.ausgeochem.earthdata_service.AusGeochemEarthDataService"
        )
        if service is None:
            information(None, "AusGeochem service is not available")
            return

        if service.test_connection():
            information(None, "Successfully connected to AusGeochem EarthData")
        else:
            information(
                None,
                "AusGeochem EarthData connection failed. Check credentials/logs.",
            )


# ============= EOF =============================================
