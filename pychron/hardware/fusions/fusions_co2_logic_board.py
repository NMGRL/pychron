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


# =============enthought library imports=======================
import cPickle as pickle
import os

from traits.api import Float, Property, TraitError

from fusions_logic_board import FusionsLogicBoard
from pychron.hardware.meter_calibration import MeterCalibration
from pychron.paths import paths


class FusionsCO2LogicBoard(FusionsLogicBoard):
    """
    """
    request_power = Property(Float(enter_set=True, auto_set=False),
                             depends_on='_request_power')
    _request_power = Float
    request_powermin = Float(0)
    request_powermax = Float(100)

    power_meter_calibration = None

    def load_additional_args(self, config):
        """
        """
        self.set_attribute(config, 'request_powermin', 'General',
                           'power min', cast='float')
        self.set_attribute(config, 'request_powermax', 'General',
                           'power max', cast='float')

        # read in the coefficients from file
        coeffs = self.config_get(config, 'PowerMeter', 'coefficients')
        if coeffs is not None:
            self.power_meter_calibration = MeterCalibration(coeffs)

        coeffs = self.config_get(config, 'PowerOutput', 'coefficients')
        if coeffs is not None:

            p = os.path.join(paths.hidden_dir, '{}_power_calibration'.format(self.name.split('.')[0]))

            obj = MeterCalibration(coeffs)
            # dump to the hidden dir
            # the manager will use it directly
            try:
                self.info('loading power calibration from config file')
                with open(p, 'wb') as f:
                    pickle.dump(obj, f)
            except (OSError, pickle.PickleError):
                self.warning('failed loading power output calibration')

        return super(FusionsCO2LogicBoard, self).load_additional_args(config)

    def read_power_meter(self, verbose=False, **kw):
        """
        """
        cmd = self._build_command('ADC1')
        r = self._parse_response(self.ask(cmd, verbose=verbose))
        if r is not None:
            try:
                r = float(r)
                # convert to watts
                # no calibration of logic board currently available
                # will have to simple normalize to 100

                if self.power_meter_calibration is not None:
                    r = self.power_meter_calibration.get_input(r)
                else:
                    r = r / 255. * 100

            except ValueError:
                self.warning('*Bad response from ADC ==> {} (len={})'.format(r, len(r)))
                r = None

        if self.simulation:
            r = self.get_random_value()

        try:
            self.internal_meter_response = r
        except TraitError:
            return

        return r

    def get_output(self):
        pass

    def get_response(self, **kw):
        return self.internal_meter_response

    def get_setpoint(self):
        return self._request_power

    def _disable_laser(self):
        """
        """
        #        cmd = self._build_command('PDC', '0.00')
        cmd = ('PDC', '0.00')
        self._request_power = 0.0

        #        callback = lambda :self._parse_response(self.ask(cmd))
        resp = self.repeat_command(cmd, check_val='OK')
        if resp is not None:
            return super(FusionsCO2LogicBoard, self)._disable_laser()
        else:
            msg = 'failed to disable co2 laser'
            self.warning(msg)
            return msg

    def _enable_laser(self, **kw):
        """
        """
        cmd = self._build_command('PWE', '1')

        #        callback = lambda :self._parse_response(self.ask(cmd))
        resp = self.repeat_command(cmd, check_val='OK')
        if resp is not None:
            return super(FusionsCO2LogicBoard, self)._enable_laser()

        else:
            msg = 'failed to enable co2 laser'
            self.warning(msg)
            return msg

    def set_laser_power(self, request_pwr, verbose=True):
        """

            see Photon Machines Logic Board Command Set Reference
            version 0.96

            this version uses PDC instead of PWW and PWE (pwm mode) to set the laser power

            request power valid range 0 100 with 0.02 resolution

            PDC sets the laser Duty Cycle
        """
        self._request_power = request_pwr

        cmd = self._build_command('PDC', '{:0.2f}'.format(request_pwr))

        self.ask(cmd, verbose=verbose)

    def _get_request_power(self):
        """
        """
        return self._request_power

    def _set_request_power(self, v):
        """
        """
        self.set_laser_power(v)

# ====================== EOF ===========================================
