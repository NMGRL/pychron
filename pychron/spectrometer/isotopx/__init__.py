# ===============================================================================
# Copyright 2017 ross
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
SOURCE_CONTROL_PARAMETERS = {'IonEnergy': 'IE',
                             'YFocus': 'YF',
                             'YBias': 'YB',
                             'ZFocus': 'ZF',
                             'ZBias': 'ZB',
                             'ElectronEnergy': 'EE',
                             'IonRepeller': 'IR',
                             'TrapVoltage': 'TV',
                             'FilamentCurrent': 'FC',
                             'FilamentVoltage': 'FV',
                             'TrapCurrent': 'TC',
                             'EmissionCurrent': 'EC',
                             'ConfinementVoltage': 'CV',
                             'ESA+Plate': 'ESA+',
                             'ESA-Plate': 'ESA-'
                             }

ERRORS = {'E00': 'ERR_SUCCESS',
          'E01': 'ERR_INVALID_COMMAND',
          'E02': 'ERR_INVALID_PARAM',
          'E03': 'ERR_OUT_OF_RANGE',
          'E04': 'ERR_INVALID_MNEMONIC',
          'E05': 'ERR_MISSING_PARAMS',

          'E20': 'ERR_ABORTEDBY_SYSTEM',
          'E21': 'ERR_ABORTEDBY_USER',

          'E30': 'ERR_HARDWARE_MISSING',
          'E31': 'ERR_HARDWARE_FAULT',
          'E32': 'ERR_TIMEOUT',

          'E40': 'ERR_AVAILABLE',
          'E41': 'ERR_BUSY',
          'E42': 'ERR_ACCESS_DENIED',
          'E43': 'ERR_NOT_AVAILABLE',
          'E44': 'ERR_NO_RESULTS_AVAILABLE',
          'E45': 'ERR_UNIT_NOT_IN_TRIP_STATE',

          'E99': 'ERR_UNKNOWN'}


class IsotopxMixin(object):
    def handle_response(self, cmd, resp, *args, **kw):
        if resp in ERRORS:
            if hasattr(self, 'warning'):
                self.warning('Command {}==>{},{}'.format(cmd, resp, ERRORS[resp]))
            resp = None
        return resp

# ============= EOF =============================================
