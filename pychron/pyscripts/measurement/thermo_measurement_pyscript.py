# ===============================================================================
# Copyright 2012 Jake Ross
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
# ============= standard library imports ========================

from pychron.pyscripts.decorators import verbose_skip
from pychron.pyscripts.measurement_pyscript import MeasurementPyScript, command_register

ESTIMATED_DURATION_FF = 1.0


class ThermoMeasurementPyScript(MeasurementPyScript):
    @verbose_skip
    @command_register
    def set_deflection(self, detname, v=""):
        """
        if v is an empty str (default) then get the deflection value from
        the configuration file.

        :param detname: name of detector
        :type detname: str
        :param v: deflection value or an empty string
        :type v: '', int, float

        """
        if v == "":
            v = self._get_deflection_from_file(detname)

        if v is not None:
            v = "{},{}".format(detname, v)
            self._set_spectrometer_parameter("SetDeflection", v)
        else:
            self.debug(
                "no deflection value for {} supplied or in the config file".format(
                    detname
                )
            )

    @verbose_skip
    @command_register
    def get_deflection(self, detname):
        """
        Read the deflection from the spectrometer

        :param detname: name of detector
        :type detname: str
        :return: float
        """
        v = self._get_spectrometer_parameter("GetDeflection {}".format(detname))
        try:
            v = float(v)
        except (TypeError, ValueError):
            self.warning("error getting deflection")
            self.debug_exception()
            v = 0

        return v

    @verbose_skip
    @command_register
    def set_deflections(self):
        """
        Set deflections to values stored in config.cfg
        """
        func = self._set_spectrometer_parameter

        config = self._get_config()
        section = "Deflections"
        dets = config.options(section)
        for dn in dets:
            v = config.getfloat(section, dn)
            if v is not None:
                func("SetDeflection", "{},{}".format(dn, v))

    @verbose_skip
    @command_register
    def set_ysymmetry(self, v):
        """
        Set YSymmetry to v

        :param v: ysymmetry value
        :type v: int, float

        """
        self._set_spectrometer_parameter("SetYSymmetry", v)

    @verbose_skip
    @command_register
    def set_zsymmetry(self, v):
        """
        Set ZSymmetry to v

        :param v: zsymmetry value
        :type v: int, float
        """
        self._set_spectrometer_parameter("SetZSymmetry", v)

    @verbose_skip
    @command_register
    def set_zfocus(self, v):
        """
        Set ZFocus to v

        :param v: zfocus value
        :type v: int, float
        """
        self._set_spectrometer_parameter("SetZFocus", v)

    @verbose_skip
    @command_register
    def set_extraction_focus(self, v):
        """
        Set ExtractionFocus to v

        :param v: extractionfocus value
        :type v: int, float
        """
        self._set_spectrometer_parameter("SetExtractionFocus", v)

    @verbose_skip
    @command_register
    def set_extraction_symmetry(self, v):
        """
        Set Extraction Symmetry to v

        :param v: extraction symmetry value
        :type v: int, float
        """
        self._set_spectrometer_parameter("SetExtractionSymmetry", v)

    @verbose_skip
    @command_register
    def set_extraction_lens(self, v):
        """
        Set Extraction Lens to v

        :param v: extraction lens value
        :type v: int, float
        """
        self._set_spectrometer_parameter("SetExtractionLens", v)

    @verbose_skip
    @command_register
    def set_cdd_operating_voltage(self, v=""):
        """
        if v is '' (default) use value from file

        :param v: cdd operating voltage
        :type v: '', int, float
        """
        if v == "":
            config = self._get_config()
            v = config.getfloat("CDDParameters", "OperatingVoltage")

        self._set_spectrometer_parameter("SetIonCounterVoltage", v)

    @verbose_skip
    @command_register
    def set_source_optics(self, **kw):
        """
        example ::

            # set all source parameters to values stored in config.cfg
            set_source_optics()

            # set ysymmetry to 10.
            # set all other values using config.cfg
            set_source_optics(YSymmetry=10.0)

        """
        self._set_from_file("SourceOptics", **kw)

    @verbose_skip
    @command_register
    def set_source_parameters(self, **kw):
        self._set_from_file("SourceParameters", **kw)

    @verbose_skip
    @command_register
    def set_accelerating_voltage(self, v=""):
        self._set_spectrometer_parameter("SetHV", v)


class NGXMeasurementPyScript(MeasurementPyScript):
    pass


# ============= EOF =============================================
