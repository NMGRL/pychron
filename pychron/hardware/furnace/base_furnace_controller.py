# ===============================================================================
# Copyright 2023 Jake Ross
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
from traits.api import HasTraits, Float, Property, provides, Int
from traits.trait_errors import TraitError

from pychron.furnace.ifurnace_controller import IFurnaceController


@provides(IFurnaceController)
class BaseFurnaceController(HasTraits):
    output_value = Float
    process_value = Float
    process_setpoint = Property(
        Float(enter_set=True, auto_set=False), depends_on="_setpoint"
    )
    _setpoint = Float
    setpoint_min = Int(0)
    setpoint_max = Int(1800)

    def test_connection(self):
        pv = self.get_process_value()
        return pv is not None

    def get_setpoint(self, *args, **kw):
        return self.process_setpoint

    def set_setpoint(self, v):
        self.process_setpoint = v

    def get_output(self, *args, **kw):
        try:
            self.output_value = self.get_output_hook(*args, **kw)
        except TraitError:
            pass

        return self.output_value

    def get_output_hook(self, *args, **kw):
        raise NotImplementedError

    def get_process_value_hook(self, *args, **kw):
        raise NotImplementedError

    def set_process_setpoint_hook(self, v):
        raise NotImplementedError

    read_percent_output = get_output

    def get_process_value(self, *args, **kw):
        try:
            self.process_value = self.get_process_value_hook(
                verbose=kw.get("verbose", True)
            )
        except TraitError:
            pass

        return self.process_value

    def _get_process_setpoint(self):
        """ """
        return self._setpoint

    def _set_process_setpoint(self, v):
        """ """
        if v is not None:
            self._setpoint = v
            self.set_process_setpoint_hook(v)

    def _validate_process_setpoint(self, v):
        """ """
        try:
            float(v)
        except ValueError:
            pass

        if self.setpoint_min <= v < self.setpoint_max:
            return v


# ============= EOF =============================================
