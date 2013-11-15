#===============================================================================
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
#===============================================================================



#============= enthought library imports =======================

#============= standard library imports ========================
import os

#============= local library imports  ==========================
from pychron.data_processing.power_mapping.power_map_viewer import PowerMapViewer
from pychron.paths import paths

if __name__ == '__main__':
    p = PowerMapViewer()

    root = os.path.join(paths.data_dir, 'powermap')
    p.set_data_files(root)
    p.configure_traits()
#============= EOF ====================================
