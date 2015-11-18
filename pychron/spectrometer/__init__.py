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
import os

from pychron.core.helpers.filetools import add_extension
from pychron.paths import paths


def set_spectrometer_config_name(name):
    ppath = os.path.join(paths.hidden_dir, 'spectrometer_config_name')
    name = add_extension(name, '.cfg')
    with open(ppath, 'w') as wfile:
        wfile.write(name)

def get_spectrometer_config_name():
    with open(os.path.join(paths.hidden_dir, 'spectrometer_config_name')) as rfile:
        return rfile.readall().strip()


def get_spectrometer_config_path(name=None):
    if name is None:
        name = get_spectrometer_config_name()

    return os.path.join(paths.spectrometer_config_dir, name)