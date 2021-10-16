# ===============================================================================
# Copyright 2015 Jake Ross
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

from traits.api import Float, Property
from traitsui.api import View, Item, Tabbed, VGroup

from pychron.spectrometer.thermo.source.base import ThermoSource


class HelixSource(ThermoSource):
    _flatapole = Float
    _rotation_quad = Float
    _vertical_deflection_n = Float
    _vertical_deflection_s = Float

    flatapole = Property(depends_on="_flatapole")
    rotation_quad = Property(depends_on="_rotation_quad")
    vertical_deflection_n = Property(depends_on="_vertical_deflection_n")
    vertical_deflection_s = Property(depends_on="_vertical_deflection_s")

    def _nominal_hv_default(self):
        return 9900

    def read_flatapole(self):
        return self._read_value("GetParameter DAC_1_0_(Flata-Pole)", "_flatapole")

    def read_rotationquad(self):
        return self._read_value("GetParameter RotationQuad", "_rotation_quad")

    def read_verticaldeflectionn(self):
        return self._read_value(
            "GetParameter DAC_0_0_(Pole-N)", "_vertical_deflection_n"
        )

    def read_verticaldeflections(self):
        return self._read_value(
            "GetParameter DAC_0_4_(Pole-S)", "_vertical_deflection_s"
        )

    def read_z_symmetry(self):
        return self._read_value("GetExtractionSymmetry", "_z_symmetry")

    def sync_parameters(self):
        super(HelixSource, self).sync_parameters()
        self.read_flatapole()
        self.read_rotationquad()
        self.read_verticaldeflectionn()
        self.read_verticaldeflections()

    def _set_parameter(self, param, v):
        if self._set_value("SetParameter", "{} Set,{}".format(param, v)):
            setattr(self, "_{}".format("_".join(param.lower().split(" "))), v)

    def _set_flatapole(self, v):
        self._set_parameter("Flatapole", v)

    def _set_rotation_quad(self, v):
        self._set_parameter("Rotation Quad", v)

    def _set_vertical_deflection_n(self, v):
        self._set_parameter("Vertical Deflection N", v)

    def _set_vertical_deflection_s(self, v):
        self._set_parameter("Vertical Deflection S", v)

    def _get_flatapole(self):
        return self._flatapole

    def _get_rotation_quad(self):
        return self._rotation_quad

    def _get_vertical_deflection_n(self):
        return self._vertical_deflection_n

    def _get_vertical_deflection_s(self):
        return self._vertical_deflection_s

    def traits_view(self):
        gg = VGroup(
            Item("flatapole"),
            Item("rotation_quad"),
            Item("vertical_deflection_n"),
            Item("vertical_deflection_s"),
            label="Multipole",
        )
        v = View(Tabbed(self._get_default_group("General"), gg))
        return v


class HelixSFTSource(HelixSource):
    def _nominal_hv_default(self):
        return 4500


# ============= EOF =============================================
