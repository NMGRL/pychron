# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from traits.api import Instance
from traitsui.api import Item

from pychron.core.pychron_traits import BorderVGroup
from pychron.experiment.automated_run.factory_view import FactoryView


class CryoFactoryView(FactoryView):
    model = Instance('pychron.experiment.automated_run.cryo.factory.CryoAutomatedRunFactory')

    def _get_group(self):
        post_measurement_group = BorderVGroup(Item('delay_after'), label='Post Measurement')
        return post_measurement_group

# ============= EOF =============================================
