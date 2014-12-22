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
from traits.api import HasTraits, Int, Button, Event
from traitsui.api import View, Item, HGroup, spring, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.icon_button_editor import icon_button_editor


def EInt(*args, **kw):
    kw['auto_set'] = False
    kw['enter_ser'] = True
    return Int(*args, **kw)


class SystemMonitorControls(HasTraits):
    weeks = EInt(0)
    days = EInt(2)
    hours = EInt(0)
    limit = EInt(5)
    update = Event
    refresh_button = Button

    def _refresh_button_fired(self):
        self.update = True

    def traits_view(self):
        v = View(
            VGroup(VGroup(Item('weeks'),
                          Item('days'),
                          Item('hours'),
                          Item('_'),
                          Item('limit'),
                          label='Search Criteria'),
                   HGroup(spring, icon_button_editor('refresh_button',
                                                     'arrow_refresh',
                                                     tooltip='Refresh')))
        )
        return v
        # ============= EOF =============================================
