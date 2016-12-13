# ===============================================================================
# Copyright 2016 ross
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
# ============= local library imports  ==========================
sensor_map = {'62': 'off',
              '95': 'thermocouple',
              '104': 'volts dc',
              '112': 'milliamps',
              '113': 'rtd 100 ohm',
              '114': 'rtd 1000 ohm',
              '155': 'potentiometer',
              '229': 'thermistor'}

isensor_map = {'off': 62,
               'thermocouple': 95,
               'volts dc': 104,
               'milliamps': 112,
               'rtd 100 ohm': 113,
               'rtd 1000 ohm': 114,
               'potentiometer': 155,
               'thermistor': 229}

itc_map = {'B': 11, 'K': 48,
           'C': 15, 'N': 58,
           'D': 23, 'R': 80,
           'E': 26, 'S': 84,
           'F': 30, 'T': 93,
           'J': 46, }

tc_map = {'11': 'B', '48': 'K',
          '15': 'C', '58': 'N',
          '23': 'D', '80': 'R',
          '26': 'E', '84': 'S',
          '30': 'F', '93': 'T',
          '46': 'J'}
autotune_aggressive_map = {'under': 99,
                           'critical': 21,
                           'over': 69}

yesno_map = {'59': 'NO', '106': 'YES'}
truefalse_map = {'59': False, '106': True}
heat_algorithm_map = {'62': 'off', '71': 'PID', '64': 'on-off'}
baudmap = {'9600': 188, '19200': 189, '38400': 190}
ibaudmap = {'188': '9600', '189': '19200', '190': '38400'}

# ============= EOF =============================================
