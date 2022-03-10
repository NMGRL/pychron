# ===============================================================================
# Copyright 2011 Jake Ross
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
from pychron.hardware.core.abstract_device import AbstractDevice
from pychron.hardware.polyinomial_mapper import PolynomialMapperMixin
from pychron.hardware.gauges.base_controller import BaseGaugeController


class ADCGaugeController(AbstractDevice, BaseGaugeController):
    def load_additional_args(self, config):
        self._load_gauges(config)

        tag = "Conversions"
        if config.has_section("Conversions"):
            for opt in config.options(tag):
                g = self.get_gauge(opt)
                if g:
                    g.map_function = config.get(tag, opt)
                else:
                    self.warning('Invalid gauge name {}. not adding map_function'.format(opt))
                    self.debug('available gauges {}'.format(','.join([g.name for g in self.gauges])))

        adc = "ADC"
        if config.has_section(adc):
            klass = self.config_get(config, adc, "klass")
            name = self.config_get(config, adc, "name", default=klass)

            pkgs = (
                "pychron.hardware.adc.analog_digital_converter",
                "pychron.hardware.agilent.agilent_multiplexer",
                "pychron.hardware.remote.agilent_multiplexer",
                "pychron.hardware.ncd.adc",
            )

            for pi in pkgs:
                factory = self.get_factory(pi, klass)
                if factory:
                    break

            self._cdevice = factory(
                name=name, configuration_dir_name=self.configuration_dir_name
            )
            return True

    def _read_pressure(self, gauge, *args, **kw):
        return gauge.voltage_to_pressure(self._cdevice.read_channel(gauge.channel))

# ============= EOF =====================================
