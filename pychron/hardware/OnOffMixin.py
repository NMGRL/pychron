# ===============================================================================
# Copyright 2021 ross
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
from pyface.confirmation_dialog import confirm
from pyface.constant import YES
from traits.api import HasTraits, Event, Bool, Property, Str


class OnOffMixin(HasTraits):
    onoff_button = Event
    onoff_state = Bool
    onoff_label = Property(depends_on="onoff_state")
    use_confirmation = True
    onoff_state_name = Str
    onoff_label_invert = False

    def read_state(self):
        raise NotImplementedError

    def set_active(self, state):
        raise NotImplementedError

    def _get_onoff_label(self):
        s = self._get_onoff_state()
        if self.onoff_label_invert:
            s = not s
        return "Off" if s else "On"

    def _set_onoff_state(self, v):
        name = self.onoff_state_name
        if not name:
            name = "onoff_state"

        return setattr(self, name, v)

    def _get_onoff_state(self):
        name = self.onoff_state_name
        if not name:
            name = "onoff_state"

        return getattr(self, name)

    def _onoff_button_fired(self):
        if self.use_confirmation:
            state = not self._get_onoff_state()
            state = "On" if state else "Off"
            if (
                not confirm(
                    None, "Are you sure you want to {} {}".format(state, self.name)
                )
                == YES
            ):
                return

        self._set_onoff_state(not self._get_onoff_state())
        self.debug("set state = {}".format(self._get_onoff_state()))

        self.set_active(self._get_onoff_state())


# ============= EOF =============================================
