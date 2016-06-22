# ===============================================================================
# Copyright 2016 Jake Ross
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
from traitsui.menu import Action


# ============= standard library imports ========================
# ============= local library imports  ==========================


class SamplePrepAction(Action):
    name = 'Sample Prep'
    dname = 'Sample Prep'
    id = 'pychron.sample_prep'

    def perform(self, event):
        pid = 'pychron.entry.sample.prep.task'
        app = event.task.window.application
        app.get_task(pid)

# ============= EOF =============================================
