# ===============================================================================
# Copyright 2011 Jake Ross
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
from traitsui.api import View, Item, HGroup

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.spectrometer.base_detector import BaseDetector
from pychron.spectrometer.spectrometer_device import SpectrometerDevice


class NuDetector(BaseDetector, SpectrometerDevice):

    def traits_view(self):
        from pychron.core.ui.qt.color_square_editor import ColorSquareEditor

        v = View(
            HGroup(
                Item("active"),
                Item("color", width=25, editor=ColorSquareEditor()),
                Item("name", style="readonly"),
                # spring,
                # Item('deflection', visible_when='use_deflection'),
                show_labels=False,
            )
        )
        return v


# ============= EOF =============================================
