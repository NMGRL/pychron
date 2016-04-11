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
from traits.api import Float, Range, Property
from traitsui.api import View, Item, RangeEditor
# ============= standard library imports ========================

# ============= local library imports  ==========================
from pychron.spectrometer.thermo.spectrometer_device import SpectrometerDevice


class ThermoSource(SpectrometerDevice):
    nominal_hv = Float(4500)
    current_hv = Float(4500)

    trap_current = Property(depends_on='_trap_current')
    _trap_current = Float

    z_symmetry = Property(depends_on='_z_symmetry')
    y_symmetry = Property(depends_on='_y_symmetry')
    extraction_lens = Property(Range(0, 100.0), depends_on='_extraction_lens')

    _y_symmetry = Float  # Range(0.0, 100.)
    _z_symmetry = Float  # Range(0.0, 100.)

    y_symmetry_low = Float(-100.0)
    y_symmetry_high = Float(100.0)
    z_symmetry_low = Float(-100.0)
    z_symmetry_high = Float(100.0)

    _extraction_lens = Float  # Range(0.0, 100.)

    def set_hv(self, v):
        return self._set_value('SetHV', v)

    def read_trap_current(self):
        return self._read_value('GetParameter Trap Current Readback', '_trap_current')

    def read_y_symmetry(self):
        return self._read_value('GetYSymmetry', '_y_symmetry')

    def read_z_symmetry(self):
        return self._read_value('GetZSymmetry', '_z_symmetry')

    def read_hv(self):
        return self._read_value('GetHighVoltage', 'current_hv')

    def _set_value(self, name, v):
        r = self.ask('{} {}'.format(name, v))
        if r is not None:
            if r.lower().strip() == 'ok':
                return True

    def _read_value(self, name, value):
        r = self.ask(name)
        try:
            r = float('{:0.3f}'.format(float(r)))
            setattr(self, value, r)
            return getattr(self, value)
        except (ValueError, TypeError):
            pass

    def sync_parameters(self):
        self.read_y_symmetry()
        self.read_z_symmetry()
        self.read_trap_current()
        self.read_hv()

    def traits_view(self):
        v = View(Item('nominal_hv', format_str='%0.4f'),
                 Item('current_hv', format_str='%0.4f', style='readonly'),
                 Item('trap_current'),
                 Item('y_symmetry', editor=RangeEditor(low_name='y_symmetry_low',
                                                       high_name='y_symmetry_high',
                                                       mode='slider')),
                 Item('z_symmetry', editor=RangeEditor(low_name='z_symmetry_low',
                                                       high_name='z_symmetry_high',
                                                       mode='slider')),
                 Item('extraction_lens'))
        return v

    # ===============================================================================
    # property get/set
    # ===============================================================================
    def _get_trap_current(self):
        return self._trap_current

    def _get_y_symmetry(self):
        return self._y_symmetry

    def _get_z_symmetry(self):
        return self._z_symmetry

    def _get_extraction_lens(self):
        return self._extraction_lens

    def _set_trap_current(self, v):
        if self._set_value('SetParameter', 'Trap Current Set,{}'.format(v)):
            self._trap_current = v

    def _set_y_symmetry(self, v):
        if self._set_value('SetYSymmetry', v):
            self._y_symmetry = v

    def _set_z_symmetry(self, v):
        if self._set_value('SetZSymmetry', v):
            self._z_symmetry = v

    def _set_extraction_lens(self, v):
        if self._set_value('SetExtractionLens', v):
            self._extraction_lens = v

# ============= EOF =============================================
