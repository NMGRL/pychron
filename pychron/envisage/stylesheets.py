# ===============================================================================
# Copyright 2016 Jake Ross
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
import os

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.paths import paths

DEFAULT_STYLESHEETS = {'experiment_factory': '''QLineEdit {font-size: 14px}
QGroupBox {background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #E0E0E0, stop: 1 #FFFFFF);
           border: 2px solid gray;
           border-radius: 5px;
           margin-top: 1ex; /* leave space at the top for the title */
           font-size: 14px;
           font-weight: bold;}
QGroupBox::title {subcontrol-origin: margin;
                  subcontrol-position: top left; /* position at the top center */
                  padding: 2 3px;}
QComboBox {font-size: 14px}
QLabel {font-size: 14px}
QToolBox::tab {font-size: 15px}
QToolTip {font-size: 14px}'''}


def load_stylesheet(name):
    path = os.path.join(paths.hidden_dir, '{}.css'.format(name))
    if os.path.isfile(path):
        with open(path, 'r') as rfile:
            ss = rfile.readall()
    else:
        ss = DEFAULT_STYLESHEETS.get(name, '')

    return ss

# ============= EOF =============================================
