# ===============================================================================
# Copyright 2012 Jake Ross
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
from traitsui.api import View, Item

from pychron.hardware.core.abstract_device import AbstractDevice

# ============= standard library imports ========================
# ============= local library imports  ==========================

class PidController(AbstractDevice):
    def load_additional_args(self, config, **kw):
        from pychron.hardware.eurotherm import Eurotherm
        self._cdevice = Eurotherm(name='Eurotherm')
        self._cdevice.load()

        return True


# from traits.api import Instance
from traitsui.api import ButtonEditor
class DevelopmentPidController(PidController):

    def get_process_value(self, **kw):
        return self._cdevice.get_random_value()

    def traits_view(self):
        v = View(
                 Item('_cdevice', style='custom', show_label=False),
                 Item('scan_button', show_label=False, editor=ButtonEditor(label_value='scan_label')),
                 Item('graph', show_label=False, style='custom'))

        return v
# ============= EOF =============================================
